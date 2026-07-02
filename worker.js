addEventListener("fetch", (event) => {
  event.respondWith(handleRequest(event.request));
});

const RENDER_API_BASE = "https://coverindex-ai.onrender.com";
const HTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <meta name="theme-color" content="#0b0728" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <meta name="mobile-web-app-capable" content="yes" />
  <title>CoverIndex AI - Your AI Insurance Assistant</title>
  <link rel="stylesheet" href="/styles.css?v=3" />
  <!-- Google Fonts: Inter & Outfit -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <!-- Lucide Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>
</head>
<body>
  <div class="mobile-backdrop" id="mobileBackdrop"></div>

  <!-- Screen 1: Landing Page -->
  <div class="landing-page" id="landingPage">
    <!-- Left Pane: Gradient & Policy X-ray Mockup -->
    <div class="landing-left">
      <div class="landing-brand">
        <i data-lucide="shield-check" class="brand-logo-icon"></i>
        <span>CoverIndex AI</span>
      </div>

      <div class="mockup-card-container">
        <div class="mockup-card">
          <div class="mockup-header">
            <div class="mockup-icon-wrapper">
              <i data-lucide="sparkles"></i>
            </div>
            <div>
              <div class="mockup-title">Policy X-ray</div>
              <div class="mockup-subtitle">HDFC ERGO - Optima Secure</div>
            </div>
          </div>
          <div class="mockup-stats">
            <div class="mockup-stat">
              <div class="stat-label">SUM INSURED</div>
              <div class="stat-val">₹10 L</div>
            </div>
            <div class="mockup-stat">
              <div class="stat-label">PREMIUM</div>
              <div class="stat-val">₹24,568<span>/yr</span></div>
            </div>
          </div>
          <div class="mockup-list">
            <div class="mockup-list-item checked">
              <i data-lucide="check-circle-2"></i>
              <span>Pre & Post Hospitalization</span>
            </div>
            <div class="mockup-list-item checked">
              <i data-lucide="check-circle-2"></i>
              <span>Day Care Treatments</span>
            </div>
            <div class="mockup-list-item yellow">
              <i data-lucide="help-circle"></i>
              <span>Maternity (after 3 yrs)</span>
            </div>
            <div class="mockup-list-item crossed">
              <i data-lucide="x-circle"></i>
              <span>Routine Dental</span>
            </div>
          </div>
        </div>
      </div>

      <div class="landing-left-footer">
        <h3>Get an instant Policy X-ray</h3>
        <p>See coverage, gaps and exclusions at a glance.</p>
        <div class="slider-dots">
          <span class="dot active"></span>
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
        <div class="powered-by">Powered by CoverIndex</div>
      </div>
    </div>

    <!-- Right Pane: Actions & Ask Button -->
    <div class="landing-right">
      <div class="landing-right-content">
        <h1 class="main-title">Your <span>AI Insurance</span> Assistant</h1>
        <p class="main-subtitle">Compare quotes, buy policies, raise claims — all through conversation.</p>

        <div class="action-grid-2x2">
          <div class="action-card-landing" onclick="enterDashboard('quotes')">
            <div class="icon-box blue">
              <i data-lucide="car"></i>
            </div>
            <span>Get Quotes</span>
          </div>
          <div class="action-card-landing" onclick="enterDashboard('scan')">
            <div class="icon-box purple">
              <i data-lucide="file-text"></i>
            </div>
            <span>Scan Policy PDF</span>
          </div>
          <div class="action-card-landing" onclick="enterDashboard('renew')">
            <div class="icon-box orange">
              <i data-lucide="refresh-cw"></i>
            </div>
            <span>Renew Insurance</span>
          </div>
          <div class="action-card-landing" onclick="enterDashboard('ask')">
            <div class="icon-box cyan">
              <i data-lucide="help-circle"></i>
            </div>
            <span>Ask Anything</span>
          </div>
        </div>

        <button class="primary-ask-btn" onclick="enterDashboard()">
          <i data-lucide="message-square"></i> Ask CoverIndex AI
        </button>

        <p class="agree-text">By clicking, you agree to our Privacy Policy and Terms & Conditions.</p>
        <div class="signin-link">Already have an account? <span onclick="enterDashboard()">Sign in <i data-lucide="chevron-right"></i></span></div>
      </div>

      <footer class="landing-right-footer">
        <div class="footer-badge"><i data-lucide="check"></i> IRDAI-certified</div>
        <div class="footer-badge"><i data-lucide="users"></i> 50+ insurers</div>
        <div class="footer-badge"><i data-lucide="clock"></i> 24x7</div>
      </footer>
    </div>
  </div>

  <!-- Screen 2 & 3: Chat Dashboard -->
  <div class="app-dashboard hidden" id="appDashboard">
    <!-- Left Sidebar -->
    <aside class="app-sidebar">
      <div class="sidebar-top">
        <div class="sidebar-brand">
          <i data-lucide="shield-check" class="brand-logo-icon"></i>
          <span>CoverIndex AI</span>
          <button class="icon-btn collapse-sidebar-btn" id="collapseSidebarBtn" title="Collapse Sidebar">
            <i data-lucide="align-justify"></i>
          </button>
        </div>

        <nav class="nav-menu">
          <a href="#" class="nav-item active" id="btnNavNewChat">
            <i data-lucide="plus" class="nav-icon"></i>
            <span>New Chat</span>
          </a>
          <a href="#" class="nav-item" id="btnNavSearch">
            <i data-lucide="search" class="nav-icon"></i>
            <span>Search Chats</span>
          </a>
          <a href="#" class="nav-item" id="btnNavGuide">
            <i data-lucide="shield" class="nav-icon"></i>
            <span>Insurance Guide</span>
          </a>
          <a href="#" class="nav-item" id="btnNavPlatform">
            <i data-lucide="sparkles" class="nav-icon"></i>
            <span>Platform Guide</span>
          </a>
          <a href="#" class="nav-item" id="btnNavVault">
            <i data-lucide="folder-lock" class="nav-icon"></i>
            <span>Insurance Vault</span>
            <span class="nav-badge">NEW</span>
          </a>
        </nav>

        <!-- Dynamic Chats List Section -->
        <div class="chats-section">
          <div class="section-divider">CHATS</div>
          <div class="chats-list" id="chatsList">
            <div class="no-chats-placeholder">
              <i data-lucide="message-square"></i>
              <span>No conversations yet</span>
            </div>
          </div>
          <a href="#" class="view-archived"><i data-lucide="archive"></i> View archived</a>
        </div>
      </div>

      <!-- Sidebar Footer User Profile -->
      <div class="sidebar-user">
        <div class="user-profile">
          <div class="avatar-guest">G</div>
          <div>
            <div class="user-name">Guest</div>
            <div class="user-tag">Sign in with phone</div>
          </div>
        </div>
        <button class="icon-btn dots-btn"><i data-lucide="more-horizontal"></i></button>
      </div>
    </aside>

    <!-- Main Workspace -->
    <main class="app-workspace">
      <!-- Top header bar -->
      <header class="workspace-header">
        <div class="header-left">
          <button class="icon-btn header-menu-btn" id="mobileMenuBtn">
            <i data-lucide="menu"></i>
          </button>
          <span class="active-chat-title" id="chatSessionTitle">New Chat</span>
        </div>
        <div class="header-right">
          <!-- Ready status badge -->
          <div class="index-badge">
            <span class="pulse-dot"></span>
            <span id="statusText">Agent Active</span>
          </div>
          <!-- Upload Shortcut button -->
          <button class="upload-badge-btn" id="headerUploadBtn" title="Upload Document for instant analysis">
            <i data-lucide="upload-cloud"></i> Upload PDF
          </button>
          <button class="icon-btn" id="btnToggleInspector" title="Toggle Inspector Drawer">
            <i data-lucide="layout-sidebar-open"></i>
          </button>
        </div>
      </header>

      <!-- Center Scrolling Chat Feed / Welcome State -->
      <div class="workspace-body" id="workspaceBody">
        
        <!-- Welcome Screen (Shown initially, hidden when messages start) -->
        <div class="welcome-screen" id="welcomeScreen">
          <h2 class="welcome-greeting">Looking to <span class="typing-text" id="typingTarget">renew a policy?</span></h2>
          
          <div class="welcome-grid-2x3">
            <div class="welcome-card" onclick="triggerPreset('quotes')">
              <div class="welcome-card-icon blue"><i data-lucide="car"></i></div>
              <div>
                <h4>Get Quotes</h4>
                <p>Enter vehicle number</p>
              </div>
            </div>
            <div class="welcome-card" onclick="triggerUpload()">
              <div class="welcome-card-icon purple"><i data-lucide="file-text"></i></div>
              <div>
                <h4>Scan Policy PDF</h4>
                <p>Upload for instant X-ray</p>
              </div>
            </div>
            <div class="welcome-card" onclick="triggerPreset('renew')">
              <div class="welcome-card-icon orange"><i data-lucide="refresh-cw"></i></div>
              <div>
                <h4>Renew Insurance</h4>
                <p>Compare plans & save</p>
              </div>
            </div>
            <div class="welcome-card" onclick="triggerPreset('vault')">
              <div class="welcome-card-icon yellow"><i data-lucide="folder-lock"></i></div>
              <div>
                <h4>My Policies</h4>
                <p>View status & documents</p>
              </div>
            </div>
            <div class="welcome-card" onclick="triggerPreset('claim')">
              <div class="welcome-card-icon cyan"><i data-lucide="heart-handshake"></i></div>
              <div>
                <h4>Raise a Claim</h4>
                <p>File & track claims</p>
              </div>
            </div>
            <div class="welcome-card" onclick="triggerPreset('ask')">
              <div class="welcome-card-icon pink"><i data-lucide="help-circle"></i></div>
              <div>
                <h4>Ask Anything</h4>
                <p>IDV, addons, NCB & more</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Chat window messages container (hidden initially) -->
        <div class="view-screen hidden" id="chatFeedWindow">
          <div class="chat-history" id="chatHistory"></div>
        </div>

        <!-- Search Chats Screen (hidden initially) -->
        <div class="view-screen hidden" id="searchChatsScreen">
          <div class="screen-header">
            <div class="screen-icon"><i data-lucide="search"></i></div>
            <h2>Search Conversations</h2>
            <p>Find past policies, quotes, and answers.</p>
          </div>
          <div class="search-bar-container">
            <i data-lucide="search"></i>
            <input type="text" placeholder="Search for 'term insurance IDV'..." />
          </div>
          <div class="empty-state-card">
            <i data-lucide="inbox"></i>
            <h3>No matching chats found</h3>
            <p>Try searching for a different keyword or start a new chat.</p>
          </div>
        </div>

        <!-- Insurance Guide Screen (hidden initially) -->
        <div class="view-screen hidden" id="insuranceGuideScreen">
          <div class="screen-header">
            <div class="screen-icon"><i data-lucide="shield"></i></div>
            <h2>Insurance Guide</h2>
            <p>Explore resources and understand coverage options.</p>
          </div>
          <div class="guide-grid">
            <div class="guide-card">
              <div class="guide-icon"><i data-lucide="activity"></i></div>
              <h3>Health Insurance</h3>
              <p>Learn about waiting periods, copays, and exclusions.</p>
              <button class="guide-btn" onclick="triggerPreset('ask', 'What are standard waiting periods in health insurance?')">Learn More</button>
            </div>
            <div class="guide-card">
              <div class="guide-icon"><i data-lucide="car"></i></div>
              <h3>Motor Insurance</h3>
              <p>Understand IDV, NCB, and zero depreciation add-ons.</p>
              <button class="guide-btn" onclick="triggerPreset('ask', 'How is IDV calculated for a 3 year old car?')">Learn More</button>
            </div>
            <div class="guide-card">
              <div class="guide-icon"><i data-lucide="heart"></i></div>
              <h3>Term Life</h3>
              <p>Secure your family's future with the right sum assured.</p>
              <button class="guide-btn" onclick="triggerPreset('ask', 'What is a term life insurance policy?')">Learn More</button>
            </div>
          </div>
        </div>

        <!-- Platform Guide Screen (hidden initially) -->
        <div class="view-screen hidden" id="platformGuideScreen">
          <div class="screen-header">
            <div class="screen-icon"><i data-lucide="sparkles"></i></div>
            <h2>Platform Guide</h2>
            <p>Master CoverIndex AI features and workflows.</p>
          </div>
          <div class="feature-list">
            <div class="feature-item">
              <div class="feature-icon"><i data-lucide="file-text"></i></div>
              <div class="feature-text">
                <h4>1. Upload Policy PDFs</h4>
                <p>Click the attachment clip to upload any policy document. The AI will instantly read and index it for your questions.</p>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon"><i data-lucide="layout-sidebar-open"></i></div>
              <div class="feature-text">
                <h4>2. Inspect Grounding Sources</h4>
                <p>Click the sidebar icon on the top right to open the Inspection Console. See exactly which pages of the PDF the AI used.</p>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon"><i data-lucide="cpu"></i></div>
              <div class="feature-text">
                <h4>3. View Routing Trace</h4>
                <p>The AI automatically routes questions to specialized agents (e.g. HDFC Ergo vs SBI General). Check the Trace tab to see how it thinks.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Insurance Vault Screen (hidden initially) -->
        <div class="view-screen hidden" id="insuranceVaultScreen">
          <div class="screen-header">
            <div class="screen-icon"><i data-lucide="folder-lock"></i></div>
            <h2>Insurance Vault</h2>
            <p>Your secure repository of indexed policy documents.</p>
          </div>
          <div class="vault-stats">
            <div class="vault-stat">
              <span>Indexed Policies</span>
              <strong>72</strong>
            </div>
            <div class="vault-stat">
              <span>Total Pages</span>
              <strong>1,954</strong>
            </div>
            <div class="vault-stat">
              <span>Storage Status</span>
              <strong class="text-green">Active</strong>
            </div>
          </div>
          <div class="vault-table-container">
            <table class="vault-table">
              <thead>
                <tr>
                  <th>Document Name</th>
                  <th>Insurer</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody id="vaultTableBody">
                <!-- Populated by JS -->
                <tr>
                  <td><i data-lucide="file-text"></i> SBI General Policy.pdf</td>
                  <td>SBI General</td>
                  <td><span class="badge success">Verified</span></td>
                  <td><button class="icon-btn"><i data-lucide="eye"></i></button></td>
                </tr>
                <tr>
                  <td><i data-lucide="file-text"></i> HDFC Ergo Optima.pdf</td>
                  <td>HDFC Ergo</td>
                  <td><span class="badge success">Verified</span></td>
                  <td><button class="icon-btn"><i data-lucide="eye"></i></button></td>
                </tr>
                <tr>
                  <td><i data-lucide="file-text"></i> ICICI Lombard Motor.pdf</td>
                  <td>ICICI Lombard</td>
                  <td><span class="badge success">Verified</span></td>
                  <td><button class="icon-btn"><i data-lucide="eye"></i></button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>

      <!-- Chat Footer Composer -->
      <footer class="workspace-footer" id="workspaceFooter">
        <!-- Attachment preview bar -->
        <div class="attachment-preview-bar hidden" id="attachmentPreviewBar">
          <div class="attachment-preview-pill">
            <i data-lucide="file-text" class="file-icon"></i>
            <span class="attachment-file-name" id="attachmentFileName">policy.pdf</span>
            <button type="button" class="remove-attachment-btn" id="removeAttachmentBtn" title="Remove attachment">
              <i data-lucide="x"></i>
            </button>
          </div>
        </div>
        <form class="chat-composer" id="composerForm">
          <button type="button" class="composer-action-btn" id="attachmentBtn" title="Attach Policy PDF">
            <i data-lucide="paperclip" id="composerClipIcon"></i>
          </button>
          <input type="text" id="composerInput" placeholder="Ask CoverIndex AI..." autocomplete="off" />
          <button type="button" class="composer-action-btn mic-btn" title="Voice Search"><i data-lucide="mic"></i></button>
          <button type="submit" class="composer-send-btn" id="composerSendBtn"><i data-lucide="arrow-up"></i></button>
        </form>
        <div class="composer-subtext">50 messages left this hour - 500 left today</div>
      </footer>
    </main>

    <!-- Right Sidebar Drawer (Inspector) -->
    <aside class="app-inspector hidden" id="appInspector">
      <div class="inspector-header">
        <h3>Inspection Console</h3>
        <button class="icon-btn close-inspector-btn" id="closeInspectorBtn"><i data-lucide="x"></i></button>
      </div>

      <div class="inspector-tabs">
        <button class="inspector-tab active" data-inspector-tab="sources"><i data-lucide="file-check"></i> Sources</button>
        <button class="inspector-tab" data-inspector-tab="trace"><i data-lucide="route"></i> Routing Trace</button>
      </div>

      <div class="inspector-body">
        <div class="inspector-tab-content active" id="inspector-tab-sources">
          <div class="inspector-subtitle">GROUNDING DOCUMENTS</div>
          <div id="inspectorSourcesList">
            <div class="inspector-empty-state">
              <i data-lucide="file-question"></i>
              <p>No grounding sources analyzed. Ask a policy-related question to see citations.</p>
            </div>
          </div>
        </div>
        <div class="inspector-tab-content" id="inspector-tab-trace">
          <div class="inspector-subtitle">PIPELINE TRACE DETAILS</div>
          <div id="inspectorTraceTimeline">
            <div class="inspector-empty-state">
              <i data-lucide="network"></i>
              <p>Routing trace timeline will be visualised here.</p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  </div>

  <!-- Hidden inputs for file upload -->
  <input type="file" id="pdfFileInput" accept="application/pdf" style="display: none;" />

  <!-- Toast Notification Container -->
  <div class="toast-container" id="toastContainer"></div>

  <!-- Scripts -->
  <script src="/app.js?v=3"></script>
