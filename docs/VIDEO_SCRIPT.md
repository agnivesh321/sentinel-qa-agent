# 2-5 Minute Demo Script

## 0:00-0:15 - Product Opening

"Sentinel SaaS is an AI release-risk platform for teams shipping code with AI coding agents. AI makes teams faster, but it also makes unsafe releases easier to miss. Sentinel scans a change, generates security gates, preserves audit evidence, and meters usage like a real SaaS product."

Show the dashboard title and side navigation.

## 0:15-0:55 - Problem And Input

"Here is a release change for an AI-assisted refund approval workflow. It touches an AI agent, refund logic, authentication roles, ERP webhooks, and customer audit data. This is exactly the kind of change teams do not want to ship blindly."

Show the JSON payload in the intake panel.

## 0:55-1:30 - Run The Scan

Click **Analyze release risk**.

"Sentinel scores the release at 96 out of 100 and blocks it pending human review. The decision is not hidden behind vague AI text. The dashboard shows why: payment risk, AI-agent tool risk, authentication risk, customer-data exposure, webhook risk, and workflow state risk."

Show the risk ring and risk bars.

## 1:30-2:15 - Release Gates

"The product generates concrete release gates, not just a warning. It requires server-side refund approval checks, duplicate refund protection, prompt-injection protection, webhook signature validation, and role-based access checks."

Scroll to release gates.

## 2:15-2:55 - Governance And Monetization

"Sentinel also records a tenant audit trail: change ingested, risk score calculated, release decision recorded, and approval gate selected. This is important for enterprise governance. The same workflow is metered as a SaaS product, with Starter, Growth, and Enterprise pricing tiers."

Show audit trail and pricing cards.

## 2:55-3:30 - Code Proof

"This is not just the frontend. The repo includes a tested Python agent engine and a local API. The demo command exports JSON analysis, a Markdown executive brief, tenant audit log, and pricing model."

Show terminal:

```powershell
python galuxium_sentinel_saas\sentinel_saas_agent.py demo
python -m unittest discover -s galuxium_sentinel_saas\tests
```

## 3:30-4:00 - Closing

"The buyer is any SaaS team using AI to ship faster. Sentinel helps them keep shipping speed without losing release safety, governance, or customer trust."
