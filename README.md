# Sentinel QA Agent

UiPath AgentHack submission package for **Track 3: UiPath Test Cloud**.

## Elevator Pitch

Sentinel QA Agent turns risky product changes into security-aware UiPath Test Cloud plans, runs the release gate, and blocks unsafe releases until a human approves the evidence.

## Why This Can Win

Most hackathon projects show an agent doing a happy-path workflow. Sentinel QA Agent shows the missing enterprise layer: trust, testing, release governance, exception handling, and audit evidence.

The demo is designed to hit multiple judging surfaces:

- UiPath Test Cloud track fit
- Best Demo / Presentation
- Cross-Platform Integration
- Best Product Feedback
- Coding-agent bonus

## What It Does

1. Ingests a code or product change.
2. Detects security and regression risk signals.
3. Generates UiPath Test Cloud-ready test cases.
4. Simulates a Test Cloud run for local demo mode.
5. Blocks risky releases and creates Action Center-style review tasks.
6. Exports a dashboard, report, JSON plan, Test Cloud payload, and human approval queue.

## Local Demo

```powershell
python uipath_sentinel_qa_agent/sentinel_qa_agent.py demo
```

Or:

```powershell
powershell -ExecutionPolicy Bypass -File uipath_sentinel_qa_agent/scripts/run_demo.ps1
```

Open:

```text
uipath_sentinel_qa_agent/demo_output/dashboard.html
```

Run the local API:

```powershell
python uipath_sentinel_qa_agent/sentinel_qa_agent.py serve --host 127.0.0.1 --port 8081
```

API test:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8081/analyze -ContentType 'application/json' -Body (Get-Content uipath_sentinel_qa_agent/demo_input/sample_change.json -Raw)
```

## Generated Artifacts

- `demo_output/dashboard.html` - judge-facing demo dashboard
- `demo_output/sentinel_report.md` - release risk and test report
- `demo_output/agent_plan.json` - full machine-readable agent plan
- `demo_output/uipath_test_set_payload.json` - Test Cloud-style test set payload
- `demo_output/uipath_action_center_tasks.json` - human approval tasks

## UiPath Integration Plan

The local demo simulates UiPath execution so the project remains runnable without credentials. With UiPath Labs access, wire it this way:

1. Agent ingests change from GitHub or CI.
2. Agent creates Test Cloud test cases from `uipath_test_set_payload.json`.
3. UiPath Orchestrator runs the selected tests.
4. Failed or high-risk tests create Action Center tasks from `uipath_action_center_tasks.json`.
5. Human approval updates the release decision.
6. Dashboard shows the trace and final release status.

## Safety And Governance

Sentinel QA Agent does not auto-approve releases. High-risk or failed test results always route to a human gate. The system is designed for non-production test credentials and staging data.

## Devpost Positioning

Project category: AI agents, software testing, cybersecurity, developer productivity, enterprise automation.

Track: **UiPath Test Cloud**.

Core claim:

> Enterprises will not trust AI-built workflows unless agents can test, explain, and gate releases. Sentinel QA Agent makes UiPath the control plane for that trust layer.
