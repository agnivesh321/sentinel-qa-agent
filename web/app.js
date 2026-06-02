const subscriptionTiers = [
  {
    name: "Scout",
    monthly_price_usd: 29,
    included_feedback_items: 250,
    target_customer: "Solo founders and student startup teams",
    overage_usd_per_100_items: 8,
  },
  {
    name: "Growth",
    monthly_price_usd: 149,
    included_feedback_items: 7500,
    target_customer: "SaaS teams with public communities and support queues",
    overage_usd_per_100_items: 4,
  },
  {
    name: "Command Center",
    monthly_price_usd: 499,
    included_feedback_items: 30000,
    target_customer: "Product orgs tracking many products, markets, or regions",
    overage_usd_per_100_items: 2,
  },
];

const clusterRules = {
  pricing_trust: {
    label: "Pricing trust risk",
    weight: 34,
    tokens: ["pricing", "price", "bill", "billing", "overage", "surprise", "churn", "trust", "spend", "guardrail"],
    opportunity: "Publish proactive pricing guardrails and overage alerts before customers feel trapped.",
    why_it_matters: "Pricing distrust converts quiet complaints into churn and lost sales.",
  },
  integration_reliability: {
    label: "Integration reliability",
    weight: 28,
    tokens: ["webhook", "integration", "sync", "erp", "idempotent", "timeout", "duplicate", "invoice", "month-end"],
    opportunity: "Ship idempotency controls, replay-safe webhooks, and customer-visible sync health.",
    why_it_matters: "Integration bugs damage operational trust at the exact moment teams depend on the product.",
  },
  onboarding_confusion: {
    label: "Onboarding confusion",
    weight: 24,
    tokens: ["onboarding", "setup", "docs", "documentation", "sandbox", "api key", "import", "wizard", "validation"],
    opportunity: "Replace scattered setup instructions with a guided onboarding checklist and failed-import evidence.",
    why_it_matters: "Confusing setup hides adoption friction until users abandon the product.",
  },
  executive_visibility: {
    label: "Executive visibility gap",
    weight: 18,
    tokens: ["digest", "executive", "pattern", "hidden", "leader", "weekly", "too late", "reviews"],
    opportunity: "Create a weekly review digest that translates scattered complaints into product decisions.",
    why_it_matters: "Teams lose the pattern when complaints are split across communities, support, and sales notes.",
  },
  competitor_pressure: {
    label: "Competitor pressure",
    weight: 16,
    tokens: ["competitor", "won", "lost", "ledgerfox", "deal", "prospect", "alternative"],
    opportunity: "Turn competitor wins into a counter-positioning roadmap with proof-backed gaps.",
    why_it_matters: "Competitor mentions are buying signals disguised as casual feedback.",
  },
  customer_love: {
    label: "Customer love",
    weight: -12,
    tokens: ["love", "useful", "easy", "clear", "great", "happy", "no major bugs"],
    opportunity: "Preserve what customers already value while watching for new hidden complaints.",
    why_it_matters: "Positive feedback is useful, but it should not bury emerging product risk.",
  },
};

const sourceMultipliers = {
  public_shadow_channel: 1.35,
  private_sales_note: 1.25,
  private_support: 1.2,
  public_review: 1.0,
};

const riskContextTokens = [
  "broke",
  "broken",
  "called it",
  "churn",
  "complained",
  "confusing",
  "could not",
  "duplicate",
  "duplicated",
  "edge case",
  "failed",
  "fails",
  "hidden",
  "lost",
  "missing",
  "overage",
  "problem",
  "silent",
  "surprise",
  "timeout",
  "too late",
  "trust problem",
];