</body>
</html>
`;
const CSS = `/* ==========================================
   CoverIndex AI - Modern Web Stylesheet
   ========================================== */

:root {
  /* Color Palette matching Cover AI branding */
  --primary-purple: #4d37ec;
  --primary-purple-hover: #3b25cf;
  --primary-purple-light: rgba(77, 55, 236, 0.08);
  --primary-purple-border: rgba(77, 55, 236, 0.15);
  
  --bg-gradient-start: #0b0728;
  --bg-gradient-mid: #140d43;
  --bg-gradient-end: #291a75;
  
  --bg-app-canvas: #f8fafc;
  --bg-sidebar: #f8fafc;
  --border-color: #e2e8f0;
  
  --text-main: #0c1a30;
  --text-muted: #5a6e85;
  --text-white: #ffffff;
  --text-white-muted: #b0b8c6;
  
  --accent-blue: #3b82f6;
  --accent-purple: #8b5cf6;
  --accent-orange: #f97316;
  --accent-cyan: #06b6d4;
  --accent-pink: #ec4899;
  --accent-yellow: #eab308;
  
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 10px 30px rgba(0, 0, 0, 0.04);
  --shadow-lg: 0 20px 50px rgba(12, 26, 48, 0.08);
  
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  
  --font-main: 'Inter', system-ui, sans-serif;
  --font-title: 'Outfit', sans-serif;
  
  --transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  width: 100%;
  overflow-x: hidden;
  -webkit-text-size-adjust: 100%;
}

body {
  font-family: var(--font-main);
  color: var(--text-main);
  background-color: var(--bg-app-canvas);
  height: 100vh;
  height: 100dvh; /* Dynamic viewport for iOS Safari */
  width: 100%;
  overflow-x: hidden;
  overflow-y: hidden;
  line-height: 1.5;
}

.hidden {
  display: none !important;
}

.mobile-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(9, 18, 31, 0.42);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
  z-index: 90;
}

body.sidebar-open .mobile-backdrop,
body.inspector-open .mobile-backdrop {
  opacity: 1;
  pointer-events: auto;
}

@media (min-width: 769px) {
  .mobile-backdrop {
    display: none;
  }
}

/* ==========================================
   Screen 1: Landing Page Styles
   ========================================== */
.landing-page {
  display: grid;
  grid-template-columns: 1fr 1fr;
  height: 100vh;
  height: 100dvh;
  width: 100%;
  overflow: hidden;
}

/* Left Pane */
.landing-left {
  background: radial-gradient(circle at top left, var(--bg-gradient-end), var(--bg-gradient-mid)),
              linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-mid) 60%, var(--bg-gradient-end) 100%);
  color: var(--text-white);
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  overflow: hidden;
}

