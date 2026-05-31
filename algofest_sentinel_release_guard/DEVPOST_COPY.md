# Devpost Copy

## Project Name

Sentinel Release Guard

## Elevator Pitch

AI release-risk agent that reads risky code changes, generates security regression gates, simulates CI evidence, and blocks unsafe releases before production.

## About The Project

### Inspiration

AI can now help teams build software very quickly, but speed creates a new problem: risky releases can move faster than the testing and review process. I wanted to build an agent that does not just generate code or answer questions. It protects the release itself.

### What It Does

Sentinel Release Guard analyzes a product or code change, detects security and regression risks, scores the release, generates targeted regression tests, simulates CI gate results, and blocks unsafe releases until a human owner reviews the evidence.

The demo scenario is an AI-assisted invoice refund workflow. The agent detects payment, authentication, AI-agent, webhook, and state-machine risk, creates targeted release-gate tests, catches simulated failures, and routes the release into a human review queue.

### How We Built It

The project is a Python agent with a transparent risk scoring engine, test planner, local HTTP API, generated HTML dashboard, JSON evidence exports, benchmark output, and automated unit tests. It uses only the Python standard library so judges can run it immediately without cloud licenses or paid API keys.

### Challenges

The main challenge was avoiding a generic AI chatbot project. I focused the build on a real engineering workflow: release governance. The agent needed to produce evidence, not just text. That meant adding risk categories, scoring, generated tests, simulated execution results, a dashboard, and benchmark cases.

### Accomplishments

- Built a runnable AI release-risk agent.
- Added risk detection for auth, payments, AI agents, webhooks, data exposure, file uploads, state machines, and UI regressions.
- Generated security-aware release-gate test cases.
- Produced dashboard, Markdown, JSON, benchmark, and PR-comment artifacts.
- Added unit tests and a no-dependency local demo.

### What We Learned

Agentic systems are most useful when they can make decisions auditable. The strongest AI developer tools are not only fast; they explain risk, preserve control, and help humans make safer calls.

### What's Next

Next steps are GitHub Actions integration, Playwright/pytest adapters, historical release outcome learning, and policy profiles for finance, healthcare, education, and startup teams.

## Built With

Python, HTML, CSS, JSON, PowerShell, unittest, GitHub, CI/CD concepts, AI agent design, cybersecurity risk scoring

## Try It Out

Repository command:

```powershell
python algofest_sentinel_release_guard\sentinel_release_guard.py demo
```

Then open:

```text
algofest_sentinel_release_guard\demo_output\dashboard.html
```
