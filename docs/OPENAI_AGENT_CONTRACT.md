# Optional OpenAI Agent Contract

Sentinel SaaS currently runs without an API key so judges can test it immediately. The product is designed so an OpenAI-backed agent can be added without changing the SaaS contract.

## Agent Goal

Review a release change, identify production risk, generate release gates, and return a structured decision that can be audited.

## Input Shape

```json
{
  "tenant": "acme-finance",
  "monthly_usage": 420,
  "title": "AI-assisted refund approval and ERP sync",
  "summary": "Adds an AI agent that recommends refund approvals...",
  "changed_files": ["services/ai_refund_agent.py"],
  "diff_excerpt": "agent can call approve_refund tool",
  "business_context": "Finance operations team wants AI-speed refund handling",
  "owner": "Finance release owner"
}
```

## Required Output Shape

```json
{
  "release_decision": "BLOCK_RELEASE_PENDING_HUMAN_REVIEW",
  "release_risk_score": 96,
  "risk_signals": [],
  "release_gates": [],
  "audit_events": [],
  "metering": {}
}
```

## Tool Schema

An OpenAI adapter would expose deterministic tools for auditability:

- `detect_risk_signals(change)`
- `score_release(signals, change)`
- `build_release_gates(signals, owner)`
- `build_audit_events(tenant, change, decision, score)`
- `build_metering(signals, gates, monthly_usage)`

The LLM layer should explain risk and reason about ambiguous context. It should not bypass deterministic gates or approve high-risk releases by itself.

## Approval Gate

For any score >= 70, the agent must return:

```text
BLOCK_RELEASE_PENDING_HUMAN_REVIEW
```

The approval decision belongs to a human release owner, not the model.
