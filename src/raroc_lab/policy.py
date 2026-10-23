"""Decision rules kept separate from financial calculations."""

from __future__ import annotations

from dataclasses import dataclass

from .engine import LoanEconomics, LoanRequest, PricingAssumptions, evaluate_loan, solve_rate


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    risk_tier: str
    price_floor_apr: float | None
    quoted_economics: LoanEconomics


def risk_tier(pd: float) -> str:
    if pd <= 0.02:
        return "A"
    if pd <= 0.05:
        return "B"
    if pd <= 0.10:
        return "C"
    if pd <= 0.15:
        return "D"
    return "E"


def decide(request: LoanRequest, assumptions: PricingAssumptions) -> Decision:
    economics = evaluate_loan(request, assumptions)
    tier = risk_tier(request.annual_pd)

    if request.data_quality_flag:
        return Decision("manual_review", "data quality flag", tier, None, economics)
    if request.annual_pd > assumptions.maximum_pd:
        return Decision("decline", "PD exceeds policy maximum", tier, None, economics)
    if economics.debt_service_to_income > assumptions.maximum_debt_service_to_income:
        return Decision("decline", "debt service to income exceeds policy maximum", tier, None, economics)

    floor = solve_rate(request, assumptions)
    if floor is None:
        return Decision(
            "manual_review",
            "RAROC hurdle cannot be met within management APR cap",
            tier,
            None,
            economics,
        )
    if request.quoted_apr + assumptions.rate_solver_tolerance < floor:
        return Decision("reprice", "quoted APR is below the RAROC price floor", tier, floor, economics)
    return Decision("approve", "eligibility and RAROC conditions are met", tier, floor, economics)

