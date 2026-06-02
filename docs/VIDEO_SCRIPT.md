# Demo Video Script

## 0:00-0:20 - Opening

"This is Hidden Reviews AI, built for the name.com Domain Roulette challenge using the domain hidden.reviews. The product finds customer reviews and complaints that are hidden across Reddit, GitHub issues, support tickets, sales notes, app reviews, and communities."

Show the dashboard and domain name.

## 0:20-0:55 - Feedback Bundle

"The demo product is NimbusLedger. The feedback looks fragmented: a Reddit complaint about surprise billing, a GitHub issue about webhook duplication, an app review about onboarding, a sales note mentioning a competitor, and support feedback asking for a weekly digest."

Show the JSON evidence input.

## 0:55-1:25 - Run Scan

Click **Reveal hidden reviews**.

"The agent scores this as 97 out of 100 hidden signal. The top risk is pricing trust. The key insight is that customers are not just complaining about price; they are describing surprise overages as a trust problem, and that connects directly to churn and lost deals."

Show signal score and source mix.

## 1:25-2:10 - Pattern Ranking

"The agent clusters evidence into pricing trust, integration reliability, onboarding confusion, executive visibility, and competitor pressure. Each cluster keeps a representative quote so the founder can see the evidence, not just a vague AI summary."

Scroll to patterns.

## 2:10-2:50 - Founder Action Plan

"The output is an action plan. It recommends pricing-alert guardrails, replay-safe webhook diagnostics, visible failed-import evidence, a weekly hidden-review digest, and competitor-loss review boards."

Scroll to actions.

## 2:50-3:25 - Code Proof

"The repo includes a tested Python agent engine, a local API, JSON analysis, Markdown founder brief, CSV evidence exports, and a static dashboard. It runs without paid API keys so judges can reproduce it immediately."

Show terminal:

```powershell
python hidden_reviews_agent.py demo
python -m unittest discover -s tests
```

## 3:25-3:45 - Closing

"The domain hidden.reviews is not just branding. It is the product promise: find the reviews customers never put in one place."
