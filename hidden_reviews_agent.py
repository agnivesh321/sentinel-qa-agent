#!/usr/bin/env python3
"""
Hidden Reviews AI

Domain Roulette submission core for hidden.reviews.

The agent finds buried customer pain in public shadow channels and private
notes, clusters the evidence, ranks product risk, and generates a founder-ready
action plan. It is deterministic so judges can run it without API keys.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "demo_input" / "sample_feedback.json"
DEFAULT_OUTPUT = ROOT / "demo_output"
DOMAIN = "hidden.reviews"


SUBSCRIPTION_TIERS = [
    {
        "name": "Scout",
        "monthly_price_usd": 29,
        "included_feedback_items": 250,
        "target_customer": "Solo founders and student startup teams",
        "overage_usd_per_100_items": 8,
    },
    {
        "name": "Growth",
        "monthly_price_usd": 149,
        "included_feedback_items": 7500,
        "target_customer": "SaaS teams with public communities and support queues",
        "overage_usd_per_100_items": 4,
    },
    {
        "name": "Command Center",
        "monthly_price_usd": 499,
        "included_feedback_items": 30000,
        "target_customer": "Product orgs tracking many products, markets, or regions",
        "overage_usd_per_100_items": 2,
    },
]


CLUSTER_RULES = {
    "pricing_trust": {
        "label": "Pricing trust risk",
        "weight": 34,
        "tokens": ("pricing", "price", "bill", "billing", "overage", "surprise", "churn", "trust", "spend", "guardrail"),
        "opportunity": "Publish proactive pricing guardrails and overage alerts before customers feel trapped.",
        "why_it_matters": "Pricing distrust converts quiet complaints into churn and lost sales.",
    },
    "integration_reliability": {
        "label": "Integration reliability",
        "weight": 28,
        "tokens": ("webhook", "integration", "sync", "erp", "idempotent", "timeout", "duplicate", "invoice", "month-end"),
        "opportunity": "Ship idempotency controls, replay-safe webhooks, and customer-visible sync health.",
        "why_it_matters": "Integration bugs damage operational trust at the exact moment teams depend on the product.",
    },
    "onboarding_confusion": {
        "label": "Onboarding confusion",
        "weight": 24,
        "tokens": ("onboarding", "setup", "docs", "documentation", "sandbox", "api key", "import", "wizard", "validation"),
        "opportunity": "Replace scattered setup instructions with a guided onboarding checklist and failed-import evidence.",
        "why_it_matters": "Confusing setup hides adoption friction until users abandon the product.",
    },
    "executive_visibility": {
        "label": "Executive visibility gap",
        "weight": 18,
        "tokens": ("digest", "executive", "pattern", "hidden", "leader", "weekly", "too late", "reviews"),
        "opportunity": "Create a weekly review digest that translates scattered complaints into product decisions.",
        "why_it_matters": "Teams lose the pattern when complaints are split across communities, support, and sales notes.",
    },
    "competitor_pressure": {
        "label": "Competitor pressure",
        "weight": 16,
        "tokens": ("competitor", "won", "lost", "ledgerfox", "deal", "prospect", "alternative"),
        "opportunity": "Turn competitor wins into a counter-positioning roadmap with proof-backed gaps.",
        "why_it_matters": "Competitor mentions are buying signals disguised as casual feedback.",
    },
    "customer_love": {
        "label": "Customer love",
        "weight": -12,
        "tokens": ("love", "useful", "easy", "clear", "great", "happy", "no major bugs"),
        "opportunity": "Preserve what customers already value while watching for new hidden complaints.",
        "why_it_matters": "Positive feedback is useful, but it should not bury emerging product risk.",
    },
}


RISK_CONTEXT_TOKENS = (
    "broke",
    "broken",
    "called it",
    "churn",
    "complained",
    "confusing",
    "could not",
    "duplicate",
    "duplicated",
    "edge case",
    "failed",
    "fails",
    "hidden",
    "lost",
    "missing",
    "overage",
    "problem",
    "silent",
    "surprise",
    "timeout",
    "too late",
    "trust problem",
)


SOURCE_MULTIPLIERS = {
    "public_shadow_channel": 1.35,
    "private_sales_note": 1.25,
    "private_support": 1.2,
    "public_review": 1.0,
}


@dataclass
class FeedbackSource:
    source: str
    source_type: str
    author: str
    text: str


@dataclass
class EvidenceEvent:
    source: str
    source_type: str
    author: str
    category: str
    severity: str
    evidence: str
    hidden_weight: int


@dataclass
class InsightCluster:
    category: str
    label: str
    severity: str
    score: int
    source_count: int
    evidence_count: int
    why_it_matters: str
    opportunity: str
    representative_quotes: List[str] = field(default_factory=list)


@dataclass
class ActionItem:
    priority: str
    title: str
    owner: str
    expected_impact: str
    evidence_categories: List[str]


@dataclass
class AnalysisResult:
    product: str
    domain: str
    generated_at: str
    hidden_signal_score: int
    domain_fit_score: int
    top_cluster: InsightCluster
    clusters: List[InsightCluster] = field(default_factory=list)
    evidence_events: List[EvidenceEvent] = field(default_factory=list)
    action_plan: List[ActionItem] = field(default_factory=list)
    recommended_tier: Dict[str, Any] = field(default_factory=dict)
    founder_summary: Dict[str, Any] = field(default_factory=dict)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_feedback_bundle(source: Path | Mapping[str, Any]) -> Dict[str, Any]:
    if isinstance(source, Path):
        raw = json.loads(source.read_text(encoding="utf-8"))
    else:
        raw = dict(source)
    return {
        "product": str(raw.get("product", "Unknown product")).strip() or "Unknown product",
        "domain": str(raw.get("domain", DOMAIN)).strip() or DOMAIN,
        "sources": [
            {
                "source": str(item.get("source", "Unknown source")).strip() or "Unknown source",
                "source_type": str(item.get("source_type", "public_review")).strip() or "public_review",
                "author": str(item.get("author", "anonymous")).strip() or "anonymous",
                "text": str(item.get("text", "")).strip(),
            }
            for item in raw.get("sources", [])
            if str(item.get("text", "")).strip()
        ],
    }


def _sentence_fragments(text: str) -> List[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [part.strip() for part in parts if part.strip()]


def _matched_tokens(text: str, tokens: Iterable[str]) -> List[str]:
    lower = text.lower()
    return [token for token in tokens if token in lower]


def _has_risk_context(text: str) -> bool:
    lower = text.lower()
    if "no major bugs" in lower and not any(token in lower for token in ("failed", "broken", "churn", "surprise", "overage")):
        return False
    return any(token in lower for token in RISK_CONTEXT_TOKENS)


def _severity(score: int) -> str:
    if score >= 80:
        return "critical"
    if score >= 55:
        return "high"
    if score >= 30:
        return "medium"
    if score >= 10:
        return "low"
    return "positive"


def extract_evidence(bundle: Mapping[str, Any]) -> List[EvidenceEvent]:
    events: List[EvidenceEvent] = []
    for source in bundle.get("sources", []):
        source_type = str(source["source_type"])
        multiplier = SOURCE_MULTIPLIERS.get(source_type, 1.0)
        fragments = _sentence_fragments(str(source["text"]))
        for category, rule in CLUSTER_RULES.items():
            matches = _matched_tokens(str(source["text"]), rule["tokens"])
            if not matches:
                continue
            if category != "customer_love" and not _has_risk_context(str(source["text"])):
                continue
            quote = next((fragment for fragment in fragments if _matched_tokens(fragment, rule["tokens"])), str(source["text"]))
            base = int(abs(rule["weight"]) + len(matches) * 4)
            hidden_weight = int(base * multiplier)
            events.append(
                EvidenceEvent(
                    source=str(source["source"]),
                    source_type=source_type,
                    author=str(source["author"]),
                    category=category,
                    severity=_severity(hidden_weight),
                    evidence=quote[:240],
                    hidden_weight=hidden_weight if rule["weight"] > 0 else -hidden_weight,
                )
            )
    if not events and bundle.get("sources"):
        source = bundle["sources"][0]
        events.append(
            EvidenceEvent(
                source=str(source["source"]),
                source_type=str(source["source_type"]),
                author=str(source["author"]),
                category="customer_love",
                severity="positive",
                evidence=str(source["text"])[:240],
                hidden_weight=-10,
            )
        )
    return events


def build_clusters(events: List[EvidenceEvent]) -> List[InsightCluster]:
    clusters: List[InsightCluster] = []
    grouped: Dict[str, List[EvidenceEvent]] = {}
    for event in events:
        grouped.setdefault(event.category, []).append(event)

    for category, category_events in grouped.items():
        rule = CLUSTER_RULES[category]
        positive_only = category == "customer_love"
        score = sum(event.hidden_weight for event in category_events)
        if positive_only:
            score = max(1, abs(score) // 2)
        else:
            score = max(1, score)
        sources = {event.source for event in category_events}
        clusters.append(
            InsightCluster(
                category=category,
                label=str(rule["label"]),
                severity=_severity(score),
                score=min(100, score),
                source_count=len(sources),
                evidence_count=len(category_events),
                why_it_matters=str(rule["why_it_matters"]),
                opportunity=str(rule["opportunity"]),
                representative_quotes=[event.evidence for event in category_events[:3]],
            )
        )
    return sorted(clusters, key=lambda cluster: cluster.score, reverse=True)


def calculate_hidden_signal_score(clusters: List[InsightCluster], events: List[EvidenceEvent]) -> int:
    if not clusters:
        return 0
    negative = [cluster for cluster in clusters if cluster.category != "customer_love"]
    if not negative:
        return min(30, max(cluster.score for cluster in clusters))
    channel_bonus = len({event.source_type for event in events if event.hidden_weight > 0}) * 6
    top_three = sum(cluster.score for cluster in negative[:3])
    return max(0, min(97, int(top_three * 0.72 + channel_bonus)))


def calculate_domain_fit_score(bundle: Mapping[str, Any], events: List[EvidenceEvent]) -> int:
    domain_hits = 45 if str(bundle.get("domain", DOMAIN)).lower() == DOMAIN else 25
    hidden_sources = sum(1 for event in events if event.source_type in {"public_shadow_channel", "private_sales_note", "private_support"})
    hidden_bonus = min(40, hidden_sources * 8)
    text = " ".join(str(source["text"]) for source in bundle.get("sources", [])).lower()
    explicit_bonus = 15 if "hidden" in text or "reviews" in text else 8
    return min(100, domain_hits + hidden_bonus + explicit_bonus)


def recommend_subscription_tier(customer_count: int) -> Dict[str, Any]:
    estimated_items = max(100, customer_count * 3)
    for tier in SUBSCRIPTION_TIERS:
        if estimated_items <= tier["included_feedback_items"]:
            return dict(tier)
    return dict(SUBSCRIPTION_TIERS[-1])


def build_action_plan(clusters: List[InsightCluster], product: str) -> List[ActionItem]:
    actions: List[ActionItem] = []
    for index, cluster in enumerate([item for item in clusters if item.category != "customer_love"][:6], start=1):
        priority = "P0" if index <= 2 else "P1"
        if cluster.category == "pricing_trust":
            title = "Launch pricing-alert guardrails and rewrite hidden overage language"
            impact = "Reduce churn risk and rescue expansion conversations before finance escalates."
        elif cluster.category == "integration_reliability":
            title = "Add replay-safe webhook diagnostics and duplicate invoice protection"
            impact = "Protect operational trust for finance teams during month-end workflows."
        elif cluster.category == "onboarding_confusion":
            title = "Ship guided onboarding with visible failed-import evidence"
            impact = "Shorten time to value and stop silent setup failures from becoming public complaints."
        elif cluster.category == "executive_visibility":
            title = "Send weekly hidden-review digest to product and founder stakeholders"
            impact = "Expose cross-channel patterns before they become churn."
        elif cluster.category == "competitor_pressure":
            title = "Create competitor-loss review board and counter-positioning copy"
            impact = "Turn lost-deal language into roadmap and sales enablement."
        else:
            title = f"Resolve {cluster.label.lower()} for {product}"
            impact = cluster.opportunity
        actions.append(
            ActionItem(
                priority=priority,
                title=title,
                owner="Product lead" if index <= 3 else "Growth lead",
                expected_impact=impact,
                evidence_categories=[cluster.category],
            )
        )
    if len(actions) < 6:
        actions.append(
            ActionItem(
                priority="P1",
                title="Instrument public shadow-channel monitoring",
                owner="Customer intelligence",
                expected_impact="Keep Reddit, GitHub, community, and app-store pain visible in one review cockpit.",
                evidence_categories=["executive_visibility"],
            )
        )
        actions.append(
            ActionItem(
                priority="P2",
                title="Create a customer-proof changelog tied to review themes",
                owner="Product marketing",
                expected_impact="Show customers that hidden feedback becomes shipped improvements.",
                evidence_categories=["pricing_trust", "onboarding_confusion"],
            )
        )
    return actions[:7]


def analyze_feedback_bundle(bundle_input: Path | Mapping[str, Any], customer_count: int = 1000) -> AnalysisResult:
    bundle = load_feedback_bundle(bundle_input) if not isinstance(bundle_input, Mapping) else load_feedback_bundle(bundle_input)
    events = extract_evidence(bundle)
    clusters = build_clusters(events)
    if not clusters:
        clusters = [
            InsightCluster(
                category="customer_love",
                label="Customer love",
                severity="positive",
                score=1,
                source_count=0,
                evidence_count=0,
                why_it_matters=str(CLUSTER_RULES["customer_love"]["why_it_matters"]),
                opportunity=str(CLUSTER_RULES["customer_love"]["opportunity"]),
                representative_quotes=[],
            )
        ]
    hidden_score = calculate_hidden_signal_score(clusters, events)
    domain_fit = calculate_domain_fit_score(bundle, events)
    top_cluster = clusters[0]
    recommended_tier = recommend_subscription_tier(customer_count)
    return AnalysisResult(
        product=str(bundle["product"]),
        domain=str(bundle["domain"]),
        generated_at=now_utc(),
        hidden_signal_score=hidden_score,
        domain_fit_score=domain_fit,
        top_cluster=top_cluster,
        clusters=clusters,
        evidence_events=events,
        action_plan=build_action_plan(clusters, str(bundle["product"])),
        recommended_tier=recommended_tier,
        founder_summary={
            "one_line": f"{DOMAIN} finds the reviews customers never put in one place.",
            "domain_connection": "The domain is literal: hidden.reviews becomes the command center for buried customer truth.",
            "buyer": "Founders, PMs, and customer success teams at SaaS companies with fragmented feedback channels.",
            "why_now": "AI lets teams scrape, cluster, and operationalize feedback faster than manual review meetings.",
        },
    )


def result_to_dict(result: AnalysisResult) -> Dict[str, Any]:
    return asdict(result)


def build_founder_brief(result: AnalysisResult) -> str:
    clusters = "\n".join(
        f"- **{cluster.label}** ({cluster.score}/100): {cluster.why_it_matters}"
        for cluster in result.clusters[:6]
    )
    actions = "\n".join(
        f"- [{action.priority}] {action.title} - {action.expected_impact}"
        for action in result.action_plan
    )
    return f"""# Hidden Reviews AI Founder Brief

