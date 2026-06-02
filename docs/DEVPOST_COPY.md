# Devpost Copy

## Project Name

Sentinel SaaS

## Elevator Pitch

AI release-risk SaaS that scans AI-generated changes, generates security regression gates, preserves audit evidence, and meters usage before unsafe releases ship.

## About The Project

AI coding tools are making software teams ship faster, but release governance has not caught up. A team can generate a payment, authentication, webhook, or AI-agent feature in minutes, then spend hours trying to understand what can safely go to production.

Sentinel SaaS solves that gap. A user pastes a PR-style change, product change, or JSON payload. The agent detects risk across payments, authentication, customer data, AI-agent tools, webhooks, and workflow state. It calculates a transparent release risk score, generates security-aware regression gates, records a tenant audit trail, and recommends a SaaS pricing tier based on usage.

The demo scenario reviews an AI-assisted refund approval workflow. Sentinel detects payment, auth, AI-agent, webhook, and customer-data risks, scores the release at 96/100, blocks it for human review, and generates concrete release gates before production.

This is built as a SaaS product, not a one-off script. The submission includes a polished static dashboard, a tested Python agent engine, a local API, JSON and Markdown evidence artifacts, a pricing model, and a video-ready workflow.

## Built With

Python, HTML, CSS, JavaScript, JSON, Markdown, unittest, local HTTP API, GitHub, Netlify/Vercel-ready static deployment, AI agent design, cybersecurity risk scoring, SaaS monetization design

## Try It Out Links

Use these once GitHub and hosted demo are live:

- Hosted demo: `PASTE_HOSTED_DEMO_URL`
- GitHub repository: `PASTE_GITHUB_REPOSITORY_URL`
- Demo video: `PASTE_VIDEO_URL`

## What Makes It Different

- It does not behave like a generic chatbot.
- It produces a release decision, not just advice.
- It creates evidence a team can use in CI/CD and audits.
- It has a pricing and usage-metering model built into the product.
- It targets a current enterprise pain point: AI-generated code is accelerating faster than release safety.

## Contribution

I built Sentinel SaaS end to end: the Python agent engine, risk scoring logic, generated release gates, audit trail, SaaS metering model, static web dashboard, test suite, demo evidence, documentation, and submission strategy.