.landing-left::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(255, 255, 255, 0.15) 1px, transparent 1px);
  background-size: 24px 24px;
  opacity: 0.25;
  pointer-events: none;
}

.landing-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 10;
}

.brand-logo-icon {
  width: 32px;
  height: 32px;
  color: var(--primary-purple);
}

.landing-brand span {
  font-family: var(--font-title);
  font-weight: 800;
  font-size: 1.3rem;
  letter-spacing: 0.5px;
}

.landing-brand .brand-logo-icon {
  color: #a78bfa;
}

/* Mockup Card */
.mockup-card-container {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  z-index: 10;
}

.mockup-card {
  width: 100%;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: var(--radius-xl);
  padding: 24px;
  box-shadow: 0 30px 60px rgba(0, 0, 0, 0.35);
  animation: slideUp 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.mockup-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.mockup-icon-wrapper {
  background: rgba(255, 255, 255, 0.12);
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.mockup-icon-wrapper i {
  color: #c084fc;
  width: 22px;
  height: 22px;
}

.mockup-title {
  font-family: var(--font-title);
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-white);
}

.mockup-subtitle {
  font-size: 0.8rem;
  color: var(--text-white-muted);
}

.mockup-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 20px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.mockup-stat {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: var(--text-white-muted);
}

.stat-val {
  font-family: var(--font-title);
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text-white);
  margin-top: 4px;
}

.stat-val span {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-white-muted);
}

.mockup-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mockup-list-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.9rem;
  font-weight: 500;
}

.mockup-list-item i {
  width: 18px;
  height: 18px;
}

.mockup-list-item.checked {
  color: #34d399;
}

.mockup-list-item.yellow {
  color: #fbbf24;
}

.mockup-list-item.crossed {
  color: #f87171;
  text-decoration: line-through;
  opacity: 0.8;
}

.landing-left-footer {
  text-align: center;
  z-index: 10;
  margin-top: 20px;
}

.landing-left-footer h3 {
  font-family: var(--font-title);
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 6px;
}

.landing-left-footer p {
  color: var(--text-white-muted);
  font-size: 0.9rem;
  margin-bottom: 16px;
}

.slider-dots {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-bottom: 20px;
}

.slider-dots .dot {
  width: 6px;
  height: 6px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  cursor: pointer;
}

.slider-dots .dot.active {
  width: 18px;
  background-color: var(--text-white);
  border-radius: 4px;
}

.powered-by {
  font-size: 0.7rem;
  color: var(--text-white-muted);
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

/* Landing Right Pane */
.landing-right {
  background-color: var(--text-white);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 60px 40px;
  overflow-y: auto;
}

.landing-right-content {
  max-width: 480px;
  margin: auto;
  width: 100%;
}

.main-title {
  font-family: var(--font-title);
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--text-main);
  line-height: 1.2;
  letter-spacing: -0.5px;
  margin-bottom: 14px;
}

.main-title span {
  color: var(--primary-purple);
}

.main-subtitle {
  color: var(--text-muted);
  font-size: 1.05rem;
  line-height: 1.5;
  margin-bottom: 32px;
}

.action-grid-2x2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 30px;
}

.action-card-landing {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  transition: var(--transition);
  font-weight: 600;
  font-size: 0.95rem;
}

.action-card-landing:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 15px 35px rgba(77, 55, 236, 0.15);
  border-color: rgba(77, 55, 236, 0.3);
}

.icon-box {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-box.blue { background-color: rgba(59, 130, 246, 0.1); color: var(--accent-blue); }
.icon-box.purple { background-color: rgba(139, 92, 246, 0.1); color: var(--accent-purple); }
.icon-box.orange { background-color: rgba(249, 115, 22, 0.1); color: var(--accent-orange); }
.icon-box.cyan { background-color: rgba(6, 182, 212, 0.1); color: var(--accent-cyan); }

.primary-ask-btn {
  width: 100%;
  background-color: var(--primary-purple);
  color: white;
  border: none;
  padding: 16px;
  border-radius: var(--radius-md);
  font-family: var(--font-title);
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 10px 24px rgba(77, 55, 236, 0.25);
  transition: var(--transition);
  margin-bottom: 24px;
}

.primary-ask-btn:hover {
  background-color: var(--primary-purple-hover);
  transform: translateY(-1px);
  box-shadow: 0 12px 28px rgba(77, 55, 236, 0.35);
}

.agree-text {
  text-align: center;
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.signin-link {
  text-align: center;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-muted);
}

.signin-link span {
  color: var(--primary-purple);
  cursor: pointer;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.signin-link span i {
  width: 14px;
  height: 14px;
}

.landing-right-footer {
  display: flex;
  justify-content: center;
  gap: 20px;
  border-top: 1px solid var(--border-color);
  padding-top: 24px;
  margin-top: 40px;
}

.footer-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
  color: var(--text-muted);
  font-weight: 600;
}

.footer-badge i {
  color: #10b981;
  width: 16px;
  height: 16px;
}


/* ==========================================
   Screen 2 & 3: Chat Dashboard Layout
   ========================================== */
.app-dashboard {
  display: grid;
  grid-template-columns: 280px 1fr 0px; /* Right drawer starts closed */
  height: 100vh;
  height: 100dvh;
  width: 100%;
  overflow: hidden;
  transition: grid-template-columns 0.3s ease;
}

.app-dashboard.inspector-open {
  grid-template-columns: 280px 1fr 340px;
}

/* Sidebar Layout */
.app-sidebar {
  background-color: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
}

.sidebar-top {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex: 1;
}

.sidebar-brand {
  padding: 20px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sidebar-brand span {
  font-family: var(--font-title);
  font-weight: 800;
  font-size: 1.25rem;
  color: var(--text-main);
  flex: 1;
  margin-left: 10px;
}

.nav-menu {
  padding: 0 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border-radius: var(--radius-md);
  color: var(--text-muted);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 600;
  transition: var(--transition);
  position: relative;
}

.nav-item:hover {
  background-color: rgba(77, 55, 236, 0.04);
  color: var(--text-main);
}

.nav-item.active {
  background-color: var(--primary-purple-light);
  color: var(--primary-purple);
}

.nav-icon {
  width: 18px;
  height: 18px;
}

.nav-badge {
  background-color: #3b82f6;
  color: white;
  font-size: 0.65rem;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: auto;
}

/* Chats Section list */
.chats-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 20px 10px;
}

.section-divider {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-white-muted);
  letter-spacing: 1px;
  margin-left: 14px;
  margin-bottom: 10px;
}

.chats-list {
  flex: 1;
  overflow-y: auto;
}

.chats-list::-webkit-scrollbar {
  width: 3px;
}
.chats-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

.no-chats-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-white-muted);
  padding: 30px 10px;
  text-align: center;
  gap: 8px;
}

.no-chats-placeholder i {
  width: 28px;
  height: 28px;
  stroke-width: 1.5;
}

.no-chats-placeholder span {
  font-size: 0.8rem;
  font-weight: 500;
}

.sidebar-chat-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  color: var(--text-main);
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 2px;
  transition: var(--transition);
}

.sidebar-chat-item:hover {
  background-color: rgba(15, 32, 56, 0.03);
}

.sidebar-chat-item.active {
  background-color: rgba(77, 55, 236, 0.05);
  color: var(--primary-purple);
}

.sidebar-chat-item i {
  width: 16px;
  height: 16px;
  color: var(--text-muted);
  flex-shrink: 0;
}

.sidebar-chat-item.active i {
  color: var(--primary-purple);
}