const sampleBundle = {
  product: "NimbusLedger",
  domain: "hidden.reviews",
  sources: [
    {
      source: "Reddit thread",
      source_type: "public_shadow_channel",
      author: "saas_ops_17",
      text:
        "NimbusLedger looked cheap until the surprise overage bill. Pricing is technically documented but hidden behind three clicks. We churned after finance called it a trust problem.",
    },
    {
      source: "GitHub issue",
      source_type: "public_shadow_channel",
      author: "integration_builder",
      text:
        "Webhook retries are not idempotent. Our ERP sync duplicated invoice status updates twice during a timeout. Support said it is an edge case, but it broke month-end close.",
    },
    {
      source: "App review",
      source_type: "public_review",
      author: "founder_amy",
      text:
        "The dashboard is useful after setup, but onboarding is confusing. I could not find the sandbox API key, the docs sent me in circles, and the first import failed silently.",
    },
    {
      source: "Sales call note",
      source_type: "private_sales_note",
      author: "account_exec",
      text:
        "Prospect likes the product, but they asked if pricing alerts exist before overages. Competitor LedgerFox won their previous deal because it had spend guardrails and clearer review evidence.",
    },
    {
      source: "Support email",
      source_type: "private_support",
      author: "ops_manager",
      text:
        "We need a weekly executive digest of complaints. Right now the worst reviews are hidden in support, Reddit, GitHub issues, and sales notes, so product leaders see the pattern too late.",
    },
    {
      source: "Community Discord",
      source_type: "public_shadow_channel",
      author: "migrating_admin",
      text:
        "The import wizard says success even when three records fail validation. We only noticed after customers complained about missing invoice rows.",
    },
  ],
};

let latestResult = null;

function normalizeBundle(input) {
  if (typeof input === "object" && input !== null) {
    return {
      product: String(input.product || "Unknown product"),
      domain: String(input.domain || "hidden.reviews"),
      sources: Array.isArray(input.sources)
        ? input.sources
            .filter((item) => item && item.text)
            .map((item) => ({
              source: String(item.source || "Unknown source"),
              source_type: String(item.source_type || "public_review"),
              author: String(item.author || "anonymous"),
              text: String(item.text || ""),
            }))
        : [],
    };
  }
  return {
    product: "Pasted product",
    domain: "hidden.reviews",
    sources: [{ source: "Manual paste", source_type: "public_review", author: "unknown", text: String(input) }],
  };
}

function sentenceFragments(text) {
  return text
    .replace(/\s+/g, " ")
    .split(/(?<=[.!?])\s+/)
    .map((part) => part.trim())
    .filter(Boolean);
}

function matchedTokens(text, tokens) {
  const lower = text.toLowerCase();
  return tokens.filter((token) => lower.includes(token));
}

function hasRiskContext(text) {
  const lower = text.toLowerCase();
  if (lower.includes("no major bugs") && !["failed", "broken", "churn", "surprise", "overage"].some((token) => lower.includes(token))) {
    return false;
  }
  return riskContextTokens.some((token) => lower.includes(token));
}

function severity(score) {
  if (score >= 80) return "critical";
  if (score >= 55) return "high";
  if (score >= 30) return "medium";
  if (score >= 10) return "low";
  return "positive";
}

function extractEvidence(bundle) {
  const events = [];
  bundle.sources.forEach((source) => {
    const multiplier = sourceMultipliers[source.source_type] || 1;
    const fragments = sentenceFragments(source.text);
    Object.entries(clusterRules).forEach(([category, rule]) => {
      const matches = matchedTokens(source.text, rule.tokens);
      if (!matches.length) return;
      if (category !== "customer_love" && !hasRiskContext(source.text)) return;
      const quote = fragments.find((fragment) => matchedTokens(fragment, rule.tokens).length) || source.text;
      const base = Math.abs(rule.weight) + matches.length * 4;
      const hiddenWeight = Math.round(base * multiplier) * (rule.weight > 0 ? 1 : -1);
      events.push({
        source: source.source,
        source_type: source.source_type,
        author: source.author,
        category,
        severity: severity(Math.abs(hiddenWeight)),
        evidence: quote.slice(0, 240),
        hidden_weight: hiddenWeight,
      });
    });
  });
  if (!events.length && bundle.sources.length) {
    const source = bundle.sources[0];
    events.push({
      source: source.source,
      source_type: source.source_type,
      author: source.author,
      category: "customer_love",
      severity: "positive",
      evidence: source.text.slice(0, 240),
      hidden_weight: -10,
    });
  }
  return events;
}

