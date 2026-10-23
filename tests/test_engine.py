import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from raroc_lab import LoanRequest, PricingAssumptions, decide, evaluate_loan, solve_rate
from raroc_lab.engine import economic_capital_rate, monthly_payment


def assumptions() -> PricingAssumptions:
    raw = json.loads((ROOT / "configs" / "base_case.json").read_text())
    return PricingAssumptions(
        **{key: raw[key] for key in PricingAssumptions.__dataclass_fields__}
    )


def request(**overrides) -> LoanRequest:
    values = {
        "application_id": "TEST-001",
        "principal_vnd": 100_000_000,
        "term_months": 36,
        "annual_pd": 0.04,
        "lgd": 0.70,
        "quoted_apr": 0.18,
        "upfront_fee_rate": 0.01,
        "monthly_income_vnd": 30_000_000,
        "existing_monthly_debt_vnd": 3_000_000,
        "data_quality_flag": False,
    }
    values.update(overrides)
    return LoanRequest(**values)


class EngineTests(unittest.TestCase):
    def test_zero_rate_payment(self):
        self.assertAlmostEqual(monthly_payment(120_000_000, 0, 12), 10_000_000)

    def test_payment_amortises_principal(self):
        payment = monthly_payment(100_000_000, 0.18, 36)
        self.assertGreater(payment, 100_000_000 / 36)

    def test_higher_pd_increases_expected_loss_and_price_floor(self):
        base = assumptions()
        low = request(annual_pd=0.02)
        high = request(annual_pd=0.10)
        self.assertGreater(
            evaluate_loan(high, base).expected_loss_vnd,
            evaluate_loan(low, base).expected_loss_vnd,
        )
        self.assertGreater(solve_rate(high, base), solve_rate(low, base))

    def test_higher_funding_cost_increases_price_floor(self):
        base = assumptions()
        expensive = PricingAssumptions(**{**base.__dict__, "funding_rate": 0.07})
        self.assertGreater(solve_rate(request(), expensive), solve_rate(request(), base))

    def test_solver_meets_hurdle(self):
        base = assumptions()
        floor = solve_rate(request(), base)
        self.assertIsNotNone(floor)
        result = evaluate_loan(request(), base, floor)
        self.assertGreaterEqual(result.annualised_raroc, base.raroc_hurdle - 0.0001)

    def test_economic_capital_is_positive_for_risky_loan(self):
        self.assertGreater(economic_capital_rate(0.05, 0.70, 0.04, 0.999), 0)

    def test_declines_unaffordable_application(self):
        decision = decide(
            request(monthly_income_vnd=8_000_000, existing_monthly_debt_vnd=4_000_000),
            assumptions(),
        )
        self.assertEqual(decision.action, "decline")

    def test_data_quality_routes_to_review(self):
        decision = decide(request(data_quality_flag=True), assumptions())
        self.assertEqual(decision.action, "manual_review")


if __name__ == "__main__":
    unittest.main()

