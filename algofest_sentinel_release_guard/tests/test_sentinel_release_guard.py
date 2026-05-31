import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import sentinel_release_guard as guard


class SentinelReleaseGuardTests(unittest.TestCase):
    def test_sample_change_blocks_release(self):
        change = guard.read_change(ROOT / "demo_input" / "sample_change.json")
        plan = guard.build_plan(change)
        self.assertGreaterEqual(plan.release_risk_score, 80)
        self.assertEqual(plan.release_decision, "BLOCK_RELEASE_PENDING_HUMAN_REVIEW")
        self.assertTrue(plan.human_approval_required)
        self.assertTrue(any(result.status == "failed" for result in plan.simulated_results))

    def test_generates_platform_neutral_release_gate_cases(self):
        change = guard.read_change(ROOT / "demo_input" / "sample_change.json")
        plan = guard.build_plan(change)
        self.assertGreaterEqual(len(plan.test_cases), 4)
        self.assertTrue(all(test.automation_target == "Sentinel CI release gate" for test in plan.test_cases))
        self.assertTrue(all(test.control_asset.startswith("ReleaseGate::") for test in plan.test_cases))

    def test_demo_writes_benchmark_outputs(self):
        output_dir = ROOT / "demo_output"
        plan = guard.run_demo(ROOT / "demo_input" / "sample_change.json", output_dir)
        self.assertEqual(plan.release_decision, "BLOCK_RELEASE_PENDING_HUMAN_REVIEW")
        self.assertTrue((output_dir / "benchmark_results.json").exists())
        self.assertTrue((output_dir / "ci_release_gate.json").exists())
        dashboard = (output_dir / "dashboard.html").read_text(encoding="utf-8")
        self.assertIn("AlgoFest 2026", dashboard)
        self.assertNotIn("UiPath", dashboard)


if __name__ == "__main__":
    unittest.main()
