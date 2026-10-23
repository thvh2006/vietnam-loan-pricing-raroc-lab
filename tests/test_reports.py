import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


class ReportIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenarios = json.loads((REPORTS / "scenario_summary.json").read_text())
        cls.bridge = json.loads((REPORTS / "pricing_bridge.json").read_text())
        cls.reconciliation = json.loads(
            (REPORTS / "reference_reconciliation.json").read_text()
        )

    def test_scenario_price_floors_are_monotonic(self):
        floors = [
            self.scenarios[name]["median_price_floor_apr"]
            for name in ("Base", "Downside", "Severe")
        ]
        self.assertLess(floors[0], floors[1])
        self.assertLess(floors[1], floors[2])

    def test_each_scenario_reconciles_to_4000_applications(self):
        for scenario in self.scenarios.values():
            self.assertEqual(sum(scenario["action_count"].values()), 4000)

    def test_price_bridge_reconciles_to_exact_floor(self):
        bridge_floor = self.bridge["steps"][-1]["cumulative_apr"]
        exact_floor = self.reconciliation["exact_price_floor_apr"]
        self.assertAlmostEqual(bridge_floor, exact_floor, places=6)


if __name__ == "__main__":
    unittest.main()