## Product

{result.product}

## Domain

{result.domain}

## Hidden Signal Score

{result.hidden_signal_score}/100

## Top Hidden Review Pattern

{result.top_cluster.label}: {result.top_cluster.why_it_matters}

## Evidence Clusters

{clusters}

## Action Plan

{actions}

## Business Model

Recommended plan: {result.recommended_tier["name"]} at ${result.recommended_tier["monthly_price_usd"]}/month.

## Judge Takeaway

Hidden Reviews AI turns a Domain Roulette name into a real product: a command center for customer truth scattered across Reddit, GitHub issues, app reviews, support email, sales notes, and community chat.
"""


def build_domain_pitch(result: AnalysisResult) -> str:
    return f"""# Why hidden.reviews Works

The product is named **hidden.reviews** because the most useful customer feedback rarely lives in one review page. It is hidden in:

- Reddit threads
- GitHub issues
- Discord/community chat
- Support tickets
- Sales call notes
- App reviews

Hidden Reviews AI finds those scattered signals, groups them into product risks, and gives founders a ranked action plan.

**Domain fit score:** {result.domain_fit_score}/100

**Tagline:** Find the reviews customers never put in one place.
"""


def evidence_csv(result: AnalysisResult) -> str:
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=["source", "source_type", "author", "category", "severity", "hidden_weight", "evidence"])
    writer.writeheader()
    for event in result.evidence_events:
        writer.writerow(asdict(event))
    return buf.getvalue()


def export_demo_artifacts(result: AnalysisResult, output_dir: Path = DEFAULT_OUTPUT) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    analysis = output_dir / "analysis_result.json"
    brief = output_dir / "founder_brief.md"
    evidence = output_dir / "evidence_events.csv"
    pitch = output_dir / "domain_pitch.md"
    pricing = output_dir / "pricing_model.json"
    analysis.write_text(json.dumps(result_to_dict(result), indent=2), encoding="utf-8")
    brief.write_text(build_founder_brief(result), encoding="utf-8")
    evidence.write_text(evidence_csv(result), encoding="utf-8")
    pitch.write_text(build_domain_pitch(result), encoding="utf-8")
    pricing.write_text(json.dumps(SUBSCRIPTION_TIERS, indent=2), encoding="utf-8")
    return {
        "analysis": str(analysis),
        "brief": str(brief),
        "evidence_csv": str(evidence),
        "domain_pitch": str(pitch),
        "pricing": str(pricing),
    }


def build_dashboard_html(result: AnalysisResult) -> str:
    def esc(value: Any) -> str:
        return html.escape(str(value))

    cluster_rows = "\n".join(
        f"<tr><td>{esc(cluster.label)}</td><td>{cluster.score}</td><td>{esc(cluster.source_count)}</td><td>{esc(cluster.opportunity)}</td></tr>"
        for cluster in result.clusters
    )
    action_rows = "\n".join(
        f"<li><strong>{esc(action.priority)}</strong> {esc(action.title)}<span>{esc(action.expected_impact)}</span></li>"
        for action in result.action_plan
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Hidden Reviews AI Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 40px; color: #161d19; }}
    h1 {{ font-size: 42px; }}
    .score {{ font-size: 54px; color: #0f766e; font-weight: 800; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
    td, th {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
    li {{ margin: 12px 0; }}
    li span {{ display: block; color: #59655f; }}
  </style>
</head>
<body>
  <h1>{esc(result.domain)} report for {esc(result.product)}</h1>
  <p class="score">{result.hidden_signal_score}/100 hidden signal</p>
  <h2>Top Pattern: {esc(result.top_cluster.label)}</h2>
  <p>{esc(result.top_cluster.why_it_matters)}</p>
  <h2>Clusters</h2>
  <table><thead><tr><th>Cluster</th><th>Score</th><th>Sources</th><th>Opportunity</th></tr></thead><tbody>{cluster_rows}</tbody></table>
  <h2>Action Plan</h2>
  <ul>{action_rows}</ul>
</body>
</html>"""


class HiddenReviewsHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json({"status": "ok", "service": "hidden-reviews-ai"})
            return
        if self.path == "/pricing":
            self._send_json(SUBSCRIPTION_TIERS)
            return
        self._send_json({"error": "not found", "paths": ["/health", "/pricing", "/analyze"]}, 404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/analyze":
            self._send_json({"error": "not found"}, 404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload: MutableMapping[str, Any] = json.loads(self.rfile.read(length).decode("utf-8"))
            customer_count = int(payload.pop("customer_count", 1000))
            result = analyze_feedback_bundle(payload, customer_count=customer_count)
            self._send_json(result_to_dict(result))
        except Exception as exc:  # pragma: no cover - defensive HTTP boundary
            self._send_json({"error": str(exc)}, 400)


def run_server(host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), HiddenReviewsHandler)
    print(f"Hidden Reviews AI API listening on http://{host}:{port}")
    print("POST /analyze, GET /health, GET /pricing")
    server.serve_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="hidden.reviews customer intelligence agent")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Run sample feedback analysis and export artifacts")
    demo.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    demo.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    demo.add_argument("--customer-count", type=int, default=1800)

    analyze = sub.add_parser("analyze", help="Analyze a feedback JSON file")
    analyze.add_argument("input", type=Path)
    analyze.add_argument("--customer-count", type=int, default=1000)

    serve = sub.add_parser("serve", help="Run local API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8092)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "demo":
        result = analyze_feedback_bundle(args.input, customer_count=args.customer_count)
        paths = export_demo_artifacts(result, args.output)
        (args.output / "dashboard_report.html").write_text(build_dashboard_html(result), encoding="utf-8")
        print(json.dumps({"domain": result.domain, "hidden_signal_score": result.hidden_signal_score, "top_cluster": result.top_cluster.category, "artifacts": paths}, indent=2))
        return 0
    if args.command == "analyze":
        result = analyze_feedback_bundle(args.input, customer_count=args.customer_count)
        print(json.dumps(result_to_dict(result), indent=2))
        return 0
    if args.command == "serve":
        run_server(args.host, args.port)
        return 0
    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