.chat-item-text {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-item-time {
  font-size: 0.7rem;
  color: var(--text-muted);
  white-space: nowrap;
}

.view-archived {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: var(--text-muted);
  text-decoration: none;
  font-weight: 600;
  margin-left: 14px;
  margin-top: 10px;
}

.view-archived i {
  width: 14px;
  height: 14px;
}

/* User profile footer */
.sidebar-user {
  padding: 14px;
  border-top: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: rgba(15, 32, 56, 0.015);
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar-guest {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background-color: var(--primary-purple);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 0.85rem;
}

.user-name {
  font-size: 0.85rem;
  font-weight: 700;
}

.user-tag {
  font-size: 0.72rem;
  color: var(--text-muted);
}

/* Main Workspace */
.app-workspace {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: white;
  min-width: 0;
}

.workspace-header {
  height: 64px;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: white;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.active-chat-title {
  font-size: 0.95rem;
  font-weight: 700;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.index-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
  background-color: var(--bg-app-canvas);
  padding: 5px 12px;
  border-radius: 20px;
  border: 1px solid var(--border-color);
}

.upload-badge-btn {
  background-color: var(--primary-purple-light);
  border: 1px dashed var(--primary-purple-border);
  color: var(--primary-purple);
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: var(--transition);
}

.upload-badge-btn:hover {
  background-color: var(--primary-purple);
  color: white;
}

.upload-badge-btn i {
  width: 14px;
  height: 14px;
}

/* Workspace body scroll */
.workspace-body {
  flex: 1;
  overflow-y: auto;
  position: relative;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.workspace-body::-webkit-scrollbar {
  width: 4px;
}
.workspace-body::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

/* Dashboard Welcome state (Screen 2) */
.welcome-screen {
  margin: auto;
  max-width: 800px;
  width: 100%;
  padding: 40px 24px;
  text-align: center;
  min-width: 0;
}

.welcome-greeting {
  font-family: var(--font-title);
  font-size: 2.2rem;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 40px;
}

.welcome-greeting span {
  color: var(--primary-purple);
  position: relative;
}

.welcome-grid-2x3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.welcome-card {
  background-color: white;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  text-align: left;
  cursor: pointer;
  transition: var(--transition);
}

.welcome-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: rgba(77, 55, 236, 0.15);
}

.welcome-card-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.welcome-card-icon.blue { background-color: rgba(59, 130, 246, 0.08); color: var(--accent-blue); }
.welcome-card-icon.purple { background-color: rgba(139, 92, 246, 0.08); color: var(--accent-purple); }
.welcome-card-icon.orange { background-color: rgba(249, 115, 22, 0.08); color: var(--accent-orange); }
.welcome-card-icon.yellow { background-color: rgba(234, 179, 8, 0.08); color: var(--accent-yellow); }
.welcome-card-icon.cyan { background-color: rgba(6, 182, 212, 0.08); color: var(--accent-cyan); }
.welcome-card-icon.pink { background-color: rgba(236, 72, 153, 0.08); color: var(--accent-pink); }

.welcome-card-icon i {
  width: 20px;
  height: 20px;
}

.welcome-card h4 {
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--text-main);
}

.welcome-card p {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-top: 2px;
}

/* Chat Feed Mode (Screen 3) */
.chat-feed-window {
  flex: 1;
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 30px 24px;
  min-width: 0;
}

.chat-history {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* Typography styles matching Screen 3 (raw margins, clean text, bold subheaders) */
.message-bubble-row {
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s ease-out;
}

.message-bubble-row.user {
  align-items: flex-end;
}

.message-bubble-row.assistant {
  align-items: flex-start;
}

/* User Message bubble badge */
.user-msg-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
  max-width: 85%;
}

.file-attachment-badge {
  background-color: var(--bg-app-canvas);
  border: 1px solid var(--border-color);
  padding: 8px 14px;
  border-radius: var(--radius-md);
  font-size: 0.82rem;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  box-shadow: var(--shadow-sm);
}

.file-attachment-badge i {
  color: var(--accent-red, #ef4444);
  width: 16px;
  height: 16px;
}

.file-attachment-badge span.badge-tag {
  background-color: black;
  color: white;
  font-size: 0.65rem;
  padding: 1px 4px;
  border-radius: 3px;
  font-weight: 800;
}

.user-bubble {
  background-color: var(--primary-purple);
  color: white;
  border-radius: var(--radius-lg);
  padding: 12px 18px;
  font-size: 0.95rem;
  line-height: 1.5;
  border-bottom-right-radius: 4px;
  box-shadow: 0 4px 12px rgba(77, 55, 236, 0.12);
}

/* Assistant Message Typography (Screen 3: raw, no bubble card!) */
.assistant-text-container {
  width: 100%;
  font-size: 0.98rem;
  color: #22252a;
  line-height: 1.75;
}

.assistant-text-container p {
  margin-bottom: 16px;
}

.assistant-text-container h4 {
  font-family: var(--font-title);
  font-size: 1.15rem;
  color: var(--text-main);
  margin: 24px 0 8px;
  font-weight: 700;
}

.assistant-text-container ul {
  list-style-type: none;
  margin-bottom: 16px;
}

.assistant-text-container li {
  margin-bottom: 12px;
  padding-left: 0px;
}

.assistant-text-container strong {
  color: var(--text-main);
  font-weight: 700;
}

.assistant-text-container blockquote {
  background-color: #fffbeb;
  border-left: 4px solid #f59e0b;
  padding: 12px 16px;
  border-radius: 6px;
  margin: 18px 0;
  font-size: 0.9rem;
  color: #b45309;
}

.assistant-text-container blockquote p {
  margin-bottom: 0;
}

/* Composer Footer */
.workspace-footer {
  padding: 12px 24px 20px;
  background-color: white;
  min-width: 0;
}

.chat-composer {
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app-canvas);
  border-radius: var(--radius-xl);
  padding: 6px 6px 6px 14px;
  display: flex;
  align-items: center;
  box-shadow: 0 8px 30px rgba(12, 26, 48, 0.03);
  transition: var(--transition);
}

.chat-composer:focus-within {
  border-color: rgba(77, 55, 236, 0.35);
  background-color: white;
  box-shadow: 0 8px 30px rgba(77, 55, 236, 0.08);
}

.composer-action-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
  flex-shrink: 0;
}

.composer-action-btn:hover {
  background-color: var(--border-color);
  color: var(--text-main);
}

.chat-composer input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.95rem;
  color: var(--text-main);
  padding: 8px 12px;
}

.composer-send-btn {
  background-color: var(--accent-blue);
  color: white;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
  flex-shrink: 0;
}

.composer-send-btn:hover {
  background-color: #2563eb;
  transform: scale(1.05);
}

.composer-send-btn i {
  width: 18px;
  height: 18px;
}

.composer-subtext {
  text-align: center;
  font-size: 0.72rem;
  color: var(--text-white-muted);
  margin-top: 8px;
  font-weight: 500;
}


/* ==========================================
   Right Inspector Drawer
   ========================================== */
.app-inspector {
  background-color: white;
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 20;
  min-width: 0;
}

.inspector-header {
  height: 64px;
  padding: 0 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.inspector-header h3 {
  font-size: 0.95rem;
  color: var(--text-main);
  font-family: var(--font-title);
  font-weight: 800;
}

.inspector-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-app-canvas);
}

.inspector-tab {
  border: none;
  background: none;
  padding: 12px;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-bottom: 2px solid transparent;
  transition: var(--transition);
}

.inspector-tab i {
  width: 14px;
  height: 14px;
}

.inspector-tab.active {
  color: var(--primary-purple);
  border-bottom-color: var(--primary-purple);
  background-color: white;
}

.inspector-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.inspector-tab-content {
  display: none;
  flex-direction: column;
}

.inspector-tab-content.active {
  display: flex;
}

.inspector-subtitle {
  font-size: 0.72rem;
  font-weight: 800;
  color: var(--text-white-muted);
  letter-spacing: 0.8px;
  margin-bottom: 14px;
}

.inspector-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--text-white-muted);
  padding: 40px 10px;
  gap: 12px;
}

.inspector-empty-state i {
  width: 36px;
  height: 36px;
  stroke-width: 1.5;
}

.inspector-empty-state p {
  font-size: 0.78rem;
  line-height: 1.5;
}

/* Timeline/Trace and Source card styles in Inspector drawer */
.timeline {
  padding-left: 14px;
  border-left: 2px solid var(--border-color);
  margin-left: 10px;
}

.timeline-item {
  position: relative;
  margin-bottom: 20px;
}

.timeline-marker {
  position: absolute;
  left: -21px;
  top: 3px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: var(--primary-purple);
  border: 2px solid white;
}

.timeline-title {
  font-size: 0.8rem;
  font-weight: 700;
}

.timeline-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
  background-color: var(--bg-app-canvas);
  border: 1px solid var(--border-color);
  padding: 6px 10px;
  border-radius: 6px;
  margin-top: 4px;
}

.source-card {
  background-color: var(--bg-app-canvas);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 14px;
  margin-bottom: 12px;
  transition: var(--transition);
  border-left: 3px solid #78909c;
}

.source-card.insurer-hdfc { border-left-color: var(--color-hdfc); }
.source-card.insurer-sbi { border-left-color: var(--color-sbi); }
.source-card.insurer-tata { border-left-color: var(--color-tata); }
.source-card.insurer-lic { border-left-color: var(--color-lic); }
.source-card.insurer-icici { border-left-color: var(--color-icici); }

.source-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.78rem;
  font-weight: 700;
  margin-bottom: 6px;
}

.source-title {
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.source-badge {
  color: var(--primary-purple);
  font-size: 0.7rem;
}

.source-snippet {
  font-size: 0.78rem;
  color: var(--text-muted);
  background: white;
  border: 1px solid var(--border-color);
  padding: 8px 10px;
  border-radius: 6px;
  max-height: 100px;
  overflow-y: auto;
  line-height: 1.5;
}

.source-footer {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
  color: var(--text-white-muted);
  margin-top: 6px;
  font-weight: 600;
}


/* Animations */
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.collapse-sidebar-btn, .header-menu-btn {
  display: none;
}


/* ==========================================
   Dashboard Views (Guide, Vault, Search, etc)
   ========================================== */
.view-screen {
  display: flex;
  flex-direction: column;
  padding: 30px 40px;
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
}

.view-screen.hidden {
  display: none !important;
}

.screen-header {
  margin-bottom: 30px;
}

.screen-header h2 {
  font-family: var(--font-title);
  font-size: 1.8rem;
  font-weight: 800;
  margin-bottom: 8px;
  color: var(--text-main);
}

.screen-header p {
  color: var(--text-muted);
  font-size: 0.95rem;
}

.screen-icon {
  width: 48px;
  height: 48px;
  background-color: var(--primary-purple-light);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  color: var(--primary-purple);
}

.screen-icon i {
  width: 24px;
  height: 24px;
}

/* Search Screen */
.search-bar-container {
  display: flex;
  align-items: center;
  background-color: white;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 14px 20px;
  margin-bottom: 30px;
  box-shadow: var(--shadow-sm);
  transition: var(--transition);
}
.search-bar-container:focus-within {
  border-color: var(--primary-purple);
  box-shadow: 0 4px 15px rgba(77, 55, 236, 0.1);
}
.search-bar-container i {
  color: var(--text-muted);
  margin-right: 12px;
}
.search-bar-container input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 1rem;
}
.empty-state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background-color: rgba(255, 255, 255, 0.5);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-lg);
  color: var(--text-muted);
  text-align: center;
}
.empty-state-card i {
  width: 48px;
  height: 48px;
  margin-bottom: 16px;
  color: var(--border-color);
}
.empty-state-card h3 {
  color: var(--text-main);
  margin-bottom: 8px;
}

/* Guide Grid */
.guide-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}
.guide-card {
  background-color: white;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  display: flex;
  flex-direction: column;
  transition: var(--transition);
}
.guide-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  border-color: rgba(77, 55, 236, 0.2);
}
.guide-icon {
  width: 40px;
  height: 40px;
  background-color: rgba(59, 130, 246, 0.1);
  color: var(--accent-blue);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}
.guide-card h3 {
  font-size: 1.1rem;
  margin-bottom: 10px;
}
.guide-card p {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 20px;
  flex: 1;
}
.guide-btn {
  background-color: var(--bg-app-canvas);
  color: var(--primary-purple);
  border: none;
  padding: 10px;
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);
}
.guide-btn:hover {
  background-color: var(--primary-purple-light);
}

/* Platform Features */
.feature-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.feature-item {
  display: flex;
  gap: 20px;
  background: white;
  padding: 24px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}
.feature-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--primary-purple), var(--accent-purple));
  color: white;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.feature-text h4 {
  font-size: 1.1rem;
  margin-bottom: 8px;
}
.feature-text p {
  color: var(--text-muted);
  font-size: 0.95rem;
}

