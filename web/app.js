const pricingTiers = [
  {
    name: "Starter",
    monthly_price_inr: 999,
    included_release_scans: 50,
    target_customer: "Indie builders and student startup teams",
    overage_inr_per_scan: 35,
  },
  {
    name: "Growth",
    monthly_price_inr: 4999,
    included_release_scans: 500,
    target_customer: "SaaS teams shipping weekly with AI coding tools",
    overage_inr_per_scan: 18,
  },
  {
    name: "Enterprise",
    monthly_price_inr: 24999,
    included_release_scans: 5000,
    target_customer: "Regulated engineering orgs with audit needs",
    overage_inr_per_scan: 8,
  },
];

const patterns = {
  authentication: {
    weight: 22,
    tokens: ["auth", "authentication", "login", "session", "jwt", "oauth", "password", "role", "permission", "client-side role"],
    impact: "Unauthorized access or privilege escalation can reach production users.",
    gates: [
      "Verify unauthenticated users cannot call protected release paths.",
      "Verify lower-privilege users cannot execute owner or finance-only actions.",
    ],
  },
  payment: {
    weight: 28,
    tokens: ["payment", "checkout", "invoice", "billing", "refund", "price", "subscription", "charge"],
    impact: "Payment regressions can create fraud, duplicate refunds, or revenue loss.",
    gates: [
      "Verify refund approvals require server-side policy and the correct approver.",
      "Verify retry and failure paths cannot duplicate invoice or refund records.",
    ],
  },
  data_exposure: {
    weight: 24,
    tokens: ["pii", "email", "customer", "export", "download", "csv", "audit payload", "private"],
    impact: "Sensitive data exposure can create privacy and compliance incidents.",
    gates: [
      "Verify audit payloads contain only fields allowed for the user's role.",
      "Verify object references cannot expose another tenant's customer data.",
    ],
  },
  ai_agent: {
    weight: 24,
    tokens: ["ai agent", "agent", "llm", "model", "prompt", "tool", "autonomous", "recommend"],
    impact: "AI agent changes can create unsafe tool calls or unreviewed decisions.",
    gates: [
      "Verify prompt injection cannot trigger an irreversible tool call.",
      "Verify the agent requires human approval before release-blocking or financial actions.",
    ],
  },
  external_integration: {
    weight: 16,
    tokens: ["webhook", "integration", "sync", "erp", "api", "vendor", "unsigned", "retry"],
    impact: "Integration failures can silently corrupt downstream systems.",
    gates: [
      "Verify webhook signatures and trusted-source checks are enforced.",
      "Verify replay, timeout, and partial-failure handling remains idempotent.",
    ],
  },
  state_management: {
    weight: 10,
    tokens: ["status", "state", "approval", "queue", "workflow", "review"],
    impact: "State-machine bugs can approve, skip, or duplicate business workflows.",
    gates: [
      "Verify state transitions cannot skip required review steps.",
      "Verify duplicate approval events are ignored after the first accepted decision.",
    ],
  },
};

const sampleChange = {
  title: "AI-assisted refund approval and ERP sync",
  summary: "Adds an AI agent that recommends refund approvals, updates billing roles, stores customer refund notes, and syncs invoice status to the ERP webhook.",
  changed_files: [
    "services/ai_refund_agent.py",
    "services/payments/refunds.py",
    "services/auth/roles.py",
    "integrations/erp_webhook.py",
    "web/review_dashboard.html",
  ],
  diff_excerpt:
    "agent can call approve_refund tool; role check moved client-side; webhook retry accepts unsigned events; customer email included in audit payload",
  business_context:
    "Finance operations team wants AI-speed refund handling without exposing customer data or approving fraudulent refunds.",
  release_deadline: "2026-06-18",
  owner: "Finance release owner",
};

let latestResult = null;

