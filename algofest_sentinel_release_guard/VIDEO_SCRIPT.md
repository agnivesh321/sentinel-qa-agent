# 2-Minute Demo Script

## 0:00 - 0:15 Problem

"AI helps teams ship software faster, but faster releases create faster mistakes. A risky change touching payments, authentication, webhooks, or AI agents should not go to production just because the build passed."

## 0:15 - 0:30 Project

"This is Sentinel Release Guard. It is an AI release-risk agent that reads a product change, scores risk, generates security-aware release tests, simulates CI gate evidence, and blocks unsafe releases for human review."

## 0:30 - 0:50 Input

"The demo change is an AI-assisted invoice refund workflow. It touches authentication, billing, ERP webhooks, AI recommendations, and dashboard state. This is exactly the kind of change where a normal happy-path test is not enough."

Show:

```powershell
python algofest_sentinel_release_guard\sentinel_release_guard.py demo
```

## 0:50 - 1:20 Dashboard

"The agent scored this release 96 out of 100 and returned BLOCK_RELEASE_PENDING_HUMAN_REVIEW. It detected payment risk, AI-agent risk, authentication risk, external integration risk, and state-machine risk."

Show generated test rows.

"It did not just describe the risk. It generated release-gate tests that target those risk categories."

## 1:20 - 1:45 Evidence

"The simulator produces pass/fail evidence. Failed checks create human review tasks, and the system exports a GitHub PR comment so this can fit into a real CI workflow."

Show:

- `human_review_queue.json`
- `github_pr_comment.md`
- `benchmark_summary.md`

## 1:45 - 2:00 Close

"Sentinel Release Guard is not a chatbot. It is a control layer for AI-speed software teams: detect risk, generate tests, preserve evidence, and keep humans in charge before production."
