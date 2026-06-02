# OpenAI-Ready Agent Contract

The submitted demo runs deterministically so judges can test it without keys. The product is designed to accept an OpenAI agent layer later.

## Agent Goal

Given a mixed feedback bundle, identify hidden customer pain, preserve evidence, cluster themes, rank risk, and generate founder actions.

## Input

```json
{
  "product": "NimbusLedger",
  "domain": "hidden.reviews",
  "customer_count": 1800,
  "sources": [
    {
      "source": "Reddit thread",
      "source_type": "public_shadow_channel",
      "author": "saas_ops_17",
      "text": "..."
    }
  ]
}
```

## Output

```json
{
  "domain": "hidden.reviews",
  "hidden_signal_score": 97,
  "domain_fit_score": 100,
  "top_cluster": {},
  "clusters": [],
  "evidence_events": [],
  "action_plan": [],
  "recommended_tier": {}
}
```

## Tool Boundary

An OpenAI agent should use deterministic tools for:

- evidence extraction
- source weighting
- clustering
- subscription recommendation
- artifact export

The model layer should improve semantic nuance and summarization. It should not erase evidence, invent sources, or alter source text.

## Guardrail

Every cluster must preserve at least one representative quote from the original feedback. Founder actions must link back to evidence categories.