function normalizeChange(input) {
  if (typeof input === "object" && input !== null) {
    return {
      title: String(input.title || "Untitled change"),
      summary: String(input.summary || ""),
      changed_files: Array.isArray(input.changed_files) ? input.changed_files.map(String) : [],
      diff_excerpt: String(input.diff_excerpt || ""),
      business_context: String(input.business_context || ""),
      release_deadline: String(input.release_deadline || ""),
      owner: String(input.owner || "Release owner"),
    };
  }
  return {
    title: "Pasted release change",
    summary: String(input),
    changed_files: [],
    diff_excerpt: String(input),
    business_context: "Manual text input",
    release_deadline: "",
    owner: "Release owner",
  };
}

function haystack(change) {
  return [
    change.title,
    change.summary,
    change.diff_excerpt,
    change.business_context,
    change.changed_files.join(" "),
  ]
    .join(" ")
    .toLowerCase();
}

function isNegated(text, token) {
  const safe = token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const expressions = [
    new RegExp(`\\bno\\b(?:\\s+[a-z0-9_-]+,?){0,4}\\s+(?:or\\s+)?${safe}\\b`, "i"),
    new RegExp(`\\bwithout\\b(?:\\s+[a-z0-9_-]+,?){0,4}\\s+(?:or\\s+)?${safe}\\b`, "i"),
    new RegExp(`\\bnot\\b(?:\\s+[a-z0-9_-]+,?){0,4}\\s+(?:or\\s+)?${safe}\\b`, "i"),
  ];
  return expressions.some((expression) => expression.test(text));
}

function severity(score) {
  if (score >= 80) return "critical";
  if (score >= 60) return "high";
  if (score >= 38) return "medium";
  return "low";
}

function detectSignals(change) {
  const text = haystack(change);
  const signals = [];
  Object.entries(patterns).forEach(([category, spec]) => {
    const evidence = [];
    spec.tokens.forEach((token) => {
      if (text.includes(token) && !isNegated(text, token)) {
        evidence.push(`keyword:${token}`);
      }
    });
    change.changed_files.forEach((file) => {
      const low = file.toLowerCase();
      if (spec.tokens.some((token) => low.includes(token))) {
        evidence.push(`file:${file}`);
      }
    });
    if (evidence.length > 0) {
      const score = spec.weight + Math.min(16, evidence.length * 3);
      signals.push({
        category,
        severity: severity(score),
        score,
        evidence: evidence.slice(0, 8),
        impact: spec.impact,
      });
    }
  });
  return signals.sort((a, b) => b.score - a.score);
}

function recommendPlan(monthlyUsage) {
  return pricingTiers.find((tier) => monthlyUsage <= tier.included_release_scans) || pricingTiers[pricingTiers.length - 1];
}

function analyze(changeInput, tenant, monthlyUsage) {
  const change = normalizeChange(changeInput);
  const signals = detectSignals(change);
  const text = haystack(change);
  let score = signals.reduce((sum, signal) => sum + signal.score, 0);
  if (change.changed_files.length >= 5) score += 8;
  if (text.includes("client-side") || text.includes("unsigned")) score += 10;
  score = Math.max(0, Math.min(96, score));
  const decision =
    score >= 70
      ? "BLOCK_RELEASE_PENDING_HUMAN_REVIEW"
      : score >= 35
        ? "CONDITIONAL_RELEASE_WITH_TARGETED_GATES"
        : "APPROVE_RELEASE";
  const gates = [];
  signals.forEach((signal) => {
    patterns[signal.category].gates.forEach((title) => {
      gates.push({
        id: `SRG-${String(gates.length + 1).padStart(3, "0")}`,
        title,
        category: signal.category,
        priority: signal.score >= 30 ? "P0" : "P1",
        owner: change.owner,
      });
    });
  });
  if (gates.length === 0) {
    gates.push({
      id: "SRG-001",
      title: "Run baseline smoke suite and capture release note evidence.",
      category: "baseline",
      priority: "P2",
      owner: change.owner,
    });
  }
  const plan = recommendPlan(monthlyUsage);
  const apiUnits = 1 + signals.length * 3 + Math.max(1, Math.floor(gates.length / 2));
  const overage = Math.max(0, monthlyUsage - plan.included_release_scans);
  const estimatedBill = plan.monthly_price_inr + overage * plan.overage_inr_per_scan;
  const generatedAt = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  return {
    tenant,
    generated_at: generatedAt,
    change,
    release_risk_score: score,
    release_decision: decision,
    human_approval_required: decision === "BLOCK_RELEASE_PENDING_HUMAN_REVIEW",
    risk_signals: signals,
    release_gates: gates,
    recommended_plan: plan,
    metering: {
      api_units: apiUnits,
      monthly_release_scans: monthlyUsage,
      estimated_monthly_bill_inr: estimatedBill,
    },
    audit_events: [
      { timestamp: generatedAt, actor: change.owner, event: "change_ingested", details: change.title },
      { timestamp: generatedAt, actor: "sentinel-agent", event: "risk_score_calculated", details: `risk_score=${score}` },
      { timestamp: generatedAt, actor: "sentinel-agent", event: "release_decision_recorded", details: decision },
      {
        timestamp: generatedAt,
        actor: score >= 70 ? change.owner : "sentinel-agent",
        event: "approval_gate_selected",
        details: score >= 70 ? "human review required" : "automation evidence sufficient",
      },
    ],
  };
}

