"""Build scenario, attribution, segment, monitoring and reconciliation outputs."""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from raroc_lab import LoanRequest, PricingAssumptions, decide, evaluate_loan, solve_rate  # noqa: E402
from raroc_lab.policy import risk_tier  # noqa: E402
from scripts.run_portfolio import generated_applications, percentile  # noqa: E402


def load() -> tuple[dict, PricingAssumptions, dict]:
    raw = json.loads((ROOT / "configs" / "base_case.json").read_text())
    scenarios = json.loads((ROOT / "configs" / "scenarios.json").read_text())
    base = PricingAssumptions(
        **{key: raw[key] for key in PricingAssumptions.__dataclass_fields__}
    )
    return raw, base, scenarios


def adjusted_assumptions(base: PricingAssumptions, scenario: dict) -> PricingAssumptions:
    values = asdict(base)
    for key in (
        "funding_rate",
        "liquidity_premium",
        "servicing_cost_rate",
        "management_capital_buffer",
        "raroc_hurdle",
    ):
        values[key] = scenario[key]
    return PricingAssumptions(**values)


def adjusted_request(request: LoanRequest, scenario: dict) -> LoanRequest:
    values = request.__dict__.copy()
    values["annual_pd"] = min(request.annual_pd * scenario["pd_multiplier"], 0.99)
    values["lgd"] = min(request.lgd + scenario["lgd_addon"], 0.99)
    return LoanRequest(**values)


def build_scenarios(
    applications: list[LoanRequest], base: PricingAssumptions, scenarios: dict
) -> dict:
    result = {}
    for name, scenario in scenarios.items():
        assumptions = adjusted_assumptions(base, scenario)
        counts: Counter[str] = Counter()
        exposure: defaultdict[str, float] = defaultdict(float)
        floors: list[float] = []
        rarocs: list[float] = []
        expected_loss = 0.0
        capital = 0.0
        total_exposure = 0.0
        for original in applications:
            request = adjusted_request(original, scenario)
            outcome = decide(request, assumptions)
            counts[outcome.action] += 1
            exposure[outcome.action] += request.principal_vnd
            total_exposure += request.principal_vnd
            expected_loss += outcome.quoted_economics.expected_loss_vnd
            capital += outcome.quoted_economics.allocated_capital_vnd
            rarocs.append(outcome.quoted_economics.annualised_raroc)
            if outcome.price_floor_apr is not None:
                floors.append(outcome.price_floor_apr)
        result[name] = {
            "inputs": scenario,
            "application_count": len(applications),
            "action_count": dict(sorted(counts.items())),
            "action_share": {key: value / len(applications) for key, value in sorted(counts.items())},
            "exposure_by_action_vnd": dict(sorted(exposure.items())),
            "approved_exposure_share": exposure.get("approve", 0.0) / total_exposure,
            "median_price_floor_apr": percentile(floors, 0.50),
            "p75_price_floor_apr": percentile(floors, 0.75),
            "median_quoted_raroc": percentile(rarocs, 0.50),
            "total_expected_loss_vnd": expected_loss,
            "total_allocated_capital_vnd": capital,
        }
    return result


def build_pricing_bridge(base: PricingAssumptions) -> dict:
    reference = LoanRequest(
        application_id="REFERENCE",
        principal_vnd=100_000_000,
        term_months=36,
        annual_pd=0.04,
        lgd=0.70,
        quoted_apr=0.18,
        upfront_fee_rate=0.01,
        monthly_income_vnd=30_000_000,
        existing_monthly_debt_vnd=3_000_000,
    )
    floor_template = {
        **asdict(base),
        "minimum_apr": 0.0,
        "maximum_management_apr": 0.50,
        "funding_rate": 0.0,
        "liquidity_premium": 0.0,
        "servicing_cost_rate": 0.0,
        "origination_cost_vnd": 0.0,
        "tax_rate": 0.0,
        "raroc_hurdle": 0.0,
    }
    zero_risk = LoanRequest(**{**reference.__dict__, "annual_pd": 0.0, "lgd": 0.0, "upfront_fee_rate": 0.0})
    steps = []

    def append_step(label: str, loan: LoanRequest, values: dict) -> float:
        floor = solve_rate(loan, PricingAssumptions(**values))
        if floor is None:
            raise RuntimeError(f"No price floor found for bridge step {label}")
        prior = steps[-1]["cumulative_apr"] if steps else 0.0
        steps.append({"component": label, "incremental_apr": floor - prior, "cumulative_apr": floor})
        return floor

    values = floor_template.copy()
    append_step("Starting rate", zero_risk, values)
    values["funding_rate"] = base.funding_rate
    append_step("Funding cost", zero_risk, values)
    values["liquidity_premium"] = base.liquidity_premium
    append_step("Liquidity premium", zero_risk, values)
    values["servicing_cost_rate"] = base.servicing_cost_rate
    values["origination_cost_vnd"] = base.origination_cost_vnd
    append_step("Operating cost", zero_risk, values)
    risk_no_fee = LoanRequest(**{**reference.__dict__, "upfront_fee_rate": 0.0})
    append_step("Expected loss", risk_no_fee, values)
    values["raroc_hurdle"] = base.raroc_hurdle
    append_step("Capital return", risk_no_fee, values)
    values["tax_rate"] = base.tax_rate
    append_step("Tax gross-up", risk_no_fee, values)
    append_step("Upfront fee offset", reference, values)
    return {"reference_application": reference.__dict__, "steps": steps}


