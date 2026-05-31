# Sentinel Release Guard - AlgoFest Pitch Deck

## Slide 1 - Title

Sentinel Release Guard

AI release-risk agent for safer software launches.

## Slide 2 - Problem

AI makes software delivery faster, but release review has not caught up. Risky changes touching payments, auth, data, or autonomous agents can pass shallow checks and still create production incidents.

## Slide 3 - Solution

Sentinel reads the change, scores release risk, generates targeted security regression gates, simulates CI evidence, and blocks unsafe releases until a human owner reviews the proof.

## Slide 4 - Demo Scenario

AI-assisted invoice refund workflow:

- AI recommends refunds
- Billing logic changes
- Auth roles change
- ERP webhook sync changes
- Dashboard state changes

## Slide 5 - Agent Pipeline

Change input -> risk classifier -> weighted scoring -> test planner -> release gate simulator -> dashboard/report/review queue.

## Slide 6 - Risk Model

The scoring engine detects auth, payment, data exposure, file upload, AI-agent, external integration, state-machine, UX, and data-consistency signals.

## Slide 7 - Output

The agent produces:

- Release decision
- Risk score
- Generated tests
- Simulated pass/fail evidence
- Human review tasks
- GitHub PR comment
- Benchmark results

## Slide 8 - Why It Wins

Most AI hackathon projects automate happy paths. Sentinel focuses on the control layer: what should happen when the agent sees risk and must stop the release.

## Slide 9 - Tech

Python standard library, local HTTP API, JSON evidence, HTML dashboard, benchmark suite, PowerShell demo runner, unittest verification.

## Slide 10 - Roadmap

GitHub Actions integration, Playwright/pytest adapters, historical release learning, policy profiles for finance, healthcare, education, and startups.
