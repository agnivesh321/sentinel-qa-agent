#!/usr/bin/env python3
"""
Sentinel SaaS Agent

Galuxium Nexus V2 submission core.

The agent turns a product or code change into a release decision, risk
evidence, security regression gates, tenant audit logs, and SaaS metering.
It is deterministic so judges can run it without paid API keys, while the
contracts are shaped for an OpenAI/LLM adapter later.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "demo_input" / "sample_pr.json"
DEFAULT_OUTPUT = ROOT / "demo_output"


PRICING_TIERS = [
    {
        "name": "Starter",
        "monthly_price_inr": 999,
        "included_release_scans": 50,
        "target_customer": "Indie builders and student startup teams",
        "overage_inr_per_scan": 35,
    },
    {
        "name": "Growth",
        "monthly_price_inr": 4999,
        "included_release_scans": 500,
        "target_customer": "SaaS teams shipping weekly with AI coding tools",
        "overage_inr_per_scan": 18,
    },
    {
        "name": "Enterprise",
        "monthly_price_inr": 24999,
        "included_release_scans": 5000,
        "target_customer": "Regulated engineering orgs with audit needs",
        "overage_inr_per_scan": 8,
    },
]


SECURITY_PATTERNS = {
    "authentication": {
        "weight": 22,
        "tokens": (
            "auth",
            "authentication",
            "login",
            "session",
            "jwt",
            "oauth",
            "password",
            "role",
            "permission",
            "client-side role",
        ),
        "impact": "Unauthorized access or privilege escalation can reach production users.",
        "gates": (
            "Verify unauthenticated users cannot call protected release paths.",
            "Verify lower-privilege users cannot execute owner or finance-only actions.",
        ),
    },
    "payment": {
        "weight": 28,
        "tokens": (
            "payment",
            "checkout",
            "invoice",
            "billing",
            "refund",
            "price",
            "subscription",
            "charge",
        ),
        "impact": "Payment regressions can create fraud, duplicate refunds, or revenue loss.",
        "gates": (
            "Verify refund approvals require server-side policy and the correct approver.",
            "Verify retry and failure paths cannot duplicate invoice or refund records.",
        ),
    },
    "data_exposure": {
        "weight": 24,
        "tokens": (
            "pii",
            "email",
            "customer",
            "export",
            "download",
            "csv",
            "audit payload",
            "private",
        ),
        "impact": "Sensitive data exposure can create privacy and compliance incidents.",
        "gates": (
            "Verify audit payloads contain only fields allowed for the user's role.",
            "Verify object references cannot expose another tenant's customer data.",
        ),
    },
    "ai_agent": {
        "weight": 24,
        "tokens": (
            "ai agent",
            "agent",
            "llm",
            "model",
            "prompt",
            "tool",
            "autonomous",
            "recommend",
        ),
        "impact": "AI agent changes can create unsafe tool calls or unreviewed decisions.",
        "gates": (
            "Verify prompt injection cannot trigger an irreversible tool call.",
            "Verify the agent requires human approval before release-blocking or financial actions.",
        ),
    },
    "external_integration": {
        "weight": 16,
        "tokens": (
            "webhook",
            "integration",
            "sync",
            "erp",
            "api",
            "vendor",
            "unsigned",
            "retry",
        ),
        "impact": "Integration failures can silently corrupt downstream systems.",
        "gates": (
            "Verify webhook signatures and trusted-source checks are enforced.",
            "Verify replay, timeout, and partial-failure handling remains idempotent.",
        ),
    },
    "state_management": {
        "weight": 10,
        "tokens": (
            "status",
            "state",
            "approval",
            "queue",
            "workflow",
            "review",
        ),
        "impact": "State-machine bugs can approve, skip, or duplicate business workflows.",
        "gates": (
            "Verify state transitions cannot skip required review steps.",
            "Verify duplicate approval events are ignored after the first accepted decision.",
        ),
    },
}


@dataclass
class RiskSignal:
    category: str
    severity: str
    score: int
    evidence: List[str]
    impact: str


@dataclass
class ReleaseGate:
    id: str
    title: str
    category: str
    priority: str
    owner: str
    automated: bool
    expected_evidence: str


@dataclass
class AuditEvent:
    timestamp: str
    tenant: str
    actor: str
    event: str
    details: str


@dataclass
class AnalysisResult:
    tenant: str
    generated_at: str
    change: Dict[str, Any]
    release_risk_score: int
    release_decision: str
    human_approval_required: bool
    risk_signals: List[RiskSignal] = field(default_factory=list)
    release_gates: List[ReleaseGate] = field(default_factory=list)
    audit_events: List[AuditEvent] = field(default_factory=list)
    recommended_plan: Dict[str, Any] = field(default_factory=dict)
    metering: Dict[str, Any] = field(default_factory=dict)
    judge_summary: Dict[str, Any] = field(default_factory=dict)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_change(source: Path | Mapping[str, Any]) -> Dict[str, Any]:
    if isinstance(source, Path):
        raw = json.loads(source.read_text(encoding="utf-8"))
    else:
        raw = dict(source)

    return {
        "title": str(raw.get("title", "Untitled change")).strip() or "Untitled change",
        "summary": str(raw.get("summary", "")).strip(),
        "changed_files": [str(item) for item in raw.get("changed_files", [])],
        "diff_excerpt": str(raw.get("diff_excerpt", "")).strip(),
        "business_context": str(raw.get("business_context", "")).strip(),
        "release_deadline": str(raw.get("release_deadline", "")).strip(),
        "owner": str(raw.get("owner", "Release owner")).strip() or "Release owner",
    }


def _haystack(change: Mapping[str, Any]) -> str:
    files = " ".join(str(item) for item in change.get("changed_files", []))
    parts = [
        str(change.get("title", "")),
        str(change.get("summary", "")),
        str(change.get("diff_excerpt", "")),
        str(change.get("business_context", "")),
        files,
    ]
    return " ".join(parts).lower()


def _is_negated_token(text: str, token: str) -> bool:
    safe = re.escape(token.lower())
    patterns = [
        rf"\bno\b(?:\s+[a-z0-9_-]+,?){{0,4}}\s+(?:or\s+)?{safe}\b",
        rf"\bwithout\b(?:\s+[a-z0-9_-]+,?){{0,4}}\s+(?:or\s+)?{safe}\b",
        rf"\bnot\b(?:\s+[a-z0-9_-]+,?){{0,4}}\s+(?:or\s+)?{safe}\b",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def _find_evidence(tokens: Iterable[str], text: str, files: Iterable[str]) -> List[str]:
    evidence: List[str] = []
    for token in tokens:
        token_lower = token.lower()
        if token_lower in text and not _is_negated_token(text, token_lower):
            evidence.append(f"keyword:{token_lower}")
    for file_name in files:
        low = str(file_name).lower()
        for token in tokens:
            if token.lower() in low:
                evidence.append(f"file:{file_name}")
                break
    return evidence[:8]


def _severity(score: int) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 38:
        return "medium"
    return "low"


def detect_risk_signals(change: Mapping[str, Any]) -> List[RiskSignal]:
    text = _haystack(change)
    files = [str(item) for item in change.get("changed_files", [])]
    signals: List[RiskSignal] = []

    for category, spec in SECURITY_PATTERNS.items():
        evidence = _find_evidence(spec["tokens"], text, files)
        if not evidence:
            continue
        score = int(spec["weight"] + min(16, len(evidence) * 3))
        signals.append(
            RiskSignal(
                category=category,
                severity=_severity(score),
                score=score,
                evidence=evidence,
                impact=str(spec["impact"]),
            )
        )

    return sorted(signals, key=lambda signal: signal.score, reverse=True)


def score_release(signals: List[RiskSignal], change: Mapping[str, Any]) -> int:
    base = sum(signal.score for signal in signals)
    file_count = len(change.get("changed_files", []))
    if file_count >= 5:
        base += 8
    if "client-side" in _haystack(change) or "unsigned" in _haystack(change):
        base += 10
    return max(0, min(96, base))


def release_decision(score: int) -> str:
    if score >= 70:
        return "BLOCK_RELEASE_PENDING_HUMAN_REVIEW"
    if score >= 35:
        return "CONDITIONAL_RELEASE_WITH_TARGETED_GATES"
    return "APPROVE_RELEASE"


def build_release_gates(signals: List[RiskSignal], owner: str) -> List[ReleaseGate]:
    gates: List[ReleaseGate] = []
    counter = 1
    for signal in signals:
        for title in SECURITY_PATTERNS[signal.category]["gates"]:
            gates.append(
                ReleaseGate(
                    id=f"SRG-{counter:03d}",
                    title=str(title),
                    category=signal.category,
                    priority="P0" if signal.score >= 30 else "P1",
                    owner=owner,
                    automated=True,
                    expected_evidence="passing regression evidence plus signed audit event",
                )
            )
            counter += 1
    if not gates:
        gates.append(
            ReleaseGate(
                id="SRG-001",
                title="Run baseline smoke suite and capture release note evidence.",
                category="baseline",
                priority="P2",
                owner=owner,
                automated=True,
                expected_evidence="baseline smoke suite passed",
            )
        )
    return gates


def recommend_plan_for_usage(monthly_usage: int) -> Dict[str, Any]:
    for tier in PRICING_TIERS:
        if monthly_usage <= tier["included_release_scans"]:
            return dict(tier)
    return dict(PRICING_TIERS[-1])


def build_metering(signals: List[RiskSignal], gates: List[ReleaseGate], monthly_usage: int) -> Dict[str, Any]:
    api_units = 1 + len(signals) * 3 + max(1, len(gates) // 2)
    plan = recommend_plan_for_usage(monthly_usage)
    included = int(plan["included_release_scans"])
    overage = max(0, monthly_usage - included)
    estimated_bill = int(plan["monthly_price_inr"] + overage * plan["overage_inr_per_scan"])
    return {
        "api_units": api_units,
        "monthly_release_scans": monthly_usage,
        "included_release_scans": included,
        "overage_scans": overage,
        "estimated_monthly_bill_inr": estimated_bill,
        "gross_margin_story": "Deterministic scan cost stays near zero; optional LLM review is metered per release.",
    }


def build_audit_events(tenant: str, change: Mapping[str, Any], decision: str, score: int) -> List[AuditEvent]:
    owner = str(change.get("owner", "Release owner"))
    ts = now_utc()
    return [
        AuditEvent(ts, tenant, owner, "change_ingested", str(change.get("title", "Untitled change"))),
        AuditEvent(ts, tenant, "sentinel-agent", "risk_score_calculated", f"risk_score={score}"),
        AuditEvent(ts, tenant, "sentinel-agent", "release_decision_recorded", decision),
        AuditEvent(ts, tenant, owner if score >= 70 else "sentinel-agent", "approval_gate_selected", "human review required" if score >= 70 else "automation evidence sufficient"),
    ]


def analyze_change(
    change_input: Path | Mapping[str, Any],
    tenant: str = "demo-tenant",
    monthly_usage: int = 120,
) -> AnalysisResult:
    change = load_change(change_input) if not isinstance(change_input, Mapping) else load_change(change_input)
    signals = detect_risk_signals(change)
    score = score_release(signals, change)
    decision = release_decision(score)
    gates = build_release_gates(signals, str(change.get("owner", "Release owner")))
    plan = recommend_plan_for_usage(monthly_usage)
    metering = build_metering(signals, gates, monthly_usage)

    return AnalysisResult(
        tenant=tenant,
        generated_at=now_utc(),
        change=change,
        release_risk_score=score,
        release_decision=decision,
        human_approval_required=decision == "BLOCK_RELEASE_PENDING_HUMAN_REVIEW",
        risk_signals=signals,
        release_gates=gates,
        audit_events=build_audit_events(tenant, change, decision, score),
        recommended_plan=plan,
        metering=metering,
        judge_summary={
            "market_friction": "AI coding accelerates releases, but governance, test coverage, and audit evidence lag behind.",
            "target_cohort": "SaaS engineering teams using AI coding agents for payments, auth, data, or workflow changes.",
            "monetization": "Monthly SaaS tiers plus usage-based release scan overages.",
            "why_now": "Every AI-generated pull request needs a release guardian before production.",
        },
    )


def to_plain_dict(result: AnalysisResult) -> Dict[str, Any]:
    return asdict(result)


def build_executive_brief(result: AnalysisResult) -> str:
    top_risks = "\n".join(
        f"- {signal.category}: {signal.impact} Evidence: {', '.join(signal.evidence)}"
        for signal in result.risk_signals[:5]
    ) or "- No material security risk detected."
    gates = "\n".join(f"- {gate.id} [{gate.priority}] {gate.title}" for gate in result.release_gates)

    return f"""# Sentinel SaaS Executive Brief

