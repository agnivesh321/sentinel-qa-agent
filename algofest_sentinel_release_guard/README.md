# Sentinel Release Guard

AlgoFest Hackathon 2026 submission for the **AI/ML** and **Open Innovation** tracks.

## Elevator Pitch

Sentinel Release Guard is an AI release-risk agent that reads risky software changes, generates security regression gates, simulates CI evidence, and blocks unsafe releases before production.

## Why This Project Is Strong For AlgoFest

AlgoFest rewards creativity and functionality. Sentinel Release Guard is built around both:

- **Creativity:** It attacks a real gap in AI-assisted software teams: agents can build features quickly, but teams still need release safety, audit evidence, and human control.
- **Functionality:** The repo includes runnable code, deterministic risk scoring, generated release-gate test cases, simulated test results, benchmark output, a dashboard, JSON evidence, and a PR-comment artifact.

The project is not a generic chatbot. It is a practical release governance system that can be dropped into a real CI/CD workflow.

## What It Does

1. Ingests a product or code change.
2. Detects risk across authentication, payments, data exposure, file upload, AI agents, external integrations, state machines, and UX changes.
3. Scores release risk using a transparent weighted model.
4. Generates targeted security-aware regression tests.
5. Simulates release-gate execution and produces pass/fail evidence.
6. Blocks unsafe releases and creates a human-review queue.
7. Exports a judge-facing dashboard, Markdown report, JSON plan, benchmark results, and a GitHub PR comment.

## Demo Scenario

The sample demo analyzes an AI-assisted invoice refund workflow. The change touches:

- AI agent recommendations
- Payment/refund logic
- Authentication and roles
- ERP webhook sync
- Dashboard review state

Sentinel detects the high-risk path, generates release-gate tests, simulates failures, and blocks the release until the finance owner reviews evidence.

## Local Demo

From the repository root:

```powershell
python algofest_sentinel_release_guard\sentinel_release_guard.py demo
```

Or:

```powershell
powershell -ExecutionPolicy Bypass -File algofest_sentinel_release_guard\scripts\run_demo.ps1
```

Open the dashboard:

```text
algofest_sentinel_release_guard\demo_output\dashboard.html
```

Run the local API:

```powershell
python algofest_sentinel_release_guard\sentinel_release_guard.py serve --host 127.0.0.1 --port 8082
```

API smoke test:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8082/analyze -ContentType 'application/json' -Body (Get-Content algofest_sentinel_release_guard\demo_input\sample_change.json -Raw)
```

Run tests:

```powershell
python -m unittest discover -s algofest_sentinel_release_guard\tests
```

## Generated Artifacts

- `demo_output/dashboard.html` - main visual demo
- `demo_output/sentinel_report.md` - release-risk report
- `demo_output/agent_plan.json` - full machine-readable agent plan
- `demo_output/ci_release_gate.json` - CI release-gate payload
- `demo_output/human_review_queue.json` - blocked-release review tasks
- `demo_output/github_pr_comment.md` - PR comment a CI bot could post
- `demo_output/benchmark_results.json` - benchmark evidence across risk levels
- `demo_output/benchmark_summary.md` - readable benchmark summary

## Architecture

```text
Change JSON / PR diff
        |
        v
Risk classifier -> weighted risk score -> coverage planner
        |                                  |
        v                                  v
Risk signals                       Release-gate tests
        |                                  |
        +----------> CI gate simulator <---+
                           |
                           v
Dashboard + report + JSON evidence + human review queue
```

## Tech Stack

- Python standard library
- Local HTTP API
- JSON-based agent plan
- HTML/CSS dashboard
- PowerShell demo runner
- `unittest` verification suite

No cloud license or paid API key is required to run the demo.

## Safety

Sentinel Release Guard is intentionally conservative. It does not auto-approve high-risk changes. If payment, auth, AI-agent, webhook, or sensitive-data risk appears, the release must pass evidence checks or wait for a human owner.

## Future Roadmap

- Connect to GitHub Actions and post `github_pr_comment.md` automatically.
- Add real test runner adapters for Playwright, pytest, and API smoke tests.
- Store historical release outcomes to tune scoring thresholds.
- Add organization-specific policies for finance, healthcare, and education teams.
