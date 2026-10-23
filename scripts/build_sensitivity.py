"""Build pricing sensitivities from the same engine used for policy decisions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from raroc_lab import LoanRequest, PricingAssumptions, solve_rate  # noqa: E402


def main() -> None:
    raw = json.loads((ROOT / "configs" / "base_case.json").read_text())
    base = PricingAssumptions(
        **{key: raw[key] for key in PricingAssumptions.__dataclass_fields__}
    )
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

    funding_rates = [0.035, 0.046, 0.055, 0.065, 0.075]
    pds = [0.02, 0.04, 0.06, 0.08, 0.10, 0.15]
    lgds = [0.50, 0.60, 0.70, 0.80, 0.90]
    hurdles = [0.12, 0.14, 0.16, 0.18, 0.20]
    principals = [50_000_000, 100_000_000, 150_000_000, 200_000_000]
    terms = [12, 24, 36, 48, 60]

    pd_funding = []
    for pd in pds:
        row = {"annual_pd": pd}
        loan = LoanRequest(**{**reference.__dict__, "annual_pd": pd})
        for funding in funding_rates:
            assumptions = PricingAssumptions(**{**base.__dict__, "funding_rate": funding})
            row[f"funding_{funding:.3f}"] = solve_rate(loan, assumptions)
        pd_funding.append(row)

    lgd_hurdle = []
    for lgd in lgds:
        row = {"lgd": lgd}
        loan = LoanRequest(**{**reference.__dict__, "lgd": lgd})
        for hurdle in hurdles:
            assumptions = PricingAssumptions(**{**base.__dict__, "raroc_hurdle": hurdle})
            row[f"hurdle_{hurdle:.2f}"] = solve_rate(loan, assumptions)
        lgd_hurdle.append(row)

    principal_term = []
    for principal in principals:
        row = {"principal_vnd": principal}
        for term in terms:
            loan = LoanRequest(
                **{**reference.__dict__, "principal_vnd": principal, "term_months": term}
            )
            row[f"term_{term}"] = solve_rate(loan, base)
        principal_term.append(row)

    output = {
        "reference_application": reference.__dict__,
        "funding_rates": funding_rates,
        "annual_pds": pds,
        "lgds": lgds,
        "raroc_hurdles": hurdles,
        "principals_vnd": principals,
        "terms_months": terms,
        "pd_by_funding": pd_funding,
        "lgd_by_hurdle": lgd_hurdle,
        "principal_by_term": principal_term,
    }
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "pricing_sensitivity.json").write_text(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