/* Vault Table */
.vault-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}
.vault-stat {
  background: white;
  padding: 16px 20px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  flex: 1;
  display: flex;
  flex-direction: column;
}
.vault-stat span {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 4px;
}
.vault-stat strong {
  font-size: 1.5rem;
  font-family: var(--font-title);
}
.text-green { color: #10b981; }
.vault-table-container {
  background: white;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}
.vault-table {
  width: 100%;
  border-collapse: collapse;
}
.vault-table th, .vault-table td {
  padding: 16px 20px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
  font-size: 0.9rem;
}
.vault-table th {
  background-color: rgba(15, 32, 56, 0.02);
  font-weight: 600;
  color: var(--text-muted);
}
.vault-table tr:last-child td {
  border-bottom: none;
}
.vault-table td i {
  width: 16px;
  height: 16px;
  color: var(--text-muted);
  margin-right: 8px;
  vertical-align: middle;
}
.badge {
  padding: 4px 8px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}
.badge.success {
  background-color: #d1fae5;
  color: #065f46;
}

/* ==========================================
   Responsive Media Queries
   ========================================== */
@media (max-width: 900px) {
  .landing-page {
    grid-template-columns: 1fr;
    overflow-y: auto;
    height: auto;
    min-height: 100vh;
    min-height: 100dvh;
  }
  .landing-left {
    padding: 30px;
    height: auto;
    min-height: 480px;
  }
  .landing-right {
    padding: 40px 24px;
    height: auto;
  }
  .mockup-card {
    max-width: 340px;
  }
  .chat-composer input {
    font-size: 16px; /* Prevents iOS Safari auto-zoom */
  }
}

@media (max-width: 1100px) {
  .main-title {
    font-size: 2.2rem;
  }

  .landing-right {
    padding: 48px 28px;
  }

  .landing-left {
    padding: 32px 28px;
  }
}

@media (max-width: 768px) {
  .app-dashboard, .app-dashboard.inspector-open {
    grid-template-columns: 1fr;
  }
  
  .action-grid-2x2 {
    grid-template-columns: 1fr;
  }
  
  .app-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    height: 100dvh;
    width: min(86vw, 300px);
    z-index: 100;
    transform: translateX(-100%);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .app-sidebar.open {
    transform: translateX(0);
    box-shadow: 10px 0 30px rgba(0,0,0,0.15);
  }
  
  .collapse-sidebar-btn {
    display: flex;
  }
  
  .header-menu-btn {
    display: flex !important;
  }
  
  .welcome-grid-2x3 {
    grid-template-columns: 1fr;
  }
  
  .app-inspector {
    position: fixed;
    right: 0;
    top: 0;
    height: 100vh;
    height: 100dvh;
    width: min(88vw, 340px);
    z-index: 100;
    transform: translateX(100%);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .app-inspector.open {
    transform: translateX(0);
    box-shadow: -10px 0 30px rgba(0,0,0,0.15);
  }

  .workspace-header {
    height: auto;
    min-height: 64px;
    padding: 12px 16px;
    gap: 10px;
    flex-wrap: wrap;
  }

  .header-right {
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 8px;
  }

  .index-badge,
  .upload-badge-btn {
    font-size: 0.72rem;
    padding: 5px 10px;
  }

  .welcome-screen {
    padding: 28px 16px 36px;
  }

  .welcome-greeting {
    font-size: clamp(1.7rem, 7vw, 2.2rem);
    margin-bottom: 28px;
  }

  .chat-feed-window {
    padding: 22px 16px;
  }

  .workspace-footer {
    padding: 12px 16px 16px;
  }

  .attachment-preview-bar {
    padding-left: 12px;
    padding-right: 12px;
  }

  .attachment-preview-pill .attachment-file-name {
    max-width: 180px;
  }

  .toast-container {
    left: 12px;
    right: 12px;
    transform: none;
    bottom: 12px;
  }

  .toast {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 640px) {
  .landing-left,
  .landing-right {
    padding-left: 20px;
    padding-right: 20px;
  }

  .mockup-card {
    max-width: 100%;
  }

  .action-grid-2x2,
  .welcome-grid-2x3,
  .inspector-tabs,
  .inspector-metrics-grid,
  .guide-grid,
  .feature-list,
  .vault-stats {
    grid-template-columns: 1fr;
  }

  .vault-stats {
    flex-direction: column;
  }

  .landing-right-footer {
    flex-wrap: wrap;
    gap: 12px;
  }

  .header-left {
    min-width: 0;
    flex: 1;
  }

  .active-chat-title {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 100%;
  }

  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .index-badge {
    flex: 1 1 auto;
    justify-content: center;
  }

  .upload-badge-btn {
    flex: 1 1 auto;
    justify-content: center;
  }

  .workspace-body {
    min-height: 0;
  }

  .chat-history {
    gap: 18px;
  }

  .message-bubble-row,
  .assistant-text-container,
  .user-msg-container,
  .welcome-card,
  .guide-card,
  .feature-item,
  .vault-table-container {
    min-width: 0;
  }

  .user-msg-container {
    max-width: 100%;
  }

  .feature-item {
    flex-direction: column;
    gap: 12px;
  }

  .vault-stat {
    width: 100%;
  }

  .assistant-text-container {
    font-size: 0.94rem;
  }

  .user-bubble {
    font-size: 0.92rem;
  }

  .screen-header h2,
  .welcome-greeting {
    overflow-wrap: anywhere;
  }
}

@media (max-width: 480px) {
  body {
    height: auto;
    min-height: 100dvh;
    overflow-y: auto;
  }

  .landing-page,
  .app-dashboard {
    min-height: 100dvh;
    height: auto;
  }

  .landing-left {
    min-height: 420px;
    padding-top: 24px;
    padding-bottom: 24px;
  }

  .landing-brand span,
  .sidebar-brand span {
    font-size: 1.05rem;
  }

  .main-title {
    font-size: 1.95rem;
  }

  .main-subtitle {
    font-size: 0.98rem;
  }

  .primary-ask-btn {
    font-size: 1rem;
    padding: 14px 16px;
  }

  .workspace-header {
    padding: 10px 12px;
  }

  .workspace-body {
    padding-bottom: env(safe-area-inset-bottom);
  }

  .welcome-screen {
    padding: 22px 12px 28px;
  }

  .welcome-greeting {
    font-size: 1.55rem;
  }

  .welcome-card,
  .guide-card,
  .feature-item {
    padding: 14px;
  }

  .chat-feed-window {
    padding: 18px 12px 22px;
  }

  .workspace-footer {
    padding: 10px 12px 14px;
  }

  .chat-composer {
    padding: 6px 6px 6px 10px;
  }

  .chat-composer input {
    font-size: 16px;
    min-width: 0;
  }

  .composer-send-btn,
  .composer-action-btn {
    width: 34px;
    height: 34px;
  }

  .attachment-preview-pill .attachment-file-name {
    max-width: 140px;
  }

  .vault-table-container {
    overflow-x: auto;
  }
}

/* Staged Attachment Preview Bar */
.attachment-preview-bar {
  display: flex;
  padding: 8px 16px 2px 16px;
  background-color: transparent;
  width: 100%;
}

.attachment-preview-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: var(--primary-purple-light);
  border: 1px solid var(--primary-purple-border);
  padding: 6px 12px;
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  color: var(--primary-purple);
  font-weight: 600;
  max-width: 100%;
}

.attachment-preview-pill .file-icon {
  width: 16px;
  height: 16px;
}

.attachment-preview-pill .attachment-file-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 240px;
}

.remove-attachment-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2px;
  border-radius: 50%;
  transition: var(--transition);
}

.remove-attachment-btn:hover {
  background-color: rgba(77, 55, 236, 0.15);
  color: var(--primary-purple);
}

.remove-attachment-btn i {
  width: 14px;
  height: 14px;
}

/* ==========================================
   Toast Notification System
   ========================================== */
.toast-container {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 9999;
  pointer-events: none;
}

.toast {
  background-color: var(--text-main);
  color: white;
  padding: 12px 20px;
  border-radius: 30px;
  font-size: 0.85rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  animation: toastSlideUp 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  pointer-events: auto;
}

.toast i {
  width: 16px;
  height: 16px;
  color: var(--primary-purple-light);
}

.toast.fade-out {
  animation: toastFadeOut 0.3s ease forwards;
}