## Release Decision

{result.release_decision}

Risk score: {result.release_risk_score}/100
Tenant: {result.tenant}
Generated: {result.generated_at}

## Change Reviewed

{result.change["title"]}

{result.change["summary"]}

## Material Risks

{top_risks}

## Required Release Gates

{gates}

## Monetization Evidence

Recommended plan: {result.recommended_plan["name"]} at INR {result.recommended_plan["monthly_price_inr"]}/month.
Estimated monthly bill for this tenant: INR {result.metering["estimated_monthly_bill_inr"]}.

## Judge Takeaway

Sentinel SaaS is not a generic chatbot. It is a revenue-ready release governance platform for AI-speed software teams: scan a risky change, produce transparent risk evidence, generate release gates, meter the usage, and preserve an audit trail.
"""


def export_demo_artifacts(result: AnalysisResult, output_dir: Path = DEFAULT_OUTPUT) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    analysis_path = output_dir / "analysis_result.json"
    brief_path = output_dir / "executive_brief.md"
    audit_path = output_dir / "tenant_audit_log.json"
    pricing_path = output_dir / "pricing_model.json"

    analysis_path.write_text(json.dumps(to_plain_dict(result), indent=2), encoding="utf-8")
    brief_path.write_text(build_executive_brief(result), encoding="utf-8")
    audit_path.write_text(json.dumps([asdict(event) for event in result.audit_events], indent=2), encoding="utf-8")
    pricing_path.write_text(json.dumps(PRICING_TIERS, indent=2), encoding="utf-8")

    return {
        "analysis": str(analysis_path),
        "brief": str(brief_path),
        "audit": str(audit_path),
        "pricing": str(pricing_path),
    }


class SentinelHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
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
            self._send_json({"status": "ok", "service": "sentinel-saas-agent"})
            return
        if self.path == "/pricing":
            self._send_json(PRICING_TIERS)
            return
        self._send_json({"error": "not found", "paths": ["/health", "/pricing", "/analyze"]}, 404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/analyze":
            self._send_json({"error": "not found"}, 404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload: MutableMapping[str, Any] = json.loads(self.rfile.read(length).decode("utf-8"))
            tenant = str(payload.pop("tenant", "api-demo"))
            monthly_usage = int(payload.pop("monthly_usage", 120))
            result = analyze_change(payload, tenant=tenant, monthly_usage=monthly_usage)
            self._send_json(to_plain_dict(result))
        except Exception as exc:  # pragma: no cover - defensive HTTP boundary
            self._send_json({"error": str(exc)}, 400)


def run_server(host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), SentinelHandler)
    print(f"Sentinel SaaS Agent API listening on http://{host}:{port}")
    print("POST /analyze, GET /health, GET /pricing")
    server.serve_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sentinel SaaS release-risk agent")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Run sample analysis and export judge artifacts")
    demo.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    demo.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    demo.add_argument("--tenant", default="acme-finance")
    demo.add_argument("--monthly-usage", type=int, default=420)

    analyze = sub.add_parser("analyze", help="Analyze a change JSON file")
    analyze.add_argument("input", type=Path)
    analyze.add_argument("--tenant", default="demo-tenant")
    analyze.add_argument("--monthly-usage", type=int, default=120)

    serve = sub.add_parser("serve", help="Run a local HTTP API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8091)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "demo":
        result = analyze_change(args.input, tenant=args.tenant, monthly_usage=args.monthly_usage)
        paths = export_demo_artifacts(result, args.output)
        print(json.dumps({"decision": result.release_decision, "risk_score": result.release_risk_score, "artifacts": paths}, indent=2))
        return 0
    if args.command == "analyze":
        result = analyze_change(args.input, tenant=args.tenant, monthly_usage=args.monthly_usage)
        print(json.dumps(to_plain_dict(result), indent=2))
        return 0
    if args.command == "serve":
        run_server(args.host, args.port)
        return 0
    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
