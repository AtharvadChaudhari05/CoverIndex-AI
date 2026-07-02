const RENDER_API_BASE = "https://coverindex-ai.onrender.com";

const HTML = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="theme-color" content="#07131f" />
  <title>CoverIndex AI | Verified Insurance Answers</title>
  <link rel="stylesheet" href="/styles.css" />
</head>
<body>
  <div class="page-shell">
    <div class="page-noise"></div>
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark">CI</div>
        <div>
          <div class="brand-title">CoverIndex AI</div>
          <div class="brand-subtitle">Vectorless PageIndex RAG for insurance policies</div>
        </div>
      </div>
      <div class="topbar-badges">
        <span class="status-pill"><span class="dot"></span><span id="statusBadge">Checking index...</span></span>
        <span class="mini-pill">Verified from PDFs</span>
        <span class="mini-pill">No vector database</span>
      </div>
    </header>

    <main class="layout">
      <section class="hero card">
        <div class="eyebrow">AI insurance assistant</div>
        <h1>Ask questions against the exact policy pages that support the answer.</h1>
        <p class="hero-copy">
          CoverIndex AI routes each query to the right insurer and page range, then returns a grounded response with
          exact citations. The frontend stays responsive on mobile, tablet, and desktop.
        </p>

        <div class="hero-grid">
          <div class="xray-card">
            <div class="xray-head">
              <div>
                <div class="xray-label">Policy X-ray</div>
                <div class="xray-title" id="selectedPolicyTitle">HDFC ERGO - Optima Secure</div>
              </div>
              <div class="xray-badge">LIVE</div>
            </div>
            <div class="xray-metrics">
              <div class="metric">
                <span>INDEX</span>
                <strong id="metricPages">--</strong>
                <small>grounded pages</small>
              </div>
              <div class="metric">
                <span>DOCS</span>
                <strong id="metricDocs">--</strong>
                <small>policy files</small>
              </div>
            </div>
            <div class="xray-points">
              <div class="point ok">Pre &amp; post hospitalization coverage</div>
              <div class="point ok">Day care treatments and claim windows</div>
              <div class="point warn">Waiting periods and exclusions highlighted</div>
            </div>
          </div>

          <div class="query-card">
            <div class="query-header">
              <div>
                <div class="section-label">Ask the documents</div>
                <h2>Verified answer panel</h2>
              </div>
              <button class="ghost-btn" id="clearPolicyBtn" type="button">Clear policy filter</button>
            </div>

            <form id="askForm" class="ask-form">
              <label class="field">
                <span>Your question</span>
                <textarea id="queryInput" rows="4" placeholder="Example: What does HDFC ERGO Optima Secure cover for hospitalization?"></textarea>
              </label>
              <div class="sample-chips" id="sampleChips">
                <button type="button" class="chip" data-query="What are the exclusions in this policy?">Exclusions</button>
                <button type="button" class="chip" data-query="What is the waiting period for maternity coverage?">Waiting period</button>
                <button type="button" class="chip" data-query="How much premium is mentioned for this policy?">Premium</button>
                <button type="button" class="chip" data-query="Summarize the coverage in simple terms.">Summary</button>
              </div>
              <div class="action-row">
                <label class="upload-btn">
                  <input id="uploadInput" type="file" accept="application/pdf" hidden />
                  <span>Upload PDF</span>
                </label>
                <button class="primary-btn" id="askBtn" type="submit">Ask verified answer</button>
              </div>
              <div class="selected-policy" id="selectedPolicyBanner">No policy filter selected. The router will auto-detect the best match.</div>
            </form>
          </div>
        </div>
      </section>

      <section class="answer card" id="answerCard">
        <div class="section-top">
          <div>
            <div class="section-label">Answer</div>
            <h2>Grounded response</h2>
          </div>
          <div class="confidence" id="confidenceBadge">Waiting for a question</div>
        </div>
        <div class="answer-body" id="answerBody">
          Ask a question to see a verified answer pulled from the policy pages.
        </div>
        <div class="answer-meta">
          <div>
            <div class="meta-label">Routing trace</div>
            <div class="meta-list" id="traceList">
              <span class="meta-empty">No trace yet.</span>
            </div>
          </div>
          <div>
            <div class="meta-label">Sources</div>
            <div class="source-list" id="sourceList">
              <span class="meta-empty">No sources yet.</span>
            </div>
          </div>
        </div>
      </section>

      <section class="library card">
        <div class="section-top">
          <div>
            <div class="section-label">Policy library</div>
            <h2>Indexed documents</h2>
          </div>
          <div class="library-count" id="libraryCount">0 policies</div>
        </div>
        <div class="policy-grid" id="policyGrid">
          <div class="skeleton-card"></div>
          <div class="skeleton-card"></div>
          <div class="skeleton-card"></div>
        </div>
      </section>
    </main>
  </div>

  <script src="/app.js"></script>