@keyframes toastSlideUp {
  from { opacity: 0; transform: translateY(20px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes toastFadeOut {
  from { opacity: 1; transform: translateY(0) scale(1); }
  to { opacity: 0; transform: translateY(10px) scale(0.95); }
}
`;
const APP_JS = `/* ==========================================
   CoverIndex AI - Frontend Application Logic
   ========================================== */

// Configure this to point to your Render backend URL once deployed.
// For local development, leave it as empty string to use relative paths.
const API_BASE_URL = "https://coverindex-ai.onrender.com";

// Typing animation items
const typingSentences = [
  "renew a policy?",
  "get insurance quotes?",
  "file a claim?",
  "scan your policy PDF?",
  "verify your coverage?"
];

let typingIndex = 0;
let sentenceIndex = 0;
let isDeleting = false;
let typingSpeed = 100;
let activeSessionName = "New Chat";
let activeChatHistory = [];
let hasMessages = false;
let uploadedFiles = [];
let stagedAttachment = null;
let indexedPolicies = [];

// DOM Elements
const landingPage = document.getElementById("landingPage");
const appDashboard = document.getElementById("appDashboard");
const workspaceBody = document.getElementById("workspaceBody");
const welcomeScreen = document.getElementById("welcomeScreen");
const chatFeedWindow = document.getElementById("chatFeedWindow");
const chatHistory = document.getElementById("chatHistory");
const chatSessionTitle = document.getElementById("chatSessionTitle");
const composerInput = document.getElementById("composerInput");
const composerForm = document.getElementById("composerForm");
const composerSendBtn = document.getElementById("composerSendBtn");
const attachmentBtn = document.getElementById("attachmentBtn");
const pdfFileInput = document.getElementById("pdfFileInput");
const composerClipIcon = document.getElementById("composerClipIcon");
const btnNewChat = document.getElementById("btnNavNewChat");
const chatsList = document.getElementById("chatsList");
const statusText = document.getElementById("statusText");
const attachmentPreviewBar = document.getElementById("attachmentPreviewBar");
const attachmentFileName = document.getElementById("attachmentFileName");
const removeAttachmentBtn = document.getElementById("removeAttachmentBtn");


// Inspector
const appInspector = document.getElementById("appInspector");
const btnToggleInspector = document.getElementById("btnToggleInspector");
const closeInspectorBtn = document.getElementById("closeInspectorBtn");
const inspectorSourcesList = document.getElementById("inspectorSourcesList");
const inspectorTraceTimeline = document.getElementById("inspectorTraceTimeline");

// Mobile Sidebar
const mobileMenuBtn = document.getElementById("mobileMenuBtn");
const sidebar = document.querySelector(".app-sidebar");
const collapseSidebarBtn = document.getElementById("collapseSidebarBtn");
const mobileBackdrop = document.getElementById("mobileBackdrop");

// Toasts
const toastContainer = document.getElementById("toastContainer");

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Lucide Icons
  if (window.lucide) {
    lucide.createIcons();
  }
  
  // Start typing greeting animation
  typeGreeting();
  setupEventListeners();
  loadIndexStatus();
  loadIndexedPolicies();
  syncMobileOverlays();
});

// Typing greeting text effect
function typeGreeting() {
  const target = document.getElementById("typingTarget");
  if (!target) return;

  const currentSentence = typingSentences[sentenceIndex];
  
  if (isDeleting) {
    target.textContent = currentSentence.substring(0, typingIndex - 1);
    typingIndex--;
    typingSpeed = 50;
  } else {
    target.textContent = currentSentence.substring(0, typingIndex + 1);
    typingIndex++;
    typingSpeed = 100;
  }

  if (!isDeleting && typingIndex === currentSentence.length) {
    isDeleting = true;
    typingSpeed = 1500; // Pause at end of sentence
  } else if (isDeleting && typingIndex === 0) {
    isDeleting = false;
    sentenceIndex = (sentenceIndex + 1) % typingSentences.length;
    typingSpeed = 500; // Pause before typing next
  }

  setTimeout(typeGreeting, typingSpeed);
}

// Navigation between Landing and Dashboard
function enterDashboard(mode = "") {
  landingPage.classList.add("hidden");
  appDashboard.classList.remove("hidden");
  
  // Switch layouts in app.js
  if (window.lucide) {
    lucide.createIcons();
  }

  // Pre-fill search inputs based on mode chosen
  if (mode === "quotes") {
    composerInput.value = "Show me commercial vehicle package policy quotes.";
    composerInput.focus();
  } else if (mode === "scan") {
    triggerUpload();
  } else if (mode === "renew") {
    composerInput.value = "I want to renew my Arogya Sanjeevani policy.";
    composerInput.focus();
  } else if (mode === "ask") {
    composerInput.value = "What is term insurance and how is it different from unit-linked insurance?";
    composerInput.focus();
  }
}

// Check index status
async function loadIndexStatus() {
  try {
    const response = await fetch(\`\${API_BASE_URL}/api/status\`);
    const payload = await response.json();
    if (payload.ready) {
      statusText.textContent = \`\${payload.page_count} pages indexed\`;
    }
  } catch (e) {
    statusText.textContent = "Offline";
  }
}

// Load pre-indexed policies list
async function loadIndexedPolicies() {
  try {
    const response = await fetch(\`\${API_BASE_URL}/api/policies\`);
    const payload = await response.json();
    if (payload.policies) {
      indexedPolicies = payload.policies.map(p => p.file_name.toLowerCase());
      populateVaultTable(payload.policies);
    }
  } catch (e) {
    console.error("Failed to load indexed policies:", e);
  }
}

// Populate Insurance Vault Table
function populateVaultTable(policies) {
  const tbody = document.getElementById("vaultTableBody");
  if (!tbody) return;
  
  // Clear hardcoded rows
  tbody.innerHTML = "";
  
  if (policies.length === 0) {
    tbody.innerHTML = \`<tr><td colspan="4" style="text-align:center; color:var(--text-muted)">No policies indexed yet. Upload one to get started!</td></tr>\`;
    return;
  }

  policies.forEach(policy => {
    // Guess insurer from filename
    let insurer = "General";
    const lowName = policy.file_name.toLowerCase();
    if (lowName.includes("hdfc")) insurer = "HDFC Ergo";
    else if (lowName.includes("sbi")) insurer = "SBI General";
    else if (lowName.includes("icici")) insurer = "ICICI Lombard";
    else if (lowName.includes("tata")) insurer = "Tata AIG";
    else if (lowName.includes("lic")) insurer = "LIC India";

    const tr = document.createElement("tr");
    tr.innerHTML = \`
      <td><i data-lucide="file-text"></i> \${policy.file_name}</td>
      <td>\${insurer}</td>
      <td><span class="badge success">Verified</span></td>
      <td><button class="icon-btn" onclick="triggerPreset('ask', 'Summarize \${policy.file_name}')" title="Analyze Policy"><i data-lucide="message-square"></i></button></td>
    \`;
    tbody.appendChild(tr);
  });
  
  if (window.lucide) lucide.createIcons();
}

// Attach Event Listeners
function setupEventListeners() {
  // New chat button
  btnNewChat.addEventListener("click", (e) => {
    e.preventDefault();
    resetChatWorkspace();
  });

  // Toggles right inspector drawer
  btnToggleInspector.addEventListener("click", () => {
    appDashboard.classList.toggle("inspector-open");
    appInspector.classList.toggle("hidden");
    syncMobileOverlays();
  });

  closeInspectorBtn.addEventListener("click", () => {
    appDashboard.classList.remove("inspector-open");
    appInspector.classList.add("hidden");
    syncMobileOverlays();
  });

  // Mobile menu toggle
  mobileMenuBtn.addEventListener("click", () => {
    sidebar.classList.toggle("open");
    syncMobileOverlays();
  });
  
  collapseSidebarBtn.addEventListener("click", () => {
    sidebar.classList.remove("open");
    syncMobileOverlays();
  });

  if (mobileBackdrop) {
    mobileBackdrop.addEventListener("click", () => {
      sidebar.classList.remove("open");
      appDashboard.classList.remove("inspector-open");
      appInspector.classList.add("hidden");
      syncMobileOverlays();
    });
  }

  // Navigation View Switching
  const navBtns = {
    "btnNavNewChat": "welcomeScreen",
    "btnNavSearch": "searchChatsScreen",
    "btnNavGuide": "insuranceGuideScreen",
    "btnNavPlatform": "platformGuideScreen",
    "btnNavVault": "insuranceVaultScreen"
  };

  Object.keys(navBtns).forEach(btnId => {
    const btn = document.getElementById(btnId);
    if (btn) {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        
        // Handle "New Chat" special case when active chat exists
        if (btnId === "btnNavNewChat" && hasMessages) {
          resetChatWorkspace();
          return;
        }

        // Update Active State
        document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
        btn.classList.add("active");

        // Switch View
        switchWorkspaceView(navBtns[btnId]);
        
        // Close sidebar on mobile
        if (window.innerWidth <= 768) {
          sidebar.classList.remove("open");
          syncMobileOverlays();
        }
      });
    }
  });

  const viewArchivedBtn = document.querySelector(".view-archived");
  if (viewArchivedBtn) {
    viewArchivedBtn.addEventListener("click", (e) => {
      e.preventDefault();
      showToast("Archived chats will be available in the next update.", "archive");
    });
  }

  // Upload actions
  attachmentBtn.addEventListener("click", () => {
    pdfFileInput.click();
  });

  const headerUploadBtn = document.getElementById("headerUploadBtn");
  if (headerUploadBtn) {
    headerUploadBtn.addEventListener("click", triggerUpload);
  }

  pdfFileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
      stagedAttachment = file;
      attachmentFileName.textContent = file.name;
      attachmentPreviewBar.classList.remove("hidden");
      if (!composerInput.value.trim()) {
        composerInput.value = "Please analyze this policy document and summarize the key benefits and exclusions.";
        composerInput.focus();
      }
    }
  });

  removeAttachmentBtn.addEventListener("click", () => {
    clearStagedAttachment();
  });

  // Composer submission
  composerForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = composerInput.value.trim();
    if (!query) return;
    submitQuery(query);
  });

  // Inspector Tabs
  const inspectorTabs = document.querySelectorAll(".inspector-tab");
  inspectorTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      inspectorTabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".inspector-tab-content").forEach(c => c.classList.remove("active"));
      
      tab.classList.add("active");
      const contentId = \`inspector-tab-\${tab.dataset.inspectorTab}\`;
      document.getElementById(contentId).classList.add("active");
    });
  });
}

// Clear staged attachment helper
function clearStagedAttachment() {
  stagedAttachment = null;
  attachmentPreviewBar.classList.add("hidden");
  pdfFileInput.value = "";
}

function syncMobileOverlays() {
  document.body.classList.toggle("sidebar-open", sidebar.classList.contains("open"));
  document.body.classList.toggle("inspector-open", appDashboard.classList.contains("inspector-open"));
}

// Toast System
function showToast(message, iconName = "bell") {
  const toast = document.createElement("div");
  toast.className = "toast";
  
  const icon = document.createElement("i");
  icon.setAttribute("data-lucide", iconName);
  
  const text = document.createElement("span");
  text.textContent = message;
  
  toast.appendChild(icon);
  toast.appendChild(text);
  toastContainer.appendChild(toast);
  
  if (window.lucide) lucide.createIcons();
  
  setTimeout(() => {
    toast.classList.add("fade-out");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Switch main workspace views
function switchWorkspaceView(viewId) {
  // Hide all view screens
  document.querySelectorAll(".view-screen").forEach(screen => {
    screen.classList.add("hidden");
  });
  
  // Ensure welcome screen is hidden unless explicitly requested
  if (viewId !== "welcomeScreen") {
    welcomeScreen.classList.add("hidden");
  } else if (!hasMessages) {
    welcomeScreen.classList.remove("hidden");
  }

  // Show target view
  const target = document.getElementById(viewId);
  if (target) {
    target.classList.remove("hidden");
  }

  // Toggle Chat Composer Footer
  const footer = document.getElementById("workspaceFooter");
  if (footer) {
    if (viewId === "welcomeScreen" || viewId === "chatFeedWindow") {
      footer.classList.remove("hidden");
    } else {
      footer.classList.add("hidden");
    }
  }
  
  if (window.lucide) lucide.createIcons();
}

// Reset workspace to welcome page
function resetChatWorkspace() {
  switchWorkspaceView("welcomeScreen");
  chatHistory.innerHTML = "";
  composerInput.value = "";
  chatSessionTitle.textContent = "New Chat";
  activeSessionName = "New Chat";
  hasMessages = false;
  clearStagedAttachment();
  
  // Update Nav
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  const btnNewChat = document.getElementById("btnNavNewChat");
  if (btnNewChat) btnNewChat.classList.add("active");
  
  // Set clip icon back to paperclip
  composerClipIcon.setAttribute("data-lucide", "paperclip");
  if (window.lucide) lucide.createIcons();
}


// Trigger upload file picker
function triggerUpload() {
  pdfFileInput.click();
}

// Trigger welcome card action presets
function triggerPreset(type, customQuery = null) {
  // Always switch to chat view
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  const btnNewChat = document.getElementById("btnNavNewChat");
  if (btnNewChat) btnNewChat.classList.add("active");
  switchWorkspaceView("chatFeedWindow");
  
  if (customQuery) {
    composerInput.value = customQuery;
    composerInput.focus();
    submitQuery(customQuery);
    return;
  }

  if (type === "quotes") {
    composerInput.value = "What is the premium rate for Commercial Vehicle package policies?";
  } else if (type === "renew") {
    composerInput.value = "Explain the policy renewal grace period terms.";
  } else if (type === "vault") {
    const btnNavVault = document.getElementById("btnNavVault");
    if (btnNavVault) btnNavVault.click();
    return;
  } else if (type === "claim") {
    composerInput.value = "What documents are required to file a death benefit claim?";
  } else if (type === "ask") {
    composerInput.value = "What are the standard exclusions under the Bharat Griha Raksha policy?";
  }
  composerInput.focus();
}

// Upload PDF to backend
async function uploadPdfFile(file) {
  // Switch views
  welcomeScreen.classList.add("hidden");
  chatFeedWindow.classList.remove("hidden");
  
  // Render user document attachment message
  const userMsgId = addMessage("user", \`Please review this insurance policy document.\`, file.name);
  
  // Render loading assistant state
  const loadingMsgId = addMessage("assistant", \`### Indexing & Analysis in progress...\nUploading and parsing **\${file.name}** to CoverIndex AI. Reading pages and extracts...\`);
  
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(\`\${API_BASE_URL}/api/upload\`, {
      method: "POST",
      body: formData
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Failed to upload file");
    }

    // Success! Update loading bubble with file summary
    updateMessage(loadingMsgId, \`### Indexing Successful! 🎉\nIt looks like you've uploaded a policy document for the **\${file.name}**. I have successfully parsed and indexed **\${payload.page_count} pages** into CoverIndex AI in-memory. \n\nYou can now ask me any specific questions about coverage details, exclusions, premium grace periods, or claims guidelines and I will retrieve the answers directly from this file!\`);
    
    // Add file to uploaded session files
    uploadedFiles.push(file.name);
    loadIndexStatus();
    createChatSessionItem(file.name);
  } catch (error) {
    updateMessage(loadingMsgId, \`### Upload Failed\nCould not index policy document: **\${error.message}**.\n\nPlease verify that your server is running and the file is a valid PDF.\`);
  }
}

// Add chat session item under CHATS sidebar
function createChatSessionItem(fileName) {
  // Clear placeholder if first chat
  const placeholder = chatsList.querySelector(".no-chats-placeholder");
  if (placeholder) {
    chatsList.removeChild(placeholder);
  }

  // Create chat item
  const item = document.createElement("div");
  item.className = "sidebar-chat-item active";
  item.addEventListener("click", () => {
    // Keep active
    document.querySelectorAll(".sidebar-chat-item").forEach(i => i.classList.remove("active"));
    item.classList.add("active");
  });

  const icon = document.createElement("i");
  icon.setAttribute("data-lucide", "message-square");

  const nameDiv = document.createElement("div");
  nameDiv.className = "chat-item-text";
  nameDiv.textContent = \`Review: \${fileName}\`;
  chatSessionTitle.textContent = \`Review: \${fileName}\`;

  const timeDiv = document.createElement("div");
  timeDiv.className = "chat-item-time";
  timeDiv.textContent = "0 min ago";

  item.appendChild(icon);
  item.appendChild(nameDiv);
  item.appendChild(timeDiv);
  chatsList.prepend(item);

  if (window.lucide) lucide.createIcons();
}

// Add new messages to feed
let messageCounter = 0;
function addMessage(role, text, attachedFileName = null) {
  messageCounter++;
  const msgId = \`msg-\${messageCounter}\`;

  switchWorkspaceView("chatFeedWindow");
  hasMessages = true;

  const msgRow = document.createElement("div");
  msgRow.className = \`message-bubble-row \${role}\`;
  msgRow.id = msgId;

  if (role === "user") {
    const userContainer = document.createElement("div");
    userContainer.className = "user-msg-container";

    if (attachedFileName) {
      const badge = document.createElement("div");
      badge.className = "file-attachment-badge";
      
      const fileIcon = document.createElement("i");
      fileIcon.setAttribute("data-lucide", "file-text");
      
      const fileNameSpan = document.createElement("span");
      fileNameSpan.textContent = attachedFileName;
      
      const formatTag = document.createElement("span");
      formatTag.className = "badge-tag";
      formatTag.textContent = "PDF";

      badge.appendChild(fileIcon);
      badge.appendChild(fileNameSpan);
      badge.appendChild(formatTag);
      userContainer.appendChild(badge);
    }

    const bubble = document.createElement("div");
    bubble.className = "user-bubble";
    bubble.textContent = text;
    userContainer.appendChild(bubble);
    msgRow.appendChild(userContainer);
  } else {
    // Assistant message: raw typography (Screen 3)
    const assistantContainer = document.createElement("div");
    assistantContainer.className = "assistant-text-container";
    assistantContainer.innerHTML = parseMarkdown(text);
    msgRow.appendChild(assistantContainer);
  }

  chatHistory.appendChild(msgRow);
  
  // Auto-scroll chat body
  workspaceBody.scrollTop = workspaceBody.scrollHeight;
  if (window.lucide) lucide.createIcons();
  
  return msgId;
}

// Update existing assistant message bubble (for uploads)
function updateMessage(msgId, text) {
  const msgRow = document.getElementById(msgId);
  if (msgRow) {
    const container = msgRow.querySelector(".assistant-text-container");
    if (container) {
      container.innerHTML = parseMarkdown(text);
    }
  }
}

// Markdown formatting for assistant text
function parseMarkdown(text) {
  let html = text;

  // Escape HTML tags to prevent XSS
  html = html
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Format headers (### Header)
  html = html.replace(/^### (.*?)$/gm, '<h4 style="font-family:\'Outfit\',sans-serif; font-size:1.15rem; color:var(--text-main); margin:20px 0 8px; font-weight:700;">$1</h4>');
  
  // Format Bold (**text**)
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // Format bullet lists (- item)
  html = html.replace(/^\- (.*?)$/gm, '<li style="margin-left:14px; margin-bottom:8px; list-style-type:circle; padding-left:4px;">$1</li>');

  // Convert blockquote alerts (> [!WARNING] or > [!NOTE])
  html = html.replace(/&gt;\s*\[\!WARNING\]\s*\n&gt;\s*(.*?)$/gm, '<blockquote style="background-color:#fff7ed; border-left:4px solid #f97316; padding:12px 16px; border-radius:6px; margin:14px 0; color:#c2410c; font-size:0.88rem;"><p>$1</p></blockquote>');
  html = html.replace(/&gt;\s*\[\!NOTE\]\s*\n&gt;\s*(.*?)$/gm, '<blockquote style="background-color:#f0fdf4; border-left:4px solid #22c55e; padding:12px 16px; border-radius:6px; margin:14px 0; color:#15803d; font-size:0.88rem;"><p>$1</p></blockquote>');
  html = html.replace(/&gt;\s*(.*?)$/gm, '<blockquote style="background-color:var(--bg-app-canvas); border-left:4px solid var(--text-muted); padding:10px 14px; border-radius:4px; margin:10px 0; font-size:0.88rem;"><p>$1</p></blockquote>');

  // Grounding Citation Badges (e.g. [policy_bond.pdf p. 4])
  const citationRegex = /\[([^\]]+?\.(?:pdf|zip|txt))\s+p\s*[-–]?\s*(\d+)\]/gi;
  html = html.replace(citationRegex, (match, filename, page) => {
    const citationId = \`\${filename} p. \${page}\`;
    const truncatedText = filename.length > 25 ? filename.slice(0, 22) + "..." : filename;
    return \`<span class="citation-link" onclick="highlightSource('\${citationId}')" title="Click to inspect source text">\${truncatedText} p. \${page}</span>\`;
  });

  return html;
}

// Client query submission
async function submitQuery(query) {
  // Set composer disabled/loading
  composerInput.disabled = true;
  composerSendBtn.disabled = true;
  composerSendBtn.innerHTML = \`<i data-lucide="loader" class="spin"></i>\`;
  if (window.lucide) lucide.createIcons();

  const fileToUpload = stagedAttachment;
  let fileUploadedName = null;
  let loadingId = null;

  if (fileToUpload) {
    clearStagedAttachment();
    
    const isAlreadyIndexed = indexedPolicies.includes(fileToUpload.name.toLowerCase());
    
    if (!hasMessages) {
      activeSessionName = \`Review: \${fileToUpload.name}\`;
      chatSessionTitle.textContent = activeSessionName;
      createChatSessionItem(fileToUpload.name);
    }
    addMessage("user", query, fileToUpload.name);
    
    if (isAlreadyIndexed) {
      // Document is already indexed, bypass upload completely
      loadingId = addMessage("assistant", \`Thinking...\`);
      fileUploadedName = fileToUpload.name;
    } else {
      // Upload and index new document
      loadingId = addMessage("assistant", \`### Uploading & Indexing... \nUploading and parsing **\${fileToUpload.name}** to CoverIndex AI. Reading pages and extracts...\`);
      
      const formData = new FormData();
      formData.append("file", fileToUpload);
      
      try {
        const uploadResponse = await fetch(\`\${API_BASE_URL}/api/upload\`, {
          method: "POST",
          body: formData
        });
        const uploadPayload = await uploadResponse.json();
        if (!uploadResponse.ok) {
          throw new Error(uploadPayload.error || "Failed to upload file");
        }
        
        // Update loading bubble to query status
        updateMessage(loadingId, \`### Analyzing Document...\nDocument **\${fileToUpload.name}** uploaded successfully. Running query: "\${query}"...\`);
        fileUploadedName = uploadPayload.filename || fileToUpload.name;
        uploadedFiles.push(fileUploadedName);
        loadIndexStatus();
      } catch (uploadError) {
        updateMessage(loadingId, \`### Upload Failed\nCould not index policy document: **\${uploadError.message}**.\`);
        // Reset composer
        composerInput.disabled = false;
        composerSendBtn.disabled = false;
        composerSendBtn.innerHTML = \`<i data-lucide="arrow-up"></i>\`;
        if (window.lucide) lucide.createIcons();
        return;
      }
    }
  } else {
    // Normal message flow
    if (!hasMessages) {
      createChatSessionItem(query.slice(0, 26) + "...");
    }
    addMessage("user", query);
    loadingId = addMessage("assistant", \`Thinking...\`);
  }

  // Now query /api/ask
  try {
    let askFileName = fileUploadedName;
    if (!askFileName && activeSessionName.startsWith("Review: ")) {
      askFileName = activeSessionName.replace("Review: ", "");
    }

    const response = await fetch(\`\${API_BASE_URL}/api/ask\`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, file_name: askFileName })
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Query failed");
    }

    // Render answer
    updateMessage(loadingId, payload.answer);
    
    // Add routing info trace to loading bubble footer if active
    if (payload.route || payload.confidence) {
      appendMetadataFooter(loadingId, payload.route, payload.confidence);
    }

    // Populate Inspector panel
    renderSources(payload.sources);
    renderRouteTrace(payload.route, payload.trace);

    // Auto-open sources tab in desktop if sources exist
    if (window.innerWidth >= 900 && payload.sources && payload.sources.length > 0) {
      appDashboard.classList.add("inspector-open");
      appInspector.classList.remove("hidden");
    }
  } catch (error) {
    updateMessage(loadingId, \`### Error Encountered\nCould not fetch response: **\${error.message}**.\nPlease check your python backend is running.\`);
  } finally {
    composerInput.disabled = false;
    composerSendBtn.disabled = false;
    composerSendBtn.innerHTML = \`<i data-lucide="arrow-up"></i>\`;

    composerInput.value = "";
    composerInput.focus();
    if (window.lucide) lucide.createIcons();
  }
}

// Render metadata tags below assistant text
function appendMetadataFooter(msgId, route, confidence) {
  const msgRow = document.getElementById(msgId);
  if (!msgRow) return;

  const footer = document.createElement("div");
  footer.className = "message-meta";
  footer.style.marginTop = "10px";
  footer.style.display = "flex";
  footer.style.gap = "8px";
  footer.style.fontSize = "0.76rem";
  footer.style.color = "var(--text-muted)";

  if (route && route.insurer) {
    const insurerTag = document.createElement("span");
    insurerTag.className = "tag routed";
    insurerTag.textContent = \`Insurer: \${route.insurer}\`;
    footer.appendChild(insurerTag);
  }
  
  if (route && route.intent && route.intent !== "general") {
    const intentTag = document.createElement("span");
    intentTag.className = "tag routed";
    intentTag.textContent = \`Category: \${route.intent}\`;
    footer.appendChild(intentTag);
  }

  if (confidence > 0) {
    const confTag = document.createElement("span");
    confTag.className = "tag grounded";
    confTag.textContent = \`\${(confidence * 100).toFixed(0)}% grounded\`;
    footer.appendChild(confTag);
  } else {
    const confTag = document.createElement("span");
    confTag.className = "tag routed";
    confTag.style.borderColor = "rgba(249, 115, 22, 0.25)";
    confTag.style.backgroundColor = "rgba(249, 115, 22, 0.08)";
    confTag.style.color = "#ea580c";
    confTag.textContent = \`General LLM Mode\`;
    footer.appendChild(confTag);
  }

  const container = msgRow.querySelector(".assistant-text-container");
  if (container) {
    container.appendChild(footer);
  }
}

// Render grounding sources in right sidebar
function renderSources(sources) {
  if (!sources || !sources.length) {
    inspectorSourcesList.innerHTML = \`
      <div class="inspector-empty-state">
        <i data-lucide="file-question"></i>
        <p>No grounding sources were utilized for this response.</p>
      </div>\`;
    if (window.lucide) lucide.createIcons();
    return;
  }

  inspectorSourcesList.innerHTML = "";
  sources.forEach(src => {
    const card = document.createElement("div");
    card.className = \`source-card \${getInsurerClass(src.insurer)}\`;
    card.id = \`src-\${src.citation.replace(/[\s\.]/g, "-")}\`;

    const header = document.createElement("div");
    header.className = "source-header";

    const title = document.createElement("span");
    title.className = "source-title";
    title.textContent = src.citation;

    const badge = document.createElement("span");
    badge.className = "source-badge";
    badge.textContent = src.insurer;

    header.appendChild(title);
    header.appendChild(badge);

    const snippet = document.createElement("div");
    snippet.className = "source-snippet";
    snippet.innerHTML = src.snippet;

    const footer = document.createElement("div");
    footer.className = "source-footer";

    const product = document.createElement("span");
    product.textContent = src.product;

    const score = document.createElement("span");
    score.textContent = \`Score: \${src.score}\`;

    footer.appendChild(product);
    footer.appendChild(score);

    card.appendChild(header);
    card.appendChild(snippet);
    card.appendChild(footer);
    inspectorSourcesList.appendChild(card);
  });
  
  if (window.lucide) lucide.createIcons();
}

// Timeline trace of agent routing in right sidebar
function renderRouteTrace(route, trace) {
  if (!trace || !trace.length) {
    inspectorTraceTimeline.innerHTML = \`
      <div class="inspector-empty-state">
        <i data-lucide="network"></i>
        <p>Trace log details not available.</p>
      </div>\`;
    if (window.lucide) lucide.createIcons();
    return;
  }

  inspectorTraceTimeline.innerHTML = "";
  
  const timeline = document.createElement("div");
  timeline.className = "timeline";

  trace.forEach((step, idx) => {
    const item = document.createElement("div");
    item.className = "timeline-item";

    const marker = document.createElement("div");
    marker.className = "timeline-marker";

    const title = document.createElement("div");
    title.className = "timeline-title";
    
    const colonIdx = step.indexOf(":");
    let stepTitle = \`Step \${idx + 1}\`;
    let stepDesc = step;
    
    if (colonIdx !== -1) {
      stepTitle = step.slice(0, colonIdx);
      stepDesc = step.slice(colonIdx + 1).trim();
    }

    title.textContent = stepTitle;

    const desc = document.createElement("div");
    desc.className = "timeline-desc";
    desc.textContent = stepDesc;

    item.appendChild(marker);
    item.appendChild(title);
    item.appendChild(desc);
    timeline.appendChild(item);
  });

  inspectorTraceTimeline.appendChild(timeline);
  if (window.lucide) lucide.createIcons();
}

// Click citation in assistant feed -> focus and scroll in inspector card
function highlightSource(citationId) {
  // Open inspector if closed
  appDashboard.classList.add("inspector-open");
  appInspector.classList.remove("hidden");

  // Set active tab to sources
  const srcTabBtn = document.querySelector('.inspector-tab[data-inspector-tab="sources"]');
  if (srcTabBtn) srcTabBtn.click();

  const targetId = \`src-\${citationId.replace(/[\s\.]/g, "-")}\`;
  const card = document.getElementById(targetId);
  if (card) {
    card.scrollIntoView({ behavior: "smooth", block: "center" });

    // Flash background
    card.style.transition = "none";
    card.style.backgroundColor = "rgba(77, 55, 236, 0.18)";
    card.style.borderColor = "var(--primary-purple)";

    setTimeout(() => {
      card.style.transition = "var(--transition)";
      card.style.backgroundColor = "";
      card.style.borderColor = "";
    }, 1500);
  }
}

// Helper: map insurer colors
function getInsurerClass(insurer) {
  const low = insurer.toLowerCase();
  if (low.includes("hdfc")) return "insurer-hdfc";
  if (low.includes("sbi")) return "insurer-sbi";
  if (low.includes("tata")) return "insurer-tata";
  if (low.includes("lic")) return "insurer-lic";
  if (low.includes("icici")) return "insurer-icici";
  return "";
}

// Global hook
window.highlightSource = highlightSource;
window.enterDashboard = enterDashboard;
window.triggerUpload = triggerUpload;
window.triggerPreset = triggerPreset;
`;

async function handleRequest(request) {
  const url = new URL(request.url);

  if (url.pathname.startsWith('/api/')) {
    return proxyApi(request, url);
  }

  if (url.pathname === '/styles.css') {
    return new Response(CSS, {
      headers: makeHeaders('text/css; charset=utf-8'),
    });
  }

  if (url.pathname === '/app.js') {
    return new Response(APP_JS, {
      headers: makeHeaders('application/javascript; charset=utf-8'),
    });
  }

  if (url.pathname === '/' || url.pathname === '/index.html') {
    return new Response(HTML, {
      headers: makeHeaders('text/html; charset=utf-8'),
    });
  }

  return new Response(HTML, {
    headers: makeHeaders('text/html; charset=utf-8'),
  });
}

async function proxyApi(request, url) {
  const target = new URL(url.pathname + url.search, RENDER_API_BASE);
  const init = {
    method: request.method,
    headers: new Headers(request.headers),
    redirect: 'follow',
  };

  init.headers.delete('host');
  init.headers.delete('cf-connecting-ip');
  init.headers.delete('cf-ipcountry');
  init.headers.delete('cf-ray');
  init.headers.delete('x-forwarded-for');
  init.headers.delete('x-forwarded-proto');
  init.headers.delete('x-forwarded-host');

  if (!['GET', 'HEAD'].includes(request.method)) {
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
    'Content-Type': contentType,
    'Cache-Control': 'no-store, max-age=0',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'no-referrer',
  };
}

function makeHeadersFrom(sourceHeaders) {
  const headers = new Headers(sourceHeaders);
  headers.set('Cache-Control', 'no-store, max-age=0');
  headers.set('X-Content-Type-Options', 'nosniff');
  headers.set('X-Frame-Options', 'DENY');
  headers.set('Referrer-Policy', 'no-referrer');
  return headers;
}