function buildClusters(events) {
  const grouped = {};
  events.forEach((event) => {
    grouped[event.category] ||= [];
    grouped[event.category].push(event);
  });
  return Object.entries(grouped)
    .map(([category, categoryEvents]) => {
      const rule = clusterRules[category];
      let score = categoryEvents.reduce((sum, event) => sum + event.hidden_weight, 0);
      score = category === "customer_love" ? Math.max(1, Math.floor(Math.abs(score) / 2)) : Math.max(1, score);
      return {
        category,
        label: rule.label,
        severity: severity(score),
        score: Math.min(100, score),
        source_count: new Set(categoryEvents.map((event) => event.source)).size,
        evidence_count: categoryEvents.length,
        why_it_matters: rule.why_it_matters,
        opportunity: rule.opportunity,
        representative_quotes: categoryEvents.slice(0, 3).map((event) => event.evidence),
      };
    })
    .sort((a, b) => b.score - a.score);
}

function recommendTier(customerCount) {
  const estimatedItems = Math.max(100, customerCount * 3);
  return subscriptionTiers.find((tier) => estimatedItems <= tier.included_feedback_items) || subscriptionTiers[subscriptionTiers.length - 1];
}

function buildActionPlan(clusters, product) {
  const actions = [];
  clusters
    .filter((cluster) => cluster.category !== "customer_love")
    .slice(0, 6)
    .forEach((cluster, index) => {
      const priority = index <= 1 ? "P0" : "P1";
      const actionMap = {
        pricing_trust: [
          "Launch pricing-alert guardrails and rewrite hidden overage language",
          "Reduce churn risk and rescue expansion conversations before finance escalates.",
        ],
        integration_reliability: [
          "Add replay-safe webhook diagnostics and duplicate invoice protection",
          "Protect operational trust for finance teams during month-end workflows.",
        ],
        onboarding_confusion: [
          "Ship guided onboarding with visible failed-import evidence",
          "Shorten time to value and stop silent setup failures from becoming public complaints.",
        ],
        executive_visibility: [
          "Send weekly hidden-review digest to product and founder stakeholders",
          "Expose cross-channel patterns before they become churn.",
        ],
        competitor_pressure: [
          "Create competitor-loss review board and counter-positioning copy",
          "Turn lost-deal language into roadmap and sales enablement.",
        ],
      };
      const fallback = [`Resolve ${cluster.label.toLowerCase()} for ${product}`, cluster.opportunity];
      const [title, expected_impact] = actionMap[cluster.category] || fallback;
      actions.push({
        priority,
        title,
        owner: index <= 2 ? "Product lead" : "Growth lead",
        expected_impact,
        evidence_categories: [cluster.category],
      });
    });
  if (actions.length < 6) {
    actions.push({
      priority: "P1",
      title: "Instrument public shadow-channel monitoring",
      owner: "Customer intelligence",
      expected_impact: "Keep Reddit, GitHub, community, and app-store pain visible in one review cockpit.",
      evidence_categories: ["executive_visibility"],
    });
    actions.push({
      priority: "P2",
      title: "Create a customer-proof changelog tied to review themes",
      owner: "Product marketing",
      expected_impact: "Show customers that hidden feedback becomes shipped improvements.",
      evidence_categories: ["pricing_trust", "onboarding_confusion"],
    });
  }
  return actions.slice(0, 7);
}

