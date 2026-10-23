"""Build deterministic application-level and portfolio-level decision reports."""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from raroc_lab import LoanRequest, PricingAssumptions, decide  # noqa: E402


def load_assumptions() -> tuple[dict, PricingAssumptions]:
    raw = json.loads((ROOT / "configs" / "base_case.json").read_text())
    fields = PricingAssumptions.__dataclass_fields__
    model = PricingAssumptions(**{key: raw[key] for key in fields})
    return raw, model


def generated_applications(size: int, seed: int) -> list[LoanRequest]:
    rng = random.Random(seed)
    terms = [12, 18, 24, 36, 48]
    requests: list[LoanRequest] = []
    for index in range(1, size + 1):
        principal = round(rng.uniform(30_000_000, 250_000_000) / 1_000_000) * 1_000_000
        pd = min(max(rng.betavariate(1.8, 18.0), 0.003), 0.35)
        lgd = min(max(rng.gauss(0.72, 0.08), 0.45), 0.90)
        quoted = min(max(0.105 + pd * 0.85 + rng.gauss(0, 0.012), 0.08), 0.30)
        income = round(rng.uniform(14_000_000, 65_000_000) / 500_000) * 500_000
        existing_debt = max(round(rng.uniform(0, income * 0.28) / 100_000) * 100_000, 0)
        requests.append(
            LoanRequest(
                application_id=f"SYN-{index:05d}",
                principal_vnd=principal,
                term_months=rng.choice(terms),
                annual_pd=pd,
                lgd=lgd,
                quoted_apr=quoted,
                upfront_fee_rate=rng.choice([0.005, 0.01, 0.015]),
                monthly_income_vnd=income,
                existing_monthly_debt_vnd=existing_debt,
                data_quality_flag=rng.random() < 0.015,
            )
        )
    return requests


def percentile(values: list[float], proportion: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    index = round((len(ordered) - 1) * proportion)
    return ordered[index]


def main() -> None:
    raw, assumptions = load_assumptions()
    applications = generated_applications(raw["portfolio_size"], raw["portfolio_seed"])
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)

    rows = []
    action_counts: Counter[str] = Counter()
    tier_counts: Counter[str] = Counter()
    exposure_by_action: defaultdict[str, float] = defaultdict(float)
    floor_rates = []
    quoted_rarocs = []

    for request in applications:
        decision = decide(request, assumptions)
        economics = decision.quoted_economics
        action_counts[decision.action] += 1
        tier_counts[decision.risk_tier] += 1
        exposure_by_action[decision.action] += request.principal_vnd
        quoted_rarocs.append(economics.annualised_raroc)
        if decision.price_floor_apr is not None:
            floor_rates.append(decision.price_floor_apr)
        rows.append(
            {
                "application_id": request.application_id,
                "principal_vnd": request.principal_vnd,
                "term_months": request.term_months,
                "annual_pd": request.annual_pd,
                "lgd": request.lgd,
                "quoted_apr": request.quoted_apr,
                "monthly_payment_vnd": economics.monthly_payment_vnd,
                "debt_service_to_income": economics.debt_service_to_income,
                "risk_tier": decision.risk_tier,
                "price_floor_apr": decision.price_floor_apr,
                "annualised_raroc": economics.annualised_raroc,
                "expected_loss_vnd": economics.expected_loss_vnd,
                "allocated_capital_vnd": economics.allocated_capital_vnd,
                "action": decision.action,
                "reason": decision.reason,
            }
        )

    output_csv = reports / "application_decisions.csv"
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    total_exposure = sum(exposure_by_action.values())
    summary = {
        "as_of_date": raw["as_of_date"],
        "portfolio_is_synthetic": True,
        "application_count": len(applications),
        "total_requested_exposure_vnd": total_exposure,
        "actions": dict(sorted(action_counts.items())),
        "action_share": {
            key: value / len(applications) for key, value in sorted(action_counts.items())
        },
        "exposure_by_action_vnd": dict(sorted(exposure_by_action.items())),
        "risk_tiers": dict(sorted(tier_counts.items())),
        "price_floor_apr_p25": percentile(floor_rates, 0.25),
        "price_floor_apr_median": percentile(floor_rates, 0.50),
        "price_floor_apr_p75": percentile(floor_rates, 0.75),
        "quoted_raroc_median": percentile(quoted_rarocs, 0.50),
        "assumptions": asdict(assumptions),
    }
    (reports / "portfolio_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