def principal_band(principal: float) -> str:
    if principal < 75_000_000:
        return "Below 75m"
    if principal < 150_000_000:
        return "75m to 150m"
    return "150m and above"


def build_segments(applications: list[LoanRequest], base: PricingAssumptions) -> list[dict]:
    groups: dict[tuple[str, str], list[tuple[LoanRequest, object]]] = defaultdict(list)
    for request in applications:
        outcome = decide(request, base)
        groups[("Risk tier", risk_tier(request.annual_pd))].append((request, outcome))
        groups[("Term", f"{request.term_months} months")].append((request, outcome))
        groups[("Principal", principal_band(request.principal_vnd))].append((request, outcome))

    rows = []
    for (dimension, segment), items in sorted(groups.items()):
        floors = [item[1].price_floor_apr for item in items if item[1].price_floor_apr is not None]
        counts = Counter(item[1].action for item in items)
        exposure = sum(item[0].principal_vnd for item in items)
        rows.append(
            {
                "dimension": dimension,
                "segment": segment,
                "applications": len(items),
                "requested_exposure_vnd": exposure,
                "average_pd": sum(item[0].annual_pd for item in items) / len(items),
                "average_quoted_apr": sum(item[0].quoted_apr for item in items) / len(items),
                "median_price_floor_apr": percentile(floors, 0.50),
                "median_quoted_raroc": percentile(
                    [item[1].quoted_economics.annualised_raroc for item in items], 0.50
                ),
                "approve_share": counts["approve"] / len(items),
                "reprice_share": counts["reprice"] / len(items),
                "review_share": counts["manual_review"] / len(items),
                "decline_share": counts["decline"] / len(items),
            }
        )
    return rows


def build_monitoring(seed: int) -> list[dict]:
    rng = random.Random(seed + 77)
    months = [date(2025 + (10 + i) // 12, (10 + i) % 12 + 1, 1) for i in range(12)]
    rows = []
    for index, month in enumerate(months):
        applications = int(310 + index * 5 + rng.gauss(0, 18))
        approval = min(max(0.70 - index * 0.004 + rng.gauss(0, 0.012), 0.60), 0.75)
        booked_apr = 0.155 + index * 0.0015 + rng.gauss(0, 0.003)
        avg_pd = 0.073 + index * 0.001 + rng.gauss(0, 0.002)
        calibration = 1.02 + rng.gauss(0, 0.05)
        funding = 0.042 + index * 0.0004 + rng.gauss(0, 0.001)
        raroc = 0.24 - index * 0.003 + rng.gauss(0, 0.008)
        override = 0.025 + rng.gauss(0, 0.004)
        if index == 8:
            calibration = 1.24
        if index == 9:
            funding = 0.061
            raroc = 0.145
        if index == 10:
            override = 0.061
        triggers = []
        if calibration > 1.15 or calibration < 0.85:
            triggers.append("PD calibration")
        if funding > 0.060:
            triggers.append("Funding cost")
        if raroc < 0.16:
            triggers.append("RAROC hurdle")
        if override > 0.05:
            triggers.append("Price overrides")
        rows.append(
            {
                "month": month.isoformat(),
                "applications": applications,
                "approval_rate": approval,
                "average_booked_apr": booked_apr,
                "average_origination_pd": avg_pd,
                "observed_to_expected_default_ratio": calibration,
                "funding_rate": funding,
                "portfolio_raroc": raroc,
                "price_override_rate": override,
                "trigger": ", ".join(triggers) if triggers else "None",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    raw, base, scenarios = load()
    applications = generated_applications(raw["portfolio_size"], raw["portfolio_seed"])
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)

    scenario_summary = build_scenarios(applications, base, scenarios)
    (reports / "scenario_summary.json").write_text(json.dumps(scenario_summary, indent=2))

    bridge = build_pricing_bridge(base)
    (reports / "pricing_bridge.json").write_text(json.dumps(bridge, indent=2))

    segment_rows = build_segments(applications, base)
    write_csv(reports / "segment_summary.csv", segment_rows)

    monitoring_rows = build_monitoring(raw["portfolio_seed"])
    write_csv(reports / "monitoring_sample.csv", monitoring_rows)

    reference = LoanRequest(**bridge["reference_application"])
    reconciliation = {
        "engine": asdict(evaluate_loan(reference, base)),
        "exact_price_floor_apr": solve_rate(reference, base),
        "source": "Python engine",
    }
    (reports / "reference_reconciliation.json").write_text(json.dumps(reconciliation, indent=2))
    print(json.dumps({"scenarios": scenario_summary, "bridge": bridge}, indent=2))


if __name__ == "__main__":
    main()