function analyzeBundle(input, customerCount) {
  const bundle = normalizeBundle(input);
  const events = extractEvidence(bundle);
  let clusters = buildClusters(events);
  if (!clusters.length) {
    clusters = [
      {
        category: "customer_love",
        label: "Customer love",
        severity: "positive",
        score: 1,
        source_count: 0,
        evidence_count: 0,
        why_it_matters: clusterRules.customer_love.why_it_matters,
        opportunity: clusterRules.customer_love.opportunity,
        representative_quotes: [],
      },
    ];
  }
  const negative = clusters.filter((cluster) => cluster.category !== "customer_love");
  const channelBonus = new Set(events.filter((event) => event.hidden_weight > 0).map((event) => event.source_type)).size * 6;
  const hiddenSignalScore = negative.length
    ? Math.max(0, Math.min(97, Math.round(negative.slice(0, 3).reduce((sum, cluster) => sum + cluster.score, 0) * 0.72 + channelBonus)))
    : Math.min(30, Math.max(...clusters.map((cluster) => cluster.score)));
  const hiddenSources = events.filter((event) => ["public_shadow_channel", "private_sales_note", "private_support"].includes(event.source_type)).length;
  const allText = bundle.sources.map((source) => source.text).join(" ").toLowerCase();
  const domainFitScore = Math.min(100, (bundle.domain === "hidden.reviews" ? 45 : 25) + Math.min(40, hiddenSources * 8) + (allText.includes("hidden") || allText.includes("reviews") ? 15 : 8));
  const tier = recommendTier(customerCount);
  return {
    product: bundle.product,
    domain: bundle.domain,
    generated_at: new Date().toISOString().replace(/\.\d{3}Z$/, "Z"),
    hidden_signal_score: hiddenSignalScore,
    domain_fit_score: domainFitScore,
    top_cluster: clusters[0],
    clusters,
    evidence_events: events,
    action_plan: buildActionPlan(clusters, bundle.product),
    recommended_tier: tier,
    founder_summary: {
      one_line: "hidden.reviews finds the reviews customers never put in one place.",
      domain_connection: "The domain is literal: hidden.reviews becomes the command center for buried customer truth.",
      buyer: "Founders, PMs, and customer success teams at SaaS companies with fragmented feedback channels.",
      why_now: "AI lets teams scrape, cluster, and operationalize feedback faster than manual review meetings.",
    },
  };
}

function formatCategory(value) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function badgeClass(score) {
  if (score >= 80) return "critical";
  if (score >= 55) return "high";
  if (score >= 35) return "medium";
  return "low";
}

function renderResult(result) {
  latestResult = result;
  const score = result.hidden_signal_score;
  const badge = badgeClass(score);
  const orbitColor = badge === "critical" ? "#c44b37" : badge === "high" ? "#b98518" : "#087568";
  document.querySelector("#scoreOrbit").style.background = `conic-gradient(${orbitColor} ${score * 3.6}deg, #e8dfcf 0deg)`;
  document.querySelector("#signalScore").textContent = score;
  document.querySelector("#topPattern").textContent = result.top_cluster.label;
  document.querySelector("#riskBadge").textContent = badge === "critical" ? "Urgent" : badge === "high" ? "High" : "Watch";
  document.querySelector("#riskBadge").className = `badge ${badge}`;
  document.querySelector("#domainFit").textContent = `${result.domain_fit_score}/100`;
  document.querySelector("#tierName").textContent = result.recommended_tier.name;
  document.querySelector("#priceModel").textContent = `$${result.recommended_tier.monthly_price_usd}/mo`;
  document.querySelector("#sidebarScore").textContent = `${score}/100 hidden signal`;

  renderSourceMix(result);
  renderClusters(result);
  renderActions(result);
  renderEvidence(result);
  if (window.lucide) window.lucide.createIcons();
}

function renderSourceMix(result) {
  const grouped = {};
  result.evidence_events.forEach((event) => {
    grouped[event.source_type] = (grouped[event.source_type] || 0) + 1;
  });
  const entries = Object.entries(grouped).sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...entries.map((entry) => entry[1]));
  document.querySelector("#topSource").textContent = entries.length ? formatCategory(entries[0][0]) : "No source";
  document.querySelector("#sourceMix").innerHTML = entries
    .map(
      ([sourceType, count]) => `
        <div class="source-row">
          <span>${formatCategory(sourceType)}</span>
          <div class="bar-track" aria-hidden="true"><div class="bar-fill" style="width:${(count / max) * 100}%"></div></div>
          <strong>${count}</strong>
        </div>
      `,
    )
    .join("");
}