function formatCategory(category) {
  return category.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function decisionClass(decision) {
  if (decision.startsWith("BLOCK")) return "block";
  if (decision.startsWith("CONDITIONAL")) return "conditional";
  if (decision.startsWith("APPROVE")) return "approve";
  return "neutral";
}

function renderResult(result) {
  latestResult = result;
  const score = result.release_risk_score;
  const decision = result.release_decision.replaceAll("_", " ");
  const className = decisionClass(result.release_decision);
  const ring = document.querySelector("#scoreRing");
  const color = className === "block" ? "#b42318" : className === "conditional" ? "#b7791f" : "#237a3a";
  ring.style.background = `conic-gradient(${color} ${score * 3.6}deg, #e8e4d7 0deg)`;

  document.querySelector("#decisionText").textContent = decision;
  document.querySelector("#decisionBadge").textContent = className === "block" ? "Blocked" : className === "conditional" ? "Conditional" : "Approved";
  document.querySelector("#decisionBadge").className = `decision-badge ${className}`;
  document.querySelector("#scoreValue").textContent = score;
  document.querySelector("#scoreCaption").textContent =
    score >= 70
      ? "High-risk release blocked until human review accepts the evidence."
      : score >= 35
        ? "Targeted gates required before release approval."
        : "Low-risk release can proceed with baseline evidence.";
  document.querySelector("#apiUnits").textContent = result.metering.api_units;
  document.querySelector("#humanGate").textContent = result.human_approval_required ? "Required" : "Not required";
  document.querySelector("#planName").textContent = result.recommended_plan.name;
  document.querySelector("#monthlyBill").textContent = `INR ${result.metering.estimated_monthly_bill_inr.toLocaleString("en-IN")} / month`;
  document.querySelector("#navDecision").textContent = document.querySelector("#decisionBadge").textContent;
  document.querySelector("#navScore").textContent = `Risk score ${score}/100`;

  renderRiskBars(result);
  renderGates(result);
  renderAudit(result);
  renderPricing(result);
  if (window.lucide) window.lucide.createIcons();
}

function renderRiskBars(result) {
  const container = document.querySelector("#riskBars");
  if (result.risk_signals.length === 0) {
    container.innerHTML = `<p>No material risk categories detected.</p>`;
    return;
  }
  container.innerHTML = result.risk_signals
    .map(
      (signal) => `
        <div class="risk-row">
          <span>${formatCategory(signal.category)}</span>
          <div class="bar-track" aria-hidden="true"><div class="bar-fill ${signal.severity}" style="width:${Math.min(100, signal.score)}%"></div></div>
          <strong>${signal.score}</strong>
        </div>
      `,
    )
    .join("");
}

function renderGates(result) {
  const container = document.querySelector("#gateList");
  document.querySelector("#gateCount").textContent = `${result.release_gates.length} gates`;
  container.innerHTML = result.release_gates
    .map(
      (gate) => `
        <article class="gate-item">
          <span class="gate-id">${gate.id}</span>
          <div>
            <div class="gate-title">${gate.title}</div>
            <div class="gate-meta">${formatCategory(gate.category)} - Owner: ${gate.owner}</div>
          </div>
          <span class="priority">${gate.priority}</span>
        </article>
      `,
    )
    .join("");
}

function renderAudit(result) {
  const container = document.querySelector("#auditList");
  container.innerHTML = result.audit_events
    .map(
      (event, index) => `
        <li>
          <span class="audit-index">${index + 1}</span>
          <div class="audit-card">
            <strong>${event.event.replaceAll("_", " ")}</strong>
            <span>${event.actor} - ${event.details}</span>
          </div>
        </li>
      `,
    )
    .join("");
}

function renderPricing(result) {
  const grid = document.querySelector("#pricingGrid");
  grid.innerHTML = pricingTiers
    .map(
      (tier) => `
        <article class="price-card ${tier.name === result.recommended_plan.name ? "active" : ""}">
          <h3>${tier.name}</h3>
          <div class="price">INR ${tier.monthly_price_inr.toLocaleString("en-IN")}</div>
          <p>${tier.included_release_scans.toLocaleString("en-IN")} scans included. Overage: INR ${tier.overage_inr_per_scan}/scan.</p>
          <p>${tier.target_customer}</p>
        </article>
      `,
    )
    .join("");
}

function readInput() {
  const raw = document.querySelector("#changeInput").value.trim();
  if (!raw) return sampleChange;
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

function runScan() {
  const tenant = document.querySelector("#tenantInput").value.trim() || "demo-tenant";
  const monthlyUsage = Math.max(1, Number(document.querySelector("#usageInput").value || 1));
  renderResult(analyze(readInput(), tenant, monthlyUsage));
}

function copyBrief() {
  if (!latestResult) runScan();
  const result = latestResult;
  const risks = result.risk_signals.map((signal) => `${formatCategory(signal.category)}: ${signal.impact}`).join("\n");
  const brief = `Sentinel SaaS executive brief

Decision: ${result.release_decision}
Risk score: ${result.release_risk_score}/100
Tenant: ${result.tenant}
Recommended plan: ${result.recommended_plan.name}
Estimated monthly bill: INR ${result.metering.estimated_monthly_bill_inr}

Material risks:
${risks || "No material security risk detected."}

Release gates: ${result.release_gates.length}
Human approval required: ${result.human_approval_required ? "yes" : "no"}`;

  navigator.clipboard?.writeText(brief);
  document.querySelector("#copyBriefButton span").textContent = "Copied";
  setTimeout(() => {
    document.querySelector("#copyBriefButton span").textContent = "Copy brief";
  }, 1500);
}

function boot() {
  document.querySelector("#changeInput").value = JSON.stringify(sampleChange, null, 2);
  document.querySelector("#analyzeButton").addEventListener("click", runScan);
  document.querySelector("#analyzeTopButton").addEventListener("click", runScan);
  document.querySelector("#copyBriefButton").addEventListener("click", copyBrief);
  document.querySelector("#resetButton").addEventListener("click", () => {
    document.querySelector("#changeInput").value = JSON.stringify(sampleChange, null, 2);
    document.querySelector("#tenantInput").value = "acme-finance";
    document.querySelector("#usageInput").value = "420";
    runScan();
  });
  renderPricing({
    recommended_plan: pricingTiers[0],
    metering: { estimated_monthly_bill_inr: pricingTiers[0].monthly_price_inr },
  });
  runScan();
  if (window.lucide) window.lucide.createIcons();
}

document.addEventListener("DOMContentLoaded", boot);
