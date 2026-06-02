import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hidden_reviews_agent import (  # noqa: E402
    analyze_feedback_bundle,
    export_demo_artifacts,
    load_feedback_bundle,
    recommend_subscription_tier,
)


class HiddenReviewsAgentTests(unittest.TestCase):
    def test_mixed_feedback_exposes_hidden_revenue_and_churn_risk(self):
        bundle = load_feedback_bundle(ROOT / "demo_input" / "sample_feedback.json")
        result = analyze_feedback_bundle(bundle, customer_count=1800)

        self.assertEqual(result.domain, "hidden.reviews")
        self.assertGreaterEqual(result.hidden_signal_score, 90)
        self.assertGreaterEqual(result.domain_fit_score, 95)
        self.assertEqual(result.top_cluster.category, "pricing_trust")
        self.assertIn("pricing_trust", {cluster.category for cluster in result.clusters})
        self.assertIn("integration_reliability", {cluster.category for cluster in result.clusters})
        self.assertIn("onboarding_confusion", {cluster.category for cluster in result.clusters})
        self.assertGreaterEqual(len(result.action_plan), 6)
        self.assertTrue(any("pricing" in action.title.lower() for action in result.action_plan))
        self.assertTrue(any(event.source_type == "public_shadow_channel" for event in result.evidence_events))

    def test_clear_positive_feedback_stays_low_urgency(self):
        result = analyze_feedback_bundle(
            {
                "product": "TinyDocs",
                "domain": "hidden.reviews",
                "sources": [
                    {
                        "source": "App Store",
                        "source_type": "public_review",
                        "author": "happy_user",
                        "text": "Love the export flow. The pricing is clear and onboarding was easy.",
                    },
                    {
                        "source": "Support email",
                        "source_type": "private_support",
                        "author": "team lead",
                        "text": "The new docs are useful. No major bugs to report.",
                    },
                ],
            },
            customer_count=80,
        )

        self.assertLess(result.hidden_signal_score, 35)
        self.assertEqual(result.top_cluster.category, "customer_love")
        self.assertEqual(result.recommended_tier["name"], "Scout")

    def test_subscription_recommendation_scales_with_customer_count(self):
        tier = recommend_subscription_tier(1800)

        self.assertEqual(tier["name"], "Growth")
        self.assertEqual(tier["monthly_price_usd"], 149)
        self.assertGreaterEqual(tier["included_feedback_items"], 5000)

    def test_demo_exports_analysis_brief_csv_and_domain_pitch(self):
        bundle = load_feedback_bundle(ROOT / "demo_input" / "sample_feedback.json")
        result = analyze_feedback_bundle(bundle, customer_count=1800)

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            paths = export_demo_artifacts(result, out_dir)

            self.assertEqual(set(paths), {"analysis", "brief", "evidence_csv", "domain_pitch", "pricing"})
            self.assertTrue((out_dir / "analysis_result.json").exists())
            self.assertTrue((out_dir / "founder_brief.md").exists())
            self.assertTrue((out_dir / "evidence_events.csv").exists())
            self.assertTrue((out_dir / "domain_pitch.md").exists())
            self.assertTrue((out_dir / "pricing_model.json").exists())

            analysis = json.loads((out_dir / "analysis_result.json").read_text(encoding="utf-8"))
            self.assertEqual(analysis["domain"], "hidden.reviews")
            self.assertEqual(analysis["top_cluster"]["category"], "pricing_trust")


if __name__ == "__main__":
    unittest.main()
