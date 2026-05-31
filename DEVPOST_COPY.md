# Devpost Copy

## Project Name

Sentinel QA Agent

## Elevator Pitch

AI release guardian that turns risky app changes into UiPath Test Cloud plans, runs security-aware regression gates, and blocks unsafe releases for human review.

## About The Project

### Inspiration

AI agents are moving into business workflows, but enterprises still need proof before releasing software. A normal demo agent can complete a task, but a real enterprise needs testing, exception handling, release gates, and audit evidence. Sentinel QA Agent was built around that gap.

### What It Does

Sentinel QA Agent analyzes a product or code change, detects security and regression risk, generates UiPath Test Cloud-ready test cases, simulates execution for demo mode, and blocks risky releases until a human reviews the evidence.

The demo scenario is an AI-assisted invoice refund workflow. The agent detects payment, authentication, AI-agent, webhook, and state-machine risks, generates targeted tests, catches a failed payment regression, and routes the release to a human approval gate.

### How We Built It

The prototype is a Python backend with a deterministic risk engine, test planner, local HTTP API, HTML dashboard, and JSON payload exports for UiPath Test Cloud and Action Center-style review tasks. It is designed to plug into UiPath Automation Cloud once Labs access and credentials are available.

### Challenges

The hardest part was avoiding a generic chatbot submission. The project had to show enterprise value, platform fit, exception handling, and a judge-friendly demo in a short time.

### Accomplishments

- Built a runnable release-risk agent.
- Generated UiPath Test Cloud-ready test plans.
- Added human approval gates for risky failures.
- Produced a dashboard, report, JSON trace, and UiPath payloads.
- Designed the project specifically for the UiPath Test Cloud track and bonus categories.

### What We Learned

Winning agent projects need more than autonomy. They need control, traceability, governance, and a clear failure story.

### What's Next

Connect to real UiPath Test Cloud APIs, import generated cases directly into test sets, trigger Orchestrator jobs, create real Action Center tasks, and add GitHub PR comments for release decisions.

## Built With

Python, UiPath Test Cloud, UiPath Automation Cloud, UiPath Orchestrator, UiPath Action Center, HTML, JSON, OpenAPI, GitHub

## Try It Out

Use the GitHub repo and local demo command:

```powershell
python uipath_sentinel_qa_agent/sentinel_qa_agent.py demo
```