</body>
</html>`;

const CSS = `:root {
  color-scheme: dark;
  --bg: #07131f;
  --bg-soft: #0d1c2d;
  --card: rgba(14, 27, 42, 0.84);
  --card-strong: rgba(18, 34, 52, 0.94);
  --line: rgba(147, 197, 253, 0.16);
  --line-strong: rgba(148, 163, 184, 0.22);
  --text: #eef5ff;
  --muted: #9fb3c8;
  --muted-2: #7f94ab;
  --accent: #29c3a6;
  --accent-2: #f59e0b;
  --accent-3: #60a5fa;
  --shadow: 0 28px 70px rgba(2, 7, 15, 0.42);
  --radius: 24px;
  --radius-sm: 16px;
  --max: 1240px;
  --font: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

* {
  box-sizing: border-box;
}

html {
  width: 100%;
  overflow-x: hidden;
  -webkit-text-size-adjust: 100%;
}

body {
  margin: 0;
  min-height: 100vh;
  background:
    radial-gradient(circle at 18% 14%, rgba(41, 195, 166, 0.18), transparent 30%),
    radial-gradient(circle at 78% 10%, rgba(96, 165, 250, 0.16), transparent 28%),
    linear-gradient(180deg, #08111d 0%, #0a1726 45%, #07121d 100%);
  color: var(--text);
  font-family: var(--font);
  overflow-x: hidden;
}

button,
input,
textarea {
  font: inherit;
}

button {
  cursor: pointer;
}

.page-shell {
  position: relative;
  min-height: 100vh;
  padding: 20px;
}

.page-noise {
  pointer-events: none;
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.025) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.55), transparent 85%);
  opacity: 0.6;
}

.topbar,
.layout {
  position: relative;
  z-index: 1;
  max-width: var(--max);
  margin: 0 auto;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 4px 0 18px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-mark {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, rgba(41, 195, 166, 0.95), rgba(96, 165, 250, 0.85));
  color: #041019;
  font-weight: 900;
  letter-spacing: 0.08em;
  box-shadow: 0 18px 35px rgba(41, 195, 166, 0.22);
}

.brand-title {
  font-size: 1.1rem;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.brand-subtitle {
  color: var(--muted);
  font-size: 0.92rem;
  margin-top: 2px;
}

.topbar-badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.status-pill,
.mini-pill,
.confidence,
.library-count,
.xray-badge {
  border: 1px solid var(--line);
  background: rgba(10, 18, 30, 0.62);
  backdrop-filter: blur(16px);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 999px;
  color: var(--text);
  font-size: 0.92rem;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--accent);
  box-shadow: 0 0 0 0 rgba(41, 195, 166, 0.6);
  animation: pulse 2s infinite;
}

.mini-pill,
.library-count {
  padding: 10px 14px;
  border-radius: 999px;
  color: var(--muted);
  font-size: 0.9rem;
}

.layout {
  display: grid;
  gap: 18px;
}

.card {
  background: linear-gradient(180deg, rgba(17, 31, 48, 0.94), rgba(11, 22, 35, 0.94));
  border: 1px solid var(--line-strong);
  box-shadow: var(--shadow);
  border-radius: var(--radius);
  overflow: hidden;
}

.hero {
  padding: 28px;
}

.eyebrow,
.section-label {
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: #8eb8ff;
  font-size: 0.75rem;
  font-weight: 800;
}

.hero h1 {
  margin: 12px 0 12px;
  font-size: clamp(2rem, 3.4vw, 4rem);
  line-height: 0.98;
  max-width: 14ch;
}

.hero-copy {
  margin: 0;
  max-width: 70ch;
  color: var(--muted);
  line-height: 1.7;
  font-size: 1rem;
}

.hero-grid {
  margin-top: 24px;
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: 18px;
}

.xray-card,
.query-card,
.answer,
.library {
  background: var(--card);
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: var(--radius);
}

.xray-card {
  padding: 18px;
}

.xray-head,
.query-header,
.section-top {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 14px;
}

.xray-label,
.meta-label {
  color: var(--muted-2);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-weight: 800;
}

