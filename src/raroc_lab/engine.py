"""Cash-flow, expected-loss, capital and price-floor calculations."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import NormalDist


@dataclass(frozen=True)
class PricingAssumptions:
    funding_rate: float
    liquidity_premium: float
    servicing_cost_rate: float
    origination_cost_vnd: float
    tax_rate: float
    retail_risk_weight: float
    regulatory_capital_ratio: float
    management_capital_buffer: float
    management_capital_floor_rate: float
    economic_capital_confidence: float
    asset_correlation: float
    raroc_hurdle: float
    minimum_apr: float
    maximum_management_apr: float
    maximum_pd: float
    maximum_debt_service_to_income: float
    ead_at_default_multiplier: float = 1.0
    rate_solver_tolerance: float = 0.000001

    @property
    def buffered_capital_ratio(self) -> float:
        return self.regulatory_capital_ratio + self.management_capital_buffer


@dataclass(frozen=True)
class LoanRequest:
    application_id: str
    principal_vnd: float
    term_months: int
    annual_pd: float
    lgd: float
    quoted_apr: float
    upfront_fee_rate: float
    monthly_income_vnd: float
    existing_monthly_debt_vnd: float
    data_quality_flag: bool = False


@dataclass(frozen=True)
class LoanEconomics:
    contractual_apr: float
    monthly_payment_vnd: float
    average_performing_ead_vnd: float
    interest_income_vnd: float
    fee_income_vnd: float
    funding_cost_vnd: float
    liquidity_cost_vnd: float
    operating_cost_vnd: float
    expected_loss_vnd: float
    pre_tax_risk_adjusted_profit_vnd: float
    after_tax_risk_adjusted_profit_vnd: float
    regulatory_capital_vnd: float
    economic_capital_vnd: float
    management_floor_capital_vnd: float
    allocated_capital_vnd: float
    annualised_raroc: float
    debt_service_to_income: float


def _validate_rate(name: str, value: float, upper: float = 1.0) -> None:
    if not 0 <= value <= upper:
        raise ValueError(f"{name} must be between 0 and {upper}")


def validate(request: LoanRequest, assumptions: PricingAssumptions) -> None:
    if request.principal_vnd <= 0:
        raise ValueError("principal_vnd must be positive")
    if request.term_months <= 0:
        raise ValueError("term_months must be positive")
    if request.monthly_income_vnd <= 0:
        raise ValueError("monthly_income_vnd must be positive")
    if request.existing_monthly_debt_vnd < 0:
        raise ValueError("existing_monthly_debt_vnd cannot be negative")
    _validate_rate("annual_pd", request.annual_pd)
    _validate_rate("lgd", request.lgd)
    _validate_rate("quoted_apr", request.quoted_apr, 5.0)
    _validate_rate("upfront_fee_rate", request.upfront_fee_rate)
    _validate_rate("tax_rate", assumptions.tax_rate)
    _validate_rate("asset_correlation", assumptions.asset_correlation, 0.99)
    _validate_rate("economic_capital_confidence", assumptions.economic_capital_confidence)


def monthly_payment(principal: float, annual_rate: float, term_months: int) -> float:
    monthly_rate = annual_rate / 12.0
    if monthly_rate == 0:
        return principal / term_months
    return principal * monthly_rate / (1.0 - (1.0 + monthly_rate) ** (-term_months))


def economic_capital_rate(pd: float, lgd: float, correlation: float, confidence: float) -> float:
    """One-factor Gaussian unexpected-loss proxy before portfolio diversification."""
    if pd <= 0 or lgd <= 0:
        return 0.0
    clipped_pd = min(max(pd, 1e-8), 1 - 1e-8)
    normal = NormalDist()
    stressed_pd = normal.cdf(
        (normal.inv_cdf(clipped_pd) + sqrt(correlation) * normal.inv_cdf(confidence))
        / sqrt(1.0 - correlation)
    )
    return max(lgd * (stressed_pd - clipped_pd), 0.0)


def evaluate_loan(
    request: LoanRequest,
    assumptions: PricingAssumptions,
    contractual_apr: float | None = None,
) -> LoanEconomics:
    validate(request, assumptions)
    apr = request.quoted_apr if contractual_apr is None else contractual_apr
    _validate_rate("contractual_apr", apr, 5.0)

    payment = monthly_payment(request.principal_vnd, apr, request.term_months)
    monthly_rate = apr / 12.0
    monthly_hazard = 1.0 - (1.0 - request.annual_pd) ** (1.0 / 12.0)
    balance = request.principal_vnd

    interest_income = 0.0
    funding_cost = 0.0
    liquidity_cost = 0.0
    recurring_operating_cost = 0.0
    expected_loss = 0.0
    performing_ead_sum = 0.0

    for month in range(1, request.term_months + 1):
        survival_start = (1.0 - monthly_hazard) ** (month - 1)
        marginal_default = survival_start * monthly_hazard
        opening_balance = balance
        contractual_interest = opening_balance * monthly_rate
        principal_payment = min(max(payment - contractual_interest, 0.0), opening_balance)
        balance = max(opening_balance - principal_payment, 0.0)

        performing_ead = opening_balance * survival_start
        performing_ead_sum += performing_ead
        interest_income += contractual_interest * survival_start
        funding_cost += performing_ead * assumptions.funding_rate / 12.0
        liquidity_cost += performing_ead * assumptions.liquidity_premium / 12.0
        recurring_operating_cost += performing_ead * assumptions.servicing_cost_rate / 12.0
        expected_loss += (
            marginal_default
            * opening_balance
            * assumptions.ead_at_default_multiplier
            * request.lgd
        )

    average_performing_ead = performing_ead_sum / request.term_months
    fee_income = request.principal_vnd * request.upfront_fee_rate
    operating_cost = assumptions.origination_cost_vnd + recurring_operating_cost
    pre_tax_profit = (
        interest_income
        + fee_income
        - funding_cost
        - liquidity_cost
        - operating_cost
        - expected_loss
    )
    tax = max(pre_tax_profit, 0.0) * assumptions.tax_rate
    after_tax_profit = pre_tax_profit - tax

    regulatory_capital = (
        average_performing_ead
        * assumptions.retail_risk_weight
        * assumptions.buffered_capital_ratio
    )
    economic_capital = average_performing_ead * economic_capital_rate(
        request.annual_pd,
        request.lgd,
        assumptions.asset_correlation,
        assumptions.economic_capital_confidence,
    )
    management_floor_capital = (
        average_performing_ead * assumptions.management_capital_floor_rate
    )
    allocated_capital = max(
        regulatory_capital,
        economic_capital,
        management_floor_capital,
    )
    term_years = request.term_months / 12.0
    annualised_profit = after_tax_profit / term_years
    raroc = annualised_profit / allocated_capital if allocated_capital > 0 else float("nan")
    debt_service_to_income = (
        payment + request.existing_monthly_debt_vnd
    ) / request.monthly_income_vnd

    return LoanEconomics(
        contractual_apr=apr,
        monthly_payment_vnd=payment,
        average_performing_ead_vnd=average_performing_ead,
        interest_income_vnd=interest_income,
        fee_income_vnd=fee_income,
        funding_cost_vnd=funding_cost,
        liquidity_cost_vnd=liquidity_cost,
        operating_cost_vnd=operating_cost,
        expected_loss_vnd=expected_loss,
        pre_tax_risk_adjusted_profit_vnd=pre_tax_profit,
        after_tax_risk_adjusted_profit_vnd=after_tax_profit,
        regulatory_capital_vnd=regulatory_capital,
        economic_capital_vnd=economic_capital,
        management_floor_capital_vnd=management_floor_capital,
        allocated_capital_vnd=allocated_capital,
        annualised_raroc=raroc,
        debt_service_to_income=debt_service_to_income,
    )


def solve_rate(request: LoanRequest, assumptions: PricingAssumptions) -> float | None:
    """Return the minimum APR meeting the RAROC hurdle, or None if the cap cannot meet it."""
    low = assumptions.minimum_apr
    high = assumptions.maximum_management_apr
    if evaluate_loan(request, assumptions, low).annualised_raroc >= assumptions.raroc_hurdle:
        return low
    if evaluate_loan(request, assumptions, high).annualised_raroc < assumptions.raroc_hurdle:
        return None

    while high - low > assumptions.rate_solver_tolerance:
        midpoint = (low + high) / 2.0
        result = evaluate_loan(request, assumptions, midpoint)
        if result.annualised_raroc >= assumptions.raroc_hurdle:
            high = midpoint
        else:
            low = midpoint
    return high

