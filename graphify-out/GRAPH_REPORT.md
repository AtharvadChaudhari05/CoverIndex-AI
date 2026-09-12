# Graph Report - CoverIndex-AI  (2026-09-12)

## Corpus Check
- Corpus is ~20,614 words - fits in a single context window. You may not need a graph.

## Summary
- 303 nodes · 568 edges · 28 communities (13 shown, 13 thin omitted)
- Extraction: 92% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 42 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Query Agent & Guardrail Tests
- Chat UI Core
- Deployment & Multi-LLM Resilience
- Conversation State & Advisor Prompts
- Retrieval Design & Sample Answers
- PDF Ingestion Pipeline
- Voice Input UI
- Chat Message Rendering
- Page Index & BM25 Search
- Chat Session Persistence
- HTTP Request Handler
- Cloudflare Worker Proxy
- Scope Lock & Refusal Rules
- Package Init
- Prompt Safety Rules
- Source Rendering UI
- Feature Showcase Timer
- Landing Showcase Timer
- Policy Vault Table UI
- Project Package Marker
- Best-Sentence Helper (orphan)
- Expanded-Context Helper (orphan)
- PolicyLens Handler (duplicate ref)
- Platform Guide Screen
- index.html Module Ref
- styles.css Module Ref

## God Nodes (most connected - your core abstractions)
1. `answer_query()` - 20 edges
2. `PageIndex` - 14 edges
3. `extract_records_from_pdf()` - 13 edges
4. `PromptGuardrailTests` - 13 edges
5. `submitQuery()` - 12 edges
6. `build_page_index()` - 11 edges
7. `PageRecord` - 11 edges
8. `normalize_text()` - 11 edges
9. `tokenize()` - 11 edges
10. `Tech Stack Table` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Rule-Based Query Router` --implements--> `route_query()`  [EXTRACTED]
  capstone_documentation.md → policy_rag/agent.py
- `policy_rag/agent.py (The Brain)` --references--> `route_query()`  [INFERRED]
  README.md → policy_rag/agent.py
- `Scope-Lock and Out-of-Scope Refusal` --implements--> `classify_query_scope()`  [EXTRACTED]
  capstone_documentation.md → policy_rag/agent.py
- `Post-Generation Grounding Verifier` --implements--> `is_allowed_normal_mode_answer()`  [EXTRACTED]
  capstone_documentation.md → policy_rag/agent.py
- `Grounding Rules (Answer Only From Retrieved Context)` --conceptually_related_to--> `is_allowed_normal_mode_answer()`  [INFERRED]
  prompts/system_prompt_insurance_rag.md → policy_rag/agent.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Explainable AI Advisor Output Template Pattern** — readme_explainable_ai_advisor_mode, prompts_system_prompt_insurance_rag_advisor_template, prompts_system_prompt_fallback_confirmed_advisor_template, public_index_app_dashboard [INFERRED 0.85]
- **Consent-Based Internet Fallback Flow** — capstone_documentation_consent_based_internet_fallback, policy_rag_agent_is_confirmation_query, policy_rag_agent_perform_internet_search, policy_rag_server_conversationstate, prompts_system_prompt_fallback_confirmed_required_prefix, prompts_system_prompt_insurance_rag_no_context_tag [EXTRACTED 1.00]
- **Deployment Architecture (Render + Cloudflare)** — render_cover_index_api_service, readme_cloudflare_pages, worker_js_cloudflare_worker, capstone_documentation_decoupled_edge_deployment, public_index_landing_page [INFERRED 0.85]

## Communities (28 total, 13 thin omitted)

### Community 0 - "Query Agent & Guardrail Tests"
Cohesion: 0.08
Nodes (39): Multilingual Query Rewriting and Translation, answer_has_citations(), answer_query(), build_rag_messages(), classify_query_scope(), extract_product_hint(), _has_keyword(), is_allowed_normal_mode_answer() (+31 more)

### Community 1 - "Chat UI Core"
Cohesion: 0.05
Nodes (40): activeChatHistory, appDashboard, appInspector, attachmentBtn, attachmentFileName, attachmentPreviewBar, btnNewChat, btnToggleInspector (+32 more)

### Community 2 - "Deployment & Multi-LLM Resilience"
Cohesion: 0.07
Nodes (33): Decoupled Edge Deployment, Dual-LLM Resilience (Groq -> Gemini), Free-Tier LLM Rate Limits (Limitation), Post-Generation Grounding Verifier, Gzip-Cached Page Index, Jailbreak Resistance, Rule-Based Query Router, Scope-Lock and Out-of-Scope Refusal (+25 more)

### Community 3 - "Conversation State & Advisor Prompts"
Cohesion: 0.09
Nodes (27): Free-Look Period (15 Days), Consent-Based Internet Fallback, In-Memory Session State (Limitation), Three-State Session Machine, ConversationState, Explainable AI Advisor Template (Fallback Mode), Citation Rules (Fallback Mode), Grounding Rules (Fallback Mode) (+19 more)

### Community 4 - "Retrieval Design & Sample Answers"
Cohesion: 0.08
Nodes (26): Annual Renewal, Contractual Basis of Policy, Dental Treatments Exclusion, Hospitalization Coverage, Pre-Existing Diseases Exclusion (48 Months), Premium Payment Condition, Renewal Requirement, SBI General Insurance Company Limited (+18 more)

### Community 5 - "PDF Ingestion Pipeline"
Cohesion: 0.20
Nodes (16): Any, default_source_candidates(), Path, build_page_index(), extract_records_from_pdf(), infer_document_type(), infer_insurer(), infer_product() (+8 more)

### Community 6 - "Voice Input UI"
Cohesion: 0.21
Nodes (15): activateVoiceCapture(), createVoiceRecognition(), getVoiceLanguageLabel(), getVoiceRecognitionLanguage(), handleVoiceLanguageChange(), initVoiceLanguagePreference(), initVoiceSupport(), isMobileVoiceEnvironment() (+7 more)

### Community 7 - "Chat Message Rendering"
Cohesion: 0.23
Nodes (15): addMessage(), appendMetadataFooter(), clearStagedAttachment(), getActiveSession(), loadIndexStatus(), parseMarkdown(), persistActiveSession(), renderRouteTrace() (+7 more)

### Community 8 - "Page Index & BM25 Search"
Cohesion: 0.31
Nodes (6): PageIndex, Counter, Path, PageRecord, SearchHit, ensure_index()

### Community 9 - "Chat Session Persistence"
Cohesion: 0.31
Nodes (10): createChatSessionItem(), createSessionId(), createSessionListItem(), ensureActiveSession(), formatSessionTime(), initChatSessions(), openChatSession(), renderChatSessions() (+2 more)

### Community 10 - "HTTP Request Handler"
Cohesion: 0.32
Nodes (3): BaseHTTPRequestHandler, HTTPStatus, PolicyLensHandler

### Community 11 - "Cloudflare Worker Proxy"
Cohesion: 0.67
Nodes (3): handleRequest(), proxyApiRequest(), STATIC_ASSETS

### Community 12 - "Scope Lock & Refusal Rules"
Cohesion: 0.67
Nodes (3): Scope Lock (Fallback-Confirmed Prompt), Exact Refusal Wording for Non-Insurance Topics, Scope Lock (Insurance RAG Prompt)

## Ambiguous Edges - Review These
- `google-genai` → `google-generativeai`  [AMBIGUOUS]
  requirements.txt · relation: conceptually_related_to

## Knowledge Gaps
- **83 isolated node(s):** `typingSentences`, `activeChatHistory`, `uploadedFiles`, `indexedPolicies`, `chatSessions` (+78 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 106 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `google-genai` and `google-generativeai`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Tech Stack Table` connect `Deployment & Multi-LLM Resilience` to `Conversation State & Advisor Prompts`?**
  _High betweenness centrality (0.353) - this node is a cross-community bridge._
- **Why does `enterDashboard()` connect `Deployment & Multi-LLM Resilience` to `Chat UI Core`?**
  _High betweenness centrality (0.302) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `PageIndex` (e.g. with `answer_query()` and `PageRecord`) actually correct?**
  _`PageIndex` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `typingSentences`, `activeChatHistory`, `uploadedFiles` to the rest of the system?**
  _83 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Query Agent & Guardrail Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.08355367530407191 - nodes in this community are weakly interconnected._
- **Should `Chat UI Core` be split into smaller, more focused modules?**
  _Cohesion score 0.045454545454545456 - nodes in this community are weakly interconnected._