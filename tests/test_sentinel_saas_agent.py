import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sentinel_saas_agent import (  # noqa: E402
    analyze_change,
    export_demo_artifacts,
    load_change,
    recommend_plan_for_usage,
)


class SentinelSaaSAgentTests(unittest.TestCase):
    def test_high_risk_ai_payment_change_blocks_release(self):
        change = load_change(ROOT / "demo_input" / "sample_pr.json")
        result = analyze_change(change, tenant="acme-finance", monthly_usage=420)

        self.assertEqual(result.release_decision, "BLOCK_RELEASE_PENDING_HUMAN_REVIEW")
        self.assertGreaterEqual(result.release_risk_score, 90)
        self.assertTrue(result.human_approval_required)
        self.assertIn("payment", {signal.category for signal in result.risk_signals})
        self.assertIn("ai_agent", {signal.category for signal in result.risk_signals})
        self.assertIn("authentication", {signal.category for signal in result.risk_signals})
        self.assertGreaterEqual(len(result.release_gates), 8)
        self.assertGreater(result.metering["api_units"], 0)

    def test_low_risk_marketing_copy_change_approves_release(self):
        result = analyze_change(
            {
                "title": "Update homepage headline copy",
                "summary": "Refresh static landing page text with no authentication, payment, or data changes.",
                "changed_files": ["web/homepage.html", "web/styles.css"],
                "diff_excerpt": "copy-only static text update",
                "business_context": "Marketing content refresh",
            },
            tenant="starter-demo",
            monthly_usage=12,
        )

        self.assertEqual(result.release_decision, "APPROVE_RELEASE")
        self.assertLess(result.release_risk_score, 35)
        self.assertFalse(result.human_approval_required)
        self.assertEqual(result.recommended_plan["name"], "Starter")

    def test_usage_recommends_growth_plan(self):
        plan = recommend_plan_for_usage(420)

        self.assertEqual(plan["name"], "Growth")
        self.assertEqual(plan["monthly_price_inr"], 4999)
        self.assertGreaterEqual(plan["included_release_scans"], 500)

    def test_demo_artifacts_export_json_markdown_and_audit_log(self):
        change = load_change(ROOT / "demo_input" / "sample_pr.json")
        result = analyze_change(change, tenant="acme-finance", monthly_usage=420)

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            paths = export_demo_artifacts(result, out_dir)

            self.assertTrue((out_dir / "analysis_result.json").exists())
            self.assertTrue((out_dir / "executive_brief.md").exists())
            self.assertTrue((out_dir / "tenant_audit_log.json").exists())
            self.assertTrue((out_dir / "pricing_model.json").exists())
            self.assertEqual(set(paths), {"analysis", "brief", "audit", "pricing"})

            analysis = json.loads((out_dir / "analysis_result.json").read_text(encoding="utf-8"))
            self.assertEqual(analysis["release_decision"], "BLOCK_RELEASE_PENDING_HUMAN_REVIEW")
            self.assertEqual(analysis["tenant"], "acme-finance")


if __name__ == "__main__":
    unittest.main()
