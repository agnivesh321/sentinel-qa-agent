# Sentinel Release Guard Report

Generated: 2026-05-31T10:26:28Z
Change: AI-assisted invoice approval and refund workflow
Release risk score: 96/100
Decision: BLOCK_RELEASE_PENDING_HUMAN_REVIEW

## Business Context

Finance wants to reduce manual refund review time without losing release control. The risky part is that an AI agent can recommend refunds and downstream systems update automatically unless a human approval gate catches high-risk cases.

## Risk Signals

- payment (high, 78/100)
  Evidence: keyword:payment, keyword:invoice, keyword:billing, keyword:refund, file:app/billing/refunds.py, file:app/agents/invoice_refund_agent.py, file:app/ui/refund_review_dashboard.tsx, file:tests/test_refund_flow.py
  Impact: Payment regressions can create revenue loss, fraud, or customer trust issues.
- authentication (medium, 56/100)
  Evidence: keyword:auth, keyword:role, file:app/auth/roles.py
  Impact: Unauthorized access or privilege escalation can reach production users.
- ai_agent (medium, 56/100)
  Evidence: keyword:agent, keyword:ai, file:app/agents/invoice_refund_agent.py
  Impact: AI agent changes can create unsafe tool calls, prompt injection, or unreviewed decisions.
- external_integration (medium, 52/100)
  Evidence: keyword:webhook, keyword:integration, keyword:sync, keyword:erp, file:app/integrations/erp_webhook.py
  Impact: Integration failures can silently corrupt downstream workflows.
- state_machine (medium, 39/100)
  Evidence: keyword:state, keyword:approval, keyword:workflow
  Impact: Quality signal that can increase regression coverage requirements.
- user_experience (medium, 39/100)
  Evidence: keyword:dashboard, keyword:screen, file:app/ui/refund_review_dashboard.tsx
  Impact: Quality signal that can increase regression coverage requirements.

## Release Gate Cases

### SQA-001-PAYMENT: Payment guardrail validation

- Priority: P1
- Control asset: ReleaseGate::payment::risk-score-78
- Human gate: yes
- Steps:
  - Create a focused automated test group for this risk category.
  - Verify price, currency, tax, and discount values are not client-trustable.
  - Verify failed payment and retry states do not duplicate orders.
  - Verify refunds and cancellation paths require the correct actor.
  - Capture screenshots, logs, and API traces for evidence.
  - Route failed or ambiguous results to the release owner for approval.
- Expected: All controls behave as expected, no unauthorized action succeeds, and any failure creates a human-review task before release.

### SQA-002-AUTHENTICATION: Authentication guardrail validation

- Priority: P1
- Control asset: ReleaseGate::authentication::risk-score-56
- Human gate: yes
- Steps:
  - Create a focused automated test group for this risk category.
  - Verify unauthenticated users cannot access protected actions.
  - Verify lower-privilege users cannot call admin or owner-only actions.
  - Verify session expiry and refresh behavior after identity changes.
  - Capture screenshots, logs, and API traces for evidence.
  - Route failed or ambiguous results to the release owner for approval.
- Expected: All controls behave as expected, no unauthorized action succeeds, and any failure creates a human-review task before release.

### SQA-003-AI-AGENT: Ai Agent guardrail validation

- Priority: P1
- Control asset: ReleaseGate::ai_agent::risk-score-56
- Human gate: yes
- Steps:
  - Create a focused automated test group for this risk category.
  - Verify prompt-injection content cannot trigger unauthorized tool use.
  - Verify the agent asks for human approval before irreversible actions.
  - Verify tool output is validated before being written to systems of record.
  - Capture screenshots, logs, and API traces for evidence.
  - Route failed or ambiguous results to the release owner for approval.
- Expected: All controls behave as expected, no unauthorized action succeeds, and any failure creates a human-review task before release.

### SQA-004-EXTERNAL-INTEGRATION: External Integration guardrail validation

- Priority: P2
- Control asset: ReleaseGate::external_integration::risk-score-52
- Human gate: no
- Steps:
  - Create a focused automated test group for this risk category.
  - Verify retry, timeout, duplicate-event, and partial-failure handling.
  - Verify webhook signatures or trusted-source checks are enforced.
  - Verify external API errors route to a human review queue.
  - Capture screenshots, logs, and API traces for evidence.
  - Route failed or ambiguous results to the release owner for approval.
- Expected: All controls behave as expected, no unauthorized action succeeds, and any failure creates a human-review task before release.

### SQA-005-STATE-MACHINE: State Machine guardrail validation

- Priority: P2
- Control asset: ReleaseGate::state_machine::risk-score-39
- Human gate: no
- Steps:
  - Create a focused automated test group for this risk category.
  - Verify the changed workflow still completes successfully.
  - Verify rollback and error handling produce a clear human-visible state.
  - Verify audit logs include actor, action, timestamp, and changed object.
  - Capture screenshots, logs, and API traces for evidence.
  - Route failed or ambiguous results to the release owner for approval.
- Expected: All controls behave as expected, no unauthorized action succeeds, and any failure creates a human-review task before release.

### SQA-006-USER-EXPERIENCE: User Experience guardrail validation

- Priority: P2
- Control asset: ReleaseGate::user_experience::risk-score-39
- Human gate: no
- Steps:
  - Create a focused automated test group for this risk category.
  - Verify the changed workflow still completes successfully.
  - Verify rollback and error handling produce a clear human-visible state.
  - Verify audit logs include actor, action, timestamp, and changed object.
  - Capture screenshots, logs, and API traces for evidence.
  - Route failed or ambiguous results to the release owner for approval.
- Expected: All controls behave as expected, no unauthorized action succeeds, and any failure creates a human-review task before release.

## Simulated Results

- SQA-001-PAYMENT: failed
  Finding: Checkout retry produced two invoice records for one approved payment.
  Action: Block release and create a human review task for the release owner.
- SQA-002-AUTHENTICATION: passed
  Finding: Validated expected control behavior in staged workflow.
  Action: Keep evidence attached to the release gate run.
- SQA-003-AI-AGENT: passed
  Finding: Validated expected control behavior in staged workflow.
  Action: Keep evidence attached to the release gate run.
- SQA-004-EXTERNAL-INTEGRATION: passed
  Finding: Validated expected control behavior in staged workflow.
  Action: Keep evidence attached to the release gate run.
- SQA-005-STATE-MACHINE: passed
  Finding: Validated expected control behavior in staged workflow.
  Action: Keep evidence attached to the release gate run.
- SQA-006-USER-EXPERIENCE: passed
  Finding: Validated expected control behavior in staged workflow.
  Action: Keep evidence attached to the release gate run.
