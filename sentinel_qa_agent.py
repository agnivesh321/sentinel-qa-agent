#!/usr/bin/env python3
"""
Sentinel QA Agent

UiPath AgentHack Track 3 submission core.

The agent converts product changes into a security-aware regression test plan,
simulates the UiPath Test Cloud orchestration loop for local demos, and exports
artifacts that can be connected to UiPath Automation Cloud once credentials are
available.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "demo_input" / "sample_change.json"
DEFAULT_OUTPUT = ROOT / "demo_output"

SECURITY_PATTERNS = {
    "authentication": {
        "tokens": ("auth", "login", "session", "jwt", "oauth", "password", "role", "permission"),
        "impact": "Unauthorized access or privilege escalation can reach production users.",
        "tests": (
            "Verify unauthenticated users cannot access protected actions.",
            "Verify lower-privilege users cannot call admin or owner-only actions.",
            "Verify session expiry and refresh behavior after identity changes.",
        ),
    },
    "payment": {
        "tokens": ("payment", "checkout", "invoice", "billing", "stripe", "refund", "price", "subscription"),
        "impact": "Payment regressions can create revenue loss, fraud, or customer trust issues.",
        "tests": (
            "Verify price, currency, tax, and discount values are not client-trustable.",
            "Verify failed payment and retry states do not duplicate orders.",
            "Verify refunds and cancellation paths require the correct actor.",
        ),
    },
    "data_exposure": {
        "tokens": ("export", "download", "pii", "email", "phone", "address", "csv", "report", "customer"),
        "impact": "Sensitive data exposure can trigger compliance and privacy incidents.",
        "tests": (
            "Verify exported files contain only fields allowed for the user's role.",
            "Verify direct object references cannot retrieve another tenant's records.",
            "Verify audit logs capture sensitive-data access.",
        ),
    },
    "file_upload": {
        "tokens": ("upload", "file", "attachment", "image", "pdf", "document", "import"),
        "impact": "File handling bugs can create malware, storage, or data-parsing risk.",
        "tests": (
            "Verify rejected file types, oversize files, and malformed files are blocked.",
            "Verify upload paths cannot overwrite existing files or escape storage scope.",
            "Verify imported content is scanned and safely parsed before use.",
        ),
    },
    "ai_agent": {
        "tokens": ("agent", "prompt", "llm", "model", "tool", "autonomous", "ai", "gemini", "openai"),
        "impact": "AI agent changes can create unsafe tool calls, prompt injection, or unreviewed decisions.",
        "tests": (
            "Verify prompt-injection content cannot trigger unauthorized tool use.",
            "Verify the agent asks for human approval before irreversible actions.",
            "Verify tool output is validated before being written to systems of record.",
        ),
    },
    "external_integration": {
        "tokens": ("api", "webhook", "integration", "sync", "github", "slack", "crm", "erp", "vendor"),
        "impact": "Integration failures can silently corrupt downstream workflows.",
        "tests": (
            "Verify retry, timeout, duplicate-event, and partial-failure handling.",
            "Verify webhook signatures or trusted-source checks are enforced.",
            "Verify external API errors route to a human review queue.",
        ),
    },
}

QUALITY_PATTERNS = {
    "high_churn": ("refactor", "migration", "rewrite", "replace", "new flow", "breaking"),
    "state_machine": ("status", "state", "stage", "approval", "queue", "workflow"),
    "user_experience": ("dashboard", "form", "button", "mobile", "screen", "page"),
    "data_consistency": ("cache", "database", "schema", "record", "transaction", "idempotent"),
}

FAILURE_LIBRARY = {
    "authentication": "Lower-privilege user unexpectedly reached admin billing action.",
    "payment": "Checkout retry produced two invoice records for one approved payment.",
    "data_exposure": "CSV export included customer email for viewer role.",
    "file_upload": "Oversize PDF was accepted and never scanned.",
    "ai_agent": "Prompt injection attempted to bypass human approval before a release decision.",
    "external_integration": "Webhook replay created duplicate downstream tasks.",
}


@dataclass
class ChangeInput:
    title: str
    summary: str
    changed_files: List[str]
    diff_excerpt: str = ""
    business_context: str = ""
    release_deadline: str = ""
    owner: str = "Release owner"


@dataclass
class RiskSignal:
    category: str
    severity: str
    score: int
    evidence: List[str]
    impact: str


@dataclass
class TestCase:
    id: str
    title: str
    category: str
    priority: str
    automation_target: str
    preconditions: List[str]
    steps: List[str]
    expected_result: str
    ui_path_asset: str
    human_gate: bool = False


@dataclass
class TestRunResult:
    test_id: str
    status: str
    duration_seconds: int
    finding: str
    recommended_action: str


@dataclass
class AgentPlan:
    generated_at: str
    change: ChangeInput
    release_risk_score: int
    release_decision: str
    risk_signals: List[RiskSignal] = field(default_factory=list)
    test_cases: List[TestCase] = field(default_factory=list)
    simulated_results: List[TestRunResult] = field(default_factory=list)
    human_approval_required: bool = True
    orchestration_trace: List[Dict[str, Any]] = field(default_factory=list)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_change(path: Path) -> ChangeInput:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ChangeInput(
        title=str(raw.get("title", "")).strip() or "Untitled change",
        summary=str(raw.get("summary", "")).strip(),
        changed_files=[str(item) for item in raw.get("changed_files", [])],
        diff_excerpt=str(raw.get("diff_excerpt", "")).strip(),
        business_context=str(raw.get("business_context", "")).strip(),
        release_deadline=str(raw.get("release_deadline", "")).strip(),
        owner=str(raw.get("owner", "Release owner")).strip() or "Release owner",
    )


def haystack(change: ChangeInput) -> str:
    return " ".join(
        [
            change.title,
            change.summary,
            change.diff_excerpt,
            change.business_context,
            " ".join(change.changed_files),
        ]
    ).lower()


def find_evidence(tokens: Iterable[str], text: str, files: Iterable[str]) -> List[str]:
    evidence = []
    for token in tokens:
        if token in text:
            evidence.append(f"keyword:{token}")
    for file_name in files:
        low = file_name.lower()
        if any(token in low for token in tokens):
            evidence.append(f"file:{file_name}")
    return evidence[:8]


def severity_from_score(score: int) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 38:
        return "medium"
    return "low"


def analyze_risks(change: ChangeInput) -> List[RiskSignal]:
    text = haystack(change)
    risks: List[RiskSignal] = []
    for category, spec in SECURITY_PATTERNS.items():
        evidence = find_evidence(spec["tokens"], text, change.changed_files)
        if not evidence:
            continue
        file_bonus = min(20, len([e for e in evidence if e.startswith("file:")]) * 6)
        keyword_bonus = min(28, len([e for e in evidence if e.startswith("keyword:")]) * 4)
        base = 30 + file_bonus + keyword_bonus
        if category in ("authentication", "payment", "ai_agent"):
            base += 12
        risks.append(
            RiskSignal(
                category=category,
                severity=severity_from_score(base),
                score=min(100, base),
                evidence=evidence,
                impact=spec["impact"],
            )
        )

    for category, tokens in QUALITY_PATTERNS.items():
        evidence = find_evidence(tokens, text, change.changed_files)
        if evidence:
            score = 24 + min(22, len(evidence) * 5)
            risks.append(
                RiskSignal(
                    category=category,
                    severity=severity_from_score(score),
                    score=score,
                    evidence=evidence,
                    impact="Quality signal that can increase regression coverage requirements.",
                )
            )

    risks.sort(key=lambda risk: risk.score, reverse=True)
    return risks


def release_score(risks: List[RiskSignal]) -> int:
    if not risks:
        return 18
    top = max(risk.score for risk in risks)
    aggregate = min(35, int(sum(risk.score for risk in risks) / max(1, len(risks)) * 0.35))
    return min(100, top + aggregate)


def release_decision(score: int, results: List[TestRunResult]) -> str:
    failed = [result for result in results if result.status == "failed"]
    if score >= 82 or failed:
        return "BLOCK_RELEASE_PENDING_HUMAN_REVIEW"
    if score >= 58:
        return "CONDITIONAL_RELEASE_AFTER_APPROVAL"
    return "APPROVE_LOW_RISK_RELEASE"


def make_test_id(index: int, category: str) -> str:
    return f"SQA-{index:03d}-{category.replace('_', '-').upper()}"


def generate_tests(change: ChangeInput, risks: List[RiskSignal]) -> List[TestCase]:
    tests: List[TestCase] = []
    selected = risks[:8] or [
        RiskSignal(
            category="baseline_regression",
            severity="medium",
            score=40,
            evidence=["default:change submitted"],
            impact="Baseline regression coverage required before release.",
        )
    ]
    for index, risk in enumerate(selected, start=1):
        spec = SECURITY_PATTERNS.get(risk.category)
        scenarios = spec["tests"] if spec else (
            "Verify the changed workflow still completes successfully.",
            "Verify rollback and error handling produce a clear human-visible state.",
            "Verify audit logs include actor, action, timestamp, and changed object.",
        )
        tests.append(
            TestCase(
                id=make_test_id(index, risk.category),
                title=f"{risk.category.replace('_', ' ').title()} guardrail validation",
                category=risk.category,
                priority="P0" if risk.score >= 80 else "P1" if risk.score >= 55 else "P2",
                automation_target="UiPath Test Cloud",
                preconditions=[
                    "Test environment seeded with admin, standard user, and read-only user.",
                    "Release candidate build is deployed to staging.",
                    "UiPath robot has access only to test credentials and non-production data.",
                ],
                steps=[
                    "Create a UiPath Test Cloud test set for this risk category.",
                    scenarios[0],
                    scenarios[1],
                    scenarios[2],
                    "Capture screenshots, logs, and API traces for evidence.",
                    "Route failed or ambiguous results to the release owner for approval.",
                ],
                expected_result=(
                    "All controls behave as expected, no unauthorized action succeeds, "
                    "and any failure creates a human-review task before release."
                ),
                ui_path_asset=f"TestCloud::{risk.category}::risk-score-{risk.score}",
                human_gate=risk.score >= 55,
            )
        )
    return tests


def simulate_test_cloud_results(tests: List[TestCase], risks: List[RiskSignal]) -> List[TestRunResult]:
    severe_categories = {risk.category for risk in risks if risk.score >= 62}
    results: List[TestRunResult] = []
    for index, test in enumerate(tests, start=1):
        should_fail = test.category in severe_categories and index in (1, 2)
        status = "failed" if should_fail else "passed"
        finding = FAILURE_LIBRARY.get(test.category, "No regression detected.")
        if status == "passed":
            finding = "Validated expected control behavior in staged workflow."
        action = (
            "Block release and create a human review task in UiPath Action Center."
            if status == "failed"
            else "Keep evidence attached to the UiPath Test Cloud run."
        )
        results.append(
            TestRunResult(
                test_id=test.id,
                status=status,
                duration_seconds=35 + index * 11,
                finding=finding,
                recommended_action=action,
            )
        )
    return results


def build_trace(change: ChangeInput, risks: List[RiskSignal], tests: List[TestCase], results: List[TestRunResult]) -> List[Dict[str, Any]]:
    return [
        {
            "time": now_utc(),
            "actor": "Sentinel QA Agent",
            "step": "ingest_change",
            "detail": f"Loaded change '{change.title}' with {len(change.changed_files)} changed files.",
        },
        {
            "time": now_utc(),
            "actor": "Risk Classifier",
            "step": "classify_release_risk",
            "detail": f"Detected {len(risks)} risk signals.",
        },
        {
            "time": now_utc(),
            "actor": "Test Planner",
            "step": "generate_test_cloud_plan",
            "detail": f"Generated {len(tests)} UiPath Test Cloud candidate cases.",
        },
        {
            "time": now_utc(),
            "actor": "UiPath Orchestrator Adapter",
            "step": "simulate_test_cloud_run",
            "detail": f"Produced {len(results)} test results for demo mode.",
        },
        {
            "time": now_utc(),
            "actor": "Human Approval Gate",
            "step": "route_release_decision",
            "detail": "Release decision is not finalized until the owner reviews failed or high-risk tests.",
        },
    ]


def build_plan(change: ChangeInput) -> AgentPlan:
    risks = analyze_risks(change)
    tests = generate_tests(change, risks)
    results = simulate_test_cloud_results(tests, risks)
    score = release_score(risks)
    decision = release_decision(score, results)
    return AgentPlan(
        generated_at=now_utc(),
        change=change,
        release_risk_score=score,
        release_decision=decision,
        risk_signals=risks,
        test_cases=tests,
        simulated_results=results,
        human_approval_required=decision != "APPROVE_LOW_RISK_RELEASE",
        orchestration_trace=build_trace(change, risks, tests, results),
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def status_class(status: str) -> str:
    return "fail" if status == "failed" else "pass"


def write_dashboard(path: Path, plan: AgentPlan) -> None:
    risk_cards = []
    for risk in plan.risk_signals:
        risk_cards.append(
            f"""
            <article class="risk {esc(risk.severity)}">
              <div class="row"><strong>{esc(risk.category.replace('_', ' ').title())}</strong><span>{risk.score}</span></div>
              <p>{esc(risk.impact)}</p>
              <small>{esc(', '.join(risk.evidence))}</small>
            </article>
            """
        )
    test_rows = []
    for test in plan.test_cases:
        result = next((item for item in plan.simulated_results if item.test_id == test.id), None)
        status = result.status if result else "queued"
        test_rows.append(
            "<tr>"
            f"<td>{esc(test.id)}</td>"
            f"<td>{esc(test.title)}</td>"
            f"<td>{esc(test.priority)}</td>"
            f"<td>{esc(test.ui_path_asset)}</td>"
            f"<td><span class='badge {status_class(status)}'>{esc(status)}</span></td>"
            f"<td>{esc(result.finding if result else 'Queued for UiPath Test Cloud')}</td>"
            "</tr>"
        )
    trace_items = "".join(
        f"<li><strong>{esc(step['actor'])}</strong>: {esc(step['detail'])}</li>"
        for step in plan.orchestration_trace
    )
    path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sentinel QA Agent</title>
  <style>
    :root {{
      --ink: #172026;
      --muted: #66717d;
      --line: #d8e0e7;
      --panel: #f7f9fb;
      --accent: #0f6f70;
      --danger: #a82619;
      --warn: #9b650d;
      --good: #0f7a39;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; color: var(--ink); background: #ffffff; }}
    header {{ padding: 34px 44px 24px; border-bottom: 1px solid var(--line); }}
    main {{ padding: 30px 44px 44px; max-width: 1280px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; letter-spacing: 0; }}
    h2 {{ margin: 30px 0 14px; font-size: 20px; letter-spacing: 0; }}
    p {{ line-height: 1.5; }}
    .meta {{ color: var(--muted); }}
    .decision {{ display: grid; grid-template-columns: repeat(4, minmax(150px, 1fr)); gap: 12px; margin-top: 20px; }}
    .metric {{ border: 1px solid var(--line); border-radius: 8px; background: var(--panel); padding: 14px; min-height: 92px; }}
    .metric strong {{ display: block; margin-top: 8px; font-size: 24px; color: var(--accent); overflow-wrap: anywhere; }}
    .metric.block strong {{ color: var(--danger); }}
    .grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
    .risk {{ border: 1px solid var(--line); border-radius: 8px; padding: 14px; background: #fff; }}
    .risk.critical, .risk.high {{ border-left: 5px solid var(--danger); }}
    .risk.medium {{ border-left: 5px solid var(--warn); }}
    .risk.low {{ border-left: 5px solid var(--good); }}
    .risk .row {{ display: flex; justify-content: space-between; gap: 12px; }}
    .risk small {{ color: var(--muted); overflow-wrap: anywhere; }}
    table {{ width: 100%; border-collapse: collapse; border: 1px solid var(--line); }}
    th, td {{ padding: 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ background: #eef3f7; }}
    .badge {{ display: inline-block; min-width: 64px; text-align: center; border-radius: 999px; padding: 4px 8px; color: #fff; font-weight: 700; }}
    .badge.pass {{ background: var(--good); }}
    .badge.fail {{ background: var(--danger); }}
    ol {{ line-height: 1.6; }}
    @media (max-width: 900px) {{
      header, main {{ padding-left: 18px; padding-right: 18px; }}
      .decision, .grid {{ grid-template-columns: 1fr; }}
      table {{ display: block; overflow-x: auto; white-space: nowrap; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Sentinel QA Agent</h1>
    <div class="meta">UiPath AgentHack Track 3: Test Cloud. Generated {esc(plan.generated_at)}.</div>
  </header>
  <main>
    <p>{esc(plan.change.summary)}</p>
    <section class="decision">
      <div class="metric"><span>Release Risk</span><strong>{plan.release_risk_score}/100</strong></div>
      <div class="metric block"><span>Decision</span><strong>{esc(plan.release_decision.replace('_', ' '))}</strong></div>
      <div class="metric"><span>Generated Tests</span><strong>{len(plan.test_cases)}</strong></div>
      <div class="metric"><span>Human Gate</span><strong>{'Required' if plan.human_approval_required else 'Not Required'}</strong></div>
    </section>
    <h2>Risk Signals</h2>
    <section class="grid">{''.join(risk_cards)}</section>
    <h2>UiPath Test Cloud Plan</h2>
    <table>
      <thead><tr><th>ID</th><th>Test</th><th>Priority</th><th>UiPath Asset</th><th>Status</th><th>Finding</th></tr></thead>
      <tbody>{''.join(test_rows)}</tbody>
    </table>
    <h2>Orchestration Trace</h2>
    <ol>{trace_items}</ol>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


def write_markdown_report(path: Path, plan: AgentPlan) -> None:
    lines = [
        "# Sentinel QA Agent Report",
        "",
        f"Generated: {plan.generated_at}",
        f"Change: {plan.change.title}",
        f"Release risk score: {plan.release_risk_score}/100",
        f"Decision: {plan.release_decision}",
        "",
        "## Business Context",
        "",
        plan.change.business_context or plan.change.summary,
        "",
        "## Risk Signals",
        "",
    ]
    for risk in plan.risk_signals:
        lines.extend(
            [
                f"- {risk.category} ({risk.severity}, {risk.score}/100)",
                f"  Evidence: {', '.join(risk.evidence)}",
                f"  Impact: {risk.impact}",
            ]
        )
    lines.extend(["", "## Test Cloud Cases", ""])
    for test in plan.test_cases:
        lines.extend(
            [
                f"### {test.id}: {test.title}",
                "",
                f"- Priority: {test.priority}",
                f"- UiPath asset: {test.ui_path_asset}",
                f"- Human gate: {'yes' if test.human_gate else 'no'}",
                "- Steps:",
            ]
        )
        for step in test.steps:
            lines.append(f"  - {step}")
        lines.append(f"- Expected: {test.expected_result}")
        lines.append("")
    lines.extend(["## Simulated Results", ""])
    for result in plan.simulated_results:
        lines.extend(
            [
                f"- {result.test_id}: {result.status}",
                f"  Finding: {result.finding}",
                f"  Action: {result.recommended_action}",
            ]
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_uipath_payloads(output_dir: Path, plan: AgentPlan) -> None:
    test_set = {
        "name": f"Sentinel QA - {plan.change.title}",
        "description": plan.change.summary,
        "releaseDecision": plan.release_decision,
        "riskScore": plan.release_risk_score,
        "testCases": [asdict(test) for test in plan.test_cases],
    }
    action_center_tasks = []
    if plan.human_approval_required:
        action_center_tasks.append(
            {
                "title": f"Approve or block release: {plan.change.title}",
                "assignedTo": plan.change.owner,
                "priority": "High" if plan.release_risk_score >= 82 else "Normal",
                "description": (
                    f"Sentinel QA scored this release {plan.release_risk_score}/100 and "
                    f"returned {plan.release_decision}."
                ),
                "recommendedAction": "Review failed evidence, approve a fix plan, or explicitly override the release gate.",
            }
        )
    for result in plan.simulated_results:
        if result.status != "failed":
            continue
        action_center_tasks.append(
            {
                "title": f"Review failed test {result.test_id}",
                "assignedTo": plan.change.owner,
                "priority": "High",
                "description": result.finding,
                "recommendedAction": result.recommended_action,
            }
        )
    write_json(output_dir / "uipath_test_set_payload.json", test_set)
    write_json(output_dir / "uipath_action_center_tasks.json", action_center_tasks)


def run_demo(input_path: Path, output_dir: Path) -> AgentPlan:
    output_dir.mkdir(parents=True, exist_ok=True)
    change = read_change(input_path)
    plan = build_plan(change)
    write_json(output_dir / "agent_plan.json", asdict(plan))
    write_dashboard(output_dir / "dashboard.html", plan)
    write_markdown_report(output_dir / "sentinel_report.md", plan)
    write_uipath_payloads(output_dir, plan)
    return plan


class Handler(BaseHTTPRequestHandler):
    def _json(self, payload: Dict[str, Any], status: int = 200) -> None:
        raw = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _html(self, payload: str, status: int = 200) -> None:
        raw = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            self._json({"ok": True, "time": now_utc()})
            return
        dashboard = DEFAULT_OUTPUT / "dashboard.html"
        if self.path in ("/", "/dashboard") and dashboard.exists():
            self._html(dashboard.read_text(encoding="utf-8"))
            return
        self._json({"error": "not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/analyze":
            self._json({"error": "not found"}, status=404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        payload = json.loads(raw)
        temp = DEFAULT_OUTPUT / "request_change.json"
        write_json(temp, payload)
        plan = run_demo(temp, DEFAULT_OUTPUT)
        self._json({"plan": asdict(plan), "dashboard": str(DEFAULT_OUTPUT / "dashboard.html")})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a UiPath Test Cloud security regression plan.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Run the local Sentinel QA demo.")
    demo.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    demo.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    server = sub.add_parser("serve", help="Serve local dashboard/API.")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8081")))
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "serve":
        httpd = ThreadingHTTPServer((args.host, args.port), Handler)
        print(f"Serving Sentinel QA Agent on http://{args.host}:{args.port}")
        httpd.serve_forever()
        return 0
    plan = run_demo(args.input, args.output_dir)
    print("Sentinel QA Agent demo complete.")
    print(f"Decision: {plan.release_decision}")
    print(f"Risk score: {plan.release_risk_score}/100")
    print(f"Dashboard: {args.output_dir / 'dashboard.html'}")
    print(f"Report: {args.output_dir / 'sentinel_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
