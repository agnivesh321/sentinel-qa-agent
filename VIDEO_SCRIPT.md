# Demo Video Script

Target length: 3:30 to 4:30.

## 0:00 - 0:20 Problem

"AI agents are entering finance, HR, and operations workflows. The problem is not whether an agent can perform a task. The problem is whether an enterprise can trust the release. Sentinel QA Agent makes UiPath Test Cloud the release trust layer."

## 0:20 - 0:50 Input

Show `demo_input/sample_change.json`.

"This change adds an AI-assisted invoice refund workflow. It touches roles, billing, ERP webhooks, an AI agent, and the refund review dashboard."

## 0:50 - 1:10 Run

Run:

```powershell
python uipath_sentinel_qa_agent/sentinel_qa_agent.py demo
```

## 1:10 - 2:20 Dashboard

Open `demo_output/dashboard.html`.

Say:

"The agent scores the release 96 out of 100 risk and blocks it pending human review. It identifies payment, authentication, AI-agent, webhook, state-machine, and dashboard risks."

Show Test Cloud plan.

"Instead of generic tests, it creates UiPath Test Cloud-ready cases mapped to each risk category."

Show failed result.

"The payment test fails: retry produced duplicate invoice records. That is the kind of failure a business actually cares about."

## 2:20 - 3:10 UiPath Fit

Show:

- `demo_output/uipath_test_set_payload.json`
- `demo_output/uipath_action_center_tasks.json`
- `uipath/INTEGRATION_GUIDE.md`

Say:

"In local mode this simulates execution, but the payloads are structured for UiPath Test Cloud and Action Center. UiPath becomes the test orchestration and human approval layer."

## 3:10 - 4:00 Why It Matters

"This is not another chatbot. It is a release control plane for AI-built software. The agent plans tests, UiPath runs and records evidence, and humans approve the risky decisions."

Close:

"Sentinel QA Agent helps enterprises ship faster without turning release trust over to an unreviewed agent."