function renderClusters(result) {
  document.querySelector("#clusterCount").textContent = `${result.clusters.length} patterns`;
  document.querySelector("#clusterList").innerHTML = result.clusters
    .map(
      (cluster) => `
        <article class="cluster-card">
          <div class="cluster-row">
            <span class="cluster-title">${cluster.label}</span>
            <div class="bar-track" aria-hidden="true"><div class="bar-fill ${cluster.severity}" style="width:${Math.min(100, cluster.score)}%"></div></div>
            <strong>${cluster.score}</strong>
          </div>
          <div class="cluster-meta">${cluster.why_it_matters} ${cluster.source_count} source${cluster.source_count === 1 ? "" : "s"} connected.</div>
          <div class="quote">${cluster.representative_quotes[0] || cluster.opportunity}</div>
        </article>
      `,
    )
    .join("");
}

function renderActions(result) {
  document.querySelector("#actionCount").textContent = `${result.action_plan.length} actions`;
  document.querySelector("#actionList").innerHTML = result.action_plan
    .map(
      (action) => `
        <li>
          <span class="priority-dot">${action.priority}</span>
          <div>
            <span class="action-title">${action.title}</span>
            <span class="action-impact">${action.expected_impact}</span>
          </div>
        </li>
      `,
    )
    .join("");
}

function renderEvidence(result) {
  document.querySelector("#evidenceCount").textContent = `${result.evidence_events.length} evidence events`;
  document.querySelector("#evidenceTable").innerHTML = result.evidence_events
    .slice(0, 12)
    .map(
      (event) => `
        <article class="evidence-row">
          <div><strong>${event.source}</strong><span>${event.author}</span></div>
          <div><strong>${formatCategory(event.category)}</strong><span>${formatCategory(event.source_type)}</span></div>
          <div class="evidence-quote">${event.evidence}</div>
          <strong>${event.hidden_weight > 0 ? "+" : ""}${event.hidden_weight}</strong>
        </article>
      `,
    )
    .join("");
}

function readInput() {
  const raw = document.querySelector("#feedbackInput").value.trim();
  if (!raw) return sampleBundle;
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

function runScan() {
  const customerCount = Math.max(1, Number(document.querySelector("#customerCount").value || 1));
  renderResult(analyzeBundle(readInput(), customerCount));
}

function copyBrief() {
  if (!latestResult) runScan();
  const result = latestResult;
  const brief = `hidden.reviews founder brief

Product: ${result.product}
Hidden signal: ${result.hidden_signal_score}/100
Domain fit: ${result.domain_fit_score}/100
Top pattern: ${result.top_cluster.label}
Recommended tier: ${result.recommended_tier.name} at $${result.recommended_tier.monthly_price_usd}/mo

Top action:
${result.action_plan[0]?.title || "No urgent action"}

Domain thesis:
${result.founder_summary.domain_connection}`;
  navigator.clipboard?.writeText(brief);
  document.querySelector("#copyBriefButton span").textContent = "Copied";
  setTimeout(() => {
    document.querySelector("#copyBriefButton span").textContent = "Copy brief";
  }, 1500);
}

function boot() {
  document.querySelector("#feedbackInput").value = JSON.stringify(sampleBundle, null, 2);
  document.querySelector("#scanButton").addEventListener("click", runScan);
  document.querySelector("#scanTopButton").addEventListener("click", runScan);
  document.querySelector("#copyBriefButton").addEventListener("click", copyBrief);
  document.querySelector("#resetButton").addEventListener("click", () => {
    document.querySelector("#customerCount").value = "1800";
    document.querySelector("#feedbackInput").value = JSON.stringify(sampleBundle, null, 2);
    runScan();
  });
  runScan();
  if (window.lucide) window.lucide.createIcons();
}

document.addEventListener("DOMContentLoaded", boot);