.xray-title,
.query-header h2,
.section-top h2 {
  margin-top: 6px;
  font-size: 1.35rem;
  font-weight: 800;
}

.xray-badge {
  padding: 8px 12px;
  border-radius: 999px;
  color: var(--accent);
  font-weight: 800;
  font-size: 0.76rem;
}

.xray-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin: 18px 0;
}

.metric {
  padding: 14px;
  border-radius: var(--radius-sm);
  background: rgba(6, 13, 21, 0.45);
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.metric span {
  display: block;
  color: var(--muted-2);
  font-size: 0.78rem;
  letter-spacing: 0.14em;
  font-weight: 800;
}

.metric strong {
  display: block;
  margin-top: 8px;
  font-size: 2rem;
  line-height: 1;
}

.metric small {
  display: block;
  color: var(--muted);
  margin-top: 8px;
}

.xray-points {
  display: grid;
  gap: 10px;
}

.point {
  padding: 13px 14px;
  border-radius: 14px;
  background: rgba(6, 13, 21, 0.45);
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.point.ok {
  box-shadow: inset 3px 0 0 rgba(41, 195, 166, 0.9);
}

.point.warn {
  box-shadow: inset 3px 0 0 rgba(245, 158, 11, 0.9);
}

.query-card {
  padding: 18px;
}

.ask-form {
  display: grid;
  gap: 14px;
}

.field {
  display: grid;
  gap: 8px;
}

.field span {
  font-size: 0.92rem;
  color: var(--muted);
}

.field textarea {
  width: 100%;
  resize: vertical;
  min-height: 126px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(4, 9, 16, 0.45);
  color: var(--text);
  padding: 16px;
  line-height: 1.6;
  outline: none;
}

.field textarea:focus {
  border-color: rgba(41, 195, 166, 0.55);
  box-shadow: 0 0 0 4px rgba(41, 195, 166, 0.12);
}

.sample-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.chip,
.ghost-btn,
.upload-btn,
.primary-btn {
  border: 0;
  border-radius: 999px;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.chip {
  background: rgba(96, 165, 250, 0.12);
  color: #dbeafe;
  padding: 10px 14px;
  border: 1px solid rgba(96, 165, 250, 0.2);
}

.ghost-btn {
  background: rgba(148, 163, 184, 0.12);
  color: var(--text);
  padding: 10px 14px;
  white-space: nowrap;
}

.upload-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 16px;
  background: rgba(41, 195, 166, 0.12);
  color: #d8fff6;
  border: 1px solid rgba(41, 195, 166, 0.24);
}

.primary-btn {
  background: linear-gradient(135deg, var(--accent), #17b692);
  color: #041019;
  font-weight: 900;
  padding: 12px 18px;
  box-shadow: 0 14px 30px rgba(41, 195, 166, 0.22);
}

.chip:hover,
.ghost-btn:hover,
.upload-btn:hover,
.primary-btn:hover {
  transform: translateY(-1px);
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.selected-policy {
  color: var(--muted);
  font-size: 0.92rem;
  line-height: 1.5;
}

.answer,
.library {
  padding: 18px;
}

.confidence {
  padding: 10px 14px;
  border-radius: 999px;
  color: #d7f5ee;
  font-size: 0.9rem;
  white-space: nowrap;
}

.answer-body {
  margin-top: 12px;
  padding: 18px;
  border-radius: 20px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(4, 9, 16, 0.42);
  color: #e8f1fb;
  line-height: 1.75;
  min-height: 180px;
  white-space: pre-line;
}

.answer-meta {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.meta-list,
.source-list {
  display: grid;
  gap: 10px;
  margin-top: 10px;
}

.meta-empty {
  color: var(--muted);
  font-size: 0.92rem;
}

.trace-item,
.source-item {
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(6, 13, 21, 0.45);
}

.trace-item {
  color: #dbeafe;
}

.source-item {
  display: grid;
  gap: 6px;
}

.source-head {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: space-between;
  align-items: center;
}

.source-head strong {
  font-size: 0.98rem;
}

.source-head span {
  color: var(--muted);
  font-size: 0.88rem;
}

.source-snippet {
  color: #c3d3e4;
  font-size: 0.92rem;
  line-height: 1.6;
}

.policy-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.policy-card,
.skeleton-card {
  min-height: 150px;
  border-radius: 20px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(6, 13, 21, 0.45);
}

.policy-card {
  text-align: left;
  color: var(--text);
  padding: 16px;
}

.policy-card.active {
  border-color: rgba(41, 195, 166, 0.42);
  box-shadow: inset 0 0 0 1px rgba(41, 195, 166, 0.22);
  background: linear-gradient(180deg, rgba(12, 29, 44, 0.98), rgba(6, 13, 21, 0.55));
}

.policy-card .title {
  font-size: 1.02rem;
  font-weight: 800;
}

.policy-card .meta {
  margin-top: 8px;
  color: var(--muted);
  line-height: 1.55;
  font-size: 0.92rem;
}

.policy-tags {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(41, 195, 166, 0.1);
  color: #cbfff4;
  font-size: 0.76rem;
  border: 1px solid rgba(41, 195, 166, 0.16);
}

.skeleton-card {
  position: relative;
  overflow: hidden;
}

.skeleton-card::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(110deg, transparent 0%, rgba(255, 255, 255, 0.06) 50%, transparent 100%);
  transform: translateX(-120%);
  animation: shimmer 1.6s infinite;
}

.library-count {
  color: #dbeafe;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(41, 195, 166, 0.62); }
  70% { box-shadow: 0 0 0 10px rgba(41, 195, 166, 0); }
  100% { box-shadow: 0 0 0 0 rgba(41, 195, 166, 0); }
}

@keyframes shimmer {
  100% { transform: translateX(120%); }
}

@media (max-width: 1080px) {
  .hero-grid,
  .answer-meta,
  .policy-grid {
    grid-template-columns: 1fr;
  }

  .topbar {
    align-items: start;
    flex-direction: column;
  }
}

@media (max-width: 720px) {
  .page-shell {
    padding: 14px;
  }

  .hero,
  .query-card,
  .answer,
  .library {
    padding: 16px;
  }

  .hero h1 {
    max-width: none;
  }

  .xray-metrics {
    grid-template-columns: 1fr;
  }

  .action-row {
    flex-direction: column;
  }

  .action-row > * {
    width: 100%;
  }

  .topbar-badges {
    justify-content: flex-start;
  }
}
`;

const JS = `const state = {
  policies: [],
  selectedPolicy: "",
  loading: false,
};

const els = {};

document.addEventListener("DOMContentLoaded", function () {
  els.statusBadge = document.getElementById("statusBadge");
  els.metricPages = document.getElementById("metricPages");
  els.metricDocs = document.getElementById("metricDocs");
  els.selectedPolicyTitle = document.getElementById("selectedPolicyTitle");
  els.selectedPolicyBanner = document.getElementById("selectedPolicyBanner");
  els.clearPolicyBtn = document.getElementById("clearPolicyBtn");
  els.queryInput = document.getElementById("queryInput");
  els.askForm = document.getElementById("askForm");
  els.askBtn = document.getElementById("askBtn");
  els.uploadInput = document.getElementById("uploadInput");
  els.answerBody = document.getElementById("answerBody");
  els.answerCard = document.getElementById("answerCard");
  els.confidenceBadge = document.getElementById("confidenceBadge");
  els.traceList = document.getElementById("traceList");
  els.sourceList = document.getElementById("sourceList");
  els.policyGrid = document.getElementById("policyGrid");
  els.libraryCount = document.getElementById("libraryCount");

  bindEvents();
  loadStatus();
  loadPolicies();
  renderEmptyState();
});

function bindEvents() {
  els.askForm.addEventListener("submit", function (event) {
    event.preventDefault();
    submitQuery();
  });

  els.clearPolicyBtn.addEventListener("click", function () {
    state.selectedPolicy = "";
    updatePolicyBanner();
    renderPolicies();
  });

  document.getElementById("sampleChips").addEventListener("click", function (event) {
    var button = event.target.closest("[data-query]");
    if (!button) return;
    els.queryInput.value = button.getAttribute("data-query") || "";
    els.queryInput.focus();
  });

  els.uploadInput.addEventListener("change", function () {
    if (els.uploadInput.files && els.uploadInput.files[0]) {
      uploadPolicy(els.uploadInput.files[0]);
    }
  });
}

async function loadStatus() {
  try {
    var response = await fetch("/api/status", { cache: "no-store" });
    var data = await response.json();
    if (data && data.ready) {
      els.statusBadge.textContent = data.page_count + " pages indexed";
      els.metricPages.textContent = formatCount(data.page_count);
      els.metricDocs.textContent = formatCount(data.document_count);
      return;
    }
  } catch (error) {
    console.error("status load failed", error);
  }

  els.statusBadge.textContent = "Backend offline";
  els.metricPages.textContent = "0";
  els.metricDocs.textContent = "0";
}

async function loadPolicies() {
  try {
    var response = await fetch("/api/policies", { cache: "no-store" });
    var data = await response.json();
    state.policies = Array.isArray(data.policies) ? data.policies : [];
    renderPolicies();
    els.libraryCount.textContent = state.policies.length + (state.policies.length === 1 ? " policy" : " policies");
  } catch (error) {
    console.error("policy load failed", error);
    els.libraryCount.textContent = "0 policies";
    els.policyGrid.innerHTML = "<div class=\\"skeleton-card\\"></div>";
  }
}

function renderPolicies() {
  if (!state.policies.length) {
    els.policyGrid.innerHTML = '<div class="skeleton-card"></div><div class="skeleton-card"></div><div class="skeleton-card"></div>';
    return;
  }

  els.policyGrid.innerHTML = state.policies.map(function (policy) {
    var active = state.selectedPolicy && state.selectedPolicy === policy.file_name ? " active" : "";
    var tags = [];
    if (policy.insurer) tags.push(policy.insurer);
    if (policy.product) tags.push(policy.product);
    if (policy.document_type) tags.push(policy.document_type);

    return [
      '<button class="policy-card' + active + '" type="button" data-policy="' + escapeHtml(policy.file_name) + '">',
      '<div class="title">' + escapeHtml(policy.file_name) + '</div>',
      '<div class="meta">' + escapeHtml(policy.title || "Verified policy document") + '</div>',
      '<div class="meta">Pages: ' + escapeHtml(String(policy.page_count || 0)) + '</div>',
      '<div class="policy-tags">' + tags.map(function (tag) { return '<span class="tag">' + escapeHtml(tag) + '</span>'; }).join("") + '</div>',
      '</button>',
    ].join("");
  }).join("");

  els.policyGrid.querySelectorAll("[data-policy]").forEach(function (card) {
    card.addEventListener("click", function () {
      state.selectedPolicy = card.getAttribute("data-policy") || "";
      updatePolicyBanner();
      renderPolicies();
    });
  });

  updatePolicyBanner();
}

function updatePolicyBanner() {
  if (state.selectedPolicy) {
    els.selectedPolicyBanner.textContent = "Filtered to: " + state.selectedPolicy + ". Answers will be grounded to this document when possible.";
    els.selectedPolicyTitle.textContent = state.selectedPolicy;
    return;
  }

  els.selectedPolicyBanner.textContent = "No policy filter selected. The router will auto-detect the best match.";
  els.selectedPolicyTitle.textContent = "HDFC ERGO - Optima Secure";
}

function renderEmptyState() {
  els.answerBody.textContent = "Ask a question to see a verified answer pulled from the policy pages.";
  els.confidenceBadge.textContent = "Waiting for a question";
  els.traceList.innerHTML = '<span class="meta-empty">No trace yet.</span>';
  els.sourceList.innerHTML = '<span class="meta-empty">No sources yet.</span>';
}

async function submitQuery() {
  var query = (els.queryInput.value || "").trim();
  if (!query) {
    els.queryInput.focus();
    return;
  }

  setLoading(true);
  try {
    var body = { query: query };
    if (state.selectedPolicy) body.file_name = state.selectedPolicy;

    var response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    var data = await response.json();
    if (!response.ok) {
      throw new Error(data && data.error ? data.error : "Request failed");
    }

    renderAnswer(data);
    els.answerCard.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    renderError(error);
  } finally {
    setLoading(false);
  }
}

async function uploadPolicy(file) {
  setLoading(true);
  try {
    var formData = new FormData();
    formData.append("file", file, file.name);
    var response = await fetch("/api/upload", { method: "POST", body: formData });
    var data = await response.json();
    if (!response.ok) {
      throw new Error(data && data.error ? data.error : "Upload failed");
    }

    els.queryInput.value = "Summarize the uploaded policy file " + file.name + ".";
    await loadStatus();
    await loadPolicies();
    els.selectedPolicyBanner.textContent = "Uploaded " + file.name + ". The index has been refreshed.";
    renderTrace(["upload: " + file.name + " indexed successfully", "retriever: upload added to the policy library"]);
    els.sourceList.innerHTML = '<div class="source-item"><div class="source-head"><strong>' + escapeHtml(file.name) + '</strong><span>' + escapeHtml(String(data.page_count || 0)) + " pages indexed</span></div><div class="source-snippet">The uploaded PDF has been added to the live document library.</div></div>";
    els.confidenceBadge.textContent = "Upload processed";
  } catch (error) {
    renderError(error);
  } finally {
    setLoading(false);
    els.uploadInput.value = "";
  }
}

function renderAnswer(data) {
  var answer = typeof data.answer === "string" ? data.answer : "No answer returned.";
  els.answerBody.innerHTML = formatAnswer(answer);
  els.confidenceBadge.textContent = "Confidence " + Math.round((data.confidence || 0) * 100) + "%";
  renderTrace(Array.isArray(data.trace) ? data.trace : []);
  renderSources(Array.isArray(data.sources) ? data.sources : []);
  if (data.route && data.route.reasoning) {
    els.statusBadge.textContent = data.route.reasoning;
  }
}

function renderSources(sources) {
  if (!sources.length) {
    els.sourceList.innerHTML = '<span class="meta-empty">No grounded sources returned for this answer.</span>';
    return;
  }

  els.sourceList.innerHTML = sources.map(function (source) {
    var citation = source.citation || ("p. " + (source.page_number || ""));
    var title = [source.insurer, source.product].filter(Boolean).join(" • ") || "Verified source";
    return [
      '<div class="source-item">',
      '<div class="source-head">',
      '<strong>' + escapeHtml(citation) + '</strong>',
      '<span>' + escapeHtml(title) + '</span>',
      '</div>',
      '<div class="source-snippet">' + escapeHtml(source.snippet || "Relevant source extracted from the policy pages.") + '</div>',
      '</div>',
    ].join("");
  }).join("");
}

function renderTrace(trace) {
  if (!trace.length) {
    els.traceList.innerHTML = '<span class="meta-empty">No trace yet.</span>';
    return;
  }

  els.traceList.innerHTML = trace.map(function (item) {
    return '<div class="trace-item">' + escapeHtml(item) + '</div>';
  }).join("");
}

function renderError(error) {
  var message = error && error.message ? error.message : "Something went wrong.";
  els.answerBody.innerHTML = "<strong>Request failed.</strong><br>" + escapeHtml(message);
  els.confidenceBadge.textContent = "Error";
  renderTrace(["client: request failed"]);
  els.sourceList.innerHTML = '<span class="meta-empty">No sources available.</span>';
}

function setLoading(isLoading) {
  state.loading = isLoading;
  els.askBtn.disabled = isLoading;
  els.askBtn.textContent = isLoading ? "Working..." : "Ask verified answer";
}

function formatCount(value) {
  var num = Number(value || 0);
  return new Intl.NumberFormat("en-IN").format(num);
}

function formatAnswer(text) {
  return escapeHtml(text)
    .replace(/\\n\\n/g, "<br><br>")
    .replace(/\\n/g, "<br>");
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
`;

addEventListener("fetch", function (event) {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);

  if (url.pathname.startsWith("/api/")) {
    return proxyApi(request, url);
  }

  if (url.pathname === "/styles.css") {
    return new Response(CSS, {
      headers: makeHeaders("text/css; charset=utf-8"),
    });
  }

  if (url.pathname === "/app.js") {
    return new Response(JS, {
      headers: makeHeaders("application/javascript; charset=utf-8"),
    });
  }

  return new Response(HTML, {
    headers: makeHeaders("text/html; charset=utf-8"),
  });
}

async function proxyApi(request, url) {
  const target = new URL(url.pathname + url.search, RENDER_API_BASE);
  const init = {
    method: request.method,
    headers: new Headers(request.headers),
    redirect: "follow",
  };

  init.headers.delete("host");
  init.headers.delete("cf-connecting-ip");
  init.headers.delete("cf-ipcountry");
  init.headers.delete("cf-ray");
  init.headers.delete("x-forwarded-for");
  init.headers.delete("x-forwarded-proto");
  init.headers.delete("x-forwarded-host");

  if (!["GET", "HEAD"].includes(request.method)) {
    init.body = await request.arrayBuffer();
  }

  const response = await fetch(target.toString(), init);
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: makeHeadersFrom(response.headers),
  });
}

function makeHeaders(contentType) {
  return {
    "Content-Type": contentType,
    "Cache-Control": "no-store, max-age=0",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
  };
}

function makeHeadersFrom(sourceHeaders) {
  const headers = new Headers(sourceHeaders);
  headers.set("Cache-Control", "no-store, max-age=0");
  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("X-Frame-Options", "DENY");
  headers.set("Referrer-Policy", "no-referrer");
  return headers;
}
