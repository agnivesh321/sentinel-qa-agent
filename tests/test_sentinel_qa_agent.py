import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import sentinel_qa_agent as agent


class SentinelAgentTests(unittest.TestCase):
    def test_sample_change_blocks_release(self):
        change = agent.read_change(ROOT / "demo_input" / "sample_change.json")
        plan = agent.build_plan(change)
        self.assertGreaterEqual(plan.release_risk_score, 80)
        self.assertEqual(plan.release_decision, "BLOCK_RELEASE_PENDING_HUMAN_REVIEW")
        self.assertTrue(plan.human_approval_required)
        self.assertTrue(any(result.status == "failed" for result in plan.simulated_results))

    def test_generates_uipath_test_cases(self):
        change = agent.read_change(ROOT / "demo_input" / "sample_change.json")
        plan = agent.build_plan(change)
        self.assertGreaterEqual(len(plan.test_cases), 4)
        self.assertTrue(all(test.automation_target == "UiPath Test Cloud" for test in plan.test_cases))
        self.assertTrue(any(test.human_gate for test in plan.test_cases))


if __name__ == "__main__":
    unittest.main()
