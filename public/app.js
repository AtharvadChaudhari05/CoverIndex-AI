/* ==========================================
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
const btnNewChat = document.getElementById("btnNewChat");
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
    const response = await fetch(`${API_BASE_URL}/api/status`);
    const payload = await response.json();
    if (payload.ready) {
      statusText.textContent = `${payload.page_count} pages indexed`;
    }
  } catch (e) {
    statusText.textContent = "Offline";
  }
}

// Load pre-indexed policies list
async function loadIndexedPolicies() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/policies`);
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
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted)">No policies indexed yet. Upload one to get started!</td></tr>`;
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
    tr.innerHTML = `
      <td><i data-lucide="file-text"></i> ${policy.file_name}</td>
      <td>${insurer}</td>
      <td><span class="badge success">Verified</span></td>
      <td><button class="icon-btn" onclick="triggerPreset('ask', 'Summarize ${policy.file_name}')" title="Analyze Policy"><i data-lucide="message-square"></i></button></td>
    `;
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
  });

  closeInspectorBtn.addEventListener("click", () => {
    appDashboard.classList.remove("inspector-open");
    appInspector.classList.add("hidden");
  });

  // Mobile menu toggle
  mobileMenuBtn.addEventListener("click", () => {
    sidebar.classList.toggle("open");
  });
  
  collapseSidebarBtn.addEventListener("click", () => {
    sidebar.classList.remove("open");
  });

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
      const contentId = `inspector-tab-${tab.dataset.inspectorTab}`;
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
  const userMsgId = addMessage("user", `Please review this insurance policy document.`, file.name);
  
  // Render loading assistant state
  const loadingMsgId = addMessage("assistant", `### Indexing & Analysis in progress...\nUploading and parsing **${file.name}** to CoverIndex AI. Reading pages and extracts...`);
  
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: "POST",
      body: formData
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Failed to upload file");
    }

    // Success! Update loading bubble with file summary
    updateMessage(loadingMsgId, `### Indexing Successful! 🎉\nIt looks like you've uploaded a policy document for the **${file.name}**. I have successfully parsed and indexed **${payload.page_count} pages** into CoverIndex AI in-memory. \n\nYou can now ask me any specific questions about coverage details, exclusions, premium grace periods, or claims guidelines and I will retrieve the answers directly from this file!`);
    
    // Add file to uploaded session files
    uploadedFiles.push(file.name);
    loadIndexStatus();
    createChatSessionItem(file.name);
  } catch (error) {
    updateMessage(loadingMsgId, `### Upload Failed\nCould not index policy document: **${error.message}**.\n\nPlease verify that your server is running and the file is a valid PDF.`);
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
  nameDiv.textContent = `Review: ${fileName}`;
  chatSessionTitle.textContent = `Review: ${fileName}`;

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
  const msgId = `msg-${messageCounter}`;

  switchWorkspaceView("chatFeedWindow");
  hasMessages = true;

  const msgRow = document.createElement("div");
  msgRow.className = `message-bubble-row ${role}`;
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
    const citationId = `${filename} p. ${page}`;
    const truncatedText = filename.length > 25 ? filename.slice(0, 22) + "..." : filename;
    return `<span class="citation-link" onclick="highlightSource('${citationId}')" title="Click to inspect source text">${truncatedText} p. ${page}</span>`;
  });

  return html;
}

// Client query submission
async function submitQuery(query) {
  // Set composer disabled/loading
  composerInput.disabled = true;
  composerSendBtn.disabled = true;
  composerSendBtn.innerHTML = `<i data-lucide="loader" class="spin"></i>`;
  if (window.lucide) lucide.createIcons();

  const fileToUpload = stagedAttachment;
  let fileUploadedName = null;
  let loadingId = null;

  if (fileToUpload) {
    clearStagedAttachment();
    
    const isAlreadyIndexed = indexedPolicies.includes(fileToUpload.name.toLowerCase());
    
    if (!hasMessages) {
      activeSessionName = `Review: ${fileToUpload.name}`;
      chatSessionTitle.textContent = activeSessionName;
      createChatSessionItem(fileToUpload.name);
    }
    addMessage("user", query, fileToUpload.name);
    
    if (isAlreadyIndexed) {
      // Document is already indexed, bypass upload completely
      loadingId = addMessage("assistant", `Thinking...`);
      fileUploadedName = fileToUpload.name;
    } else {
      // Upload and index new document
      loadingId = addMessage("assistant", `### Uploading & Indexing... \nUploading and parsing **${fileToUpload.name}** to CoverIndex AI. Reading pages and extracts...`);
      
      const formData = new FormData();
      formData.append("file", fileToUpload);
      
      try {
        const uploadResponse = await fetch(`${API_BASE_URL}/api/upload`, {
          method: "POST",
          body: formData
        });
        const uploadPayload = await uploadResponse.json();
        if (!uploadResponse.ok) {
          throw new Error(uploadPayload.error || "Failed to upload file");
        }
        
        // Update loading bubble to query status
        updateMessage(loadingId, `### Analyzing Document...\nDocument **${fileToUpload.name}** uploaded successfully. Running query: "${query}"...`);
        fileUploadedName = uploadPayload.filename || fileToUpload.name;
        uploadedFiles.push(fileUploadedName);
        loadIndexStatus();
      } catch (uploadError) {
        updateMessage(loadingId, `### Upload Failed\nCould not index policy document: **${uploadError.message}**.`);
        // Reset composer
        composerInput.disabled = false;
        composerSendBtn.disabled = false;
        composerSendBtn.innerHTML = `<i data-lucide="arrow-up"></i>`;
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
    loadingId = addMessage("assistant", `Thinking...`);
  }

  // Now query /api/ask
  try {
    let askFileName = fileUploadedName;
    if (!askFileName && activeSessionName.startsWith("Review: ")) {
      askFileName = activeSessionName.replace("Review: ", "");
    }

    const response = await fetch(`${API_BASE_URL}/api/ask`, {
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
    updateMessage(loadingId, `### Error Encountered\nCould not fetch response: **${error.message}**.\nPlease check your python backend is running.`);
  } finally {
    composerInput.disabled = false;
    composerSendBtn.disabled = false;
    composerSendBtn.innerHTML = `<i data-lucide="arrow-up"></i>`;

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
    insurerTag.textContent = `Insurer: ${route.insurer}`;
    footer.appendChild(insurerTag);
  }
  
  if (route && route.intent && route.intent !== "general") {
    const intentTag = document.createElement("span");
    intentTag.className = "tag routed";
    intentTag.textContent = `Category: ${route.intent}`;
    footer.appendChild(intentTag);
  }

  if (confidence > 0) {
    const confTag = document.createElement("span");
    confTag.className = "tag grounded";
    confTag.textContent = `${(confidence * 100).toFixed(0)}% grounded`;
    footer.appendChild(confTag);
  } else {
    const confTag = document.createElement("span");
    confTag.className = "tag routed";
    confTag.style.borderColor = "rgba(249, 115, 22, 0.25)";
    confTag.style.backgroundColor = "rgba(249, 115, 22, 0.08)";
    confTag.style.color = "#ea580c";
    confTag.textContent = `General LLM Mode`;
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
    inspectorSourcesList.innerHTML = `
      <div class="inspector-empty-state">
        <i data-lucide="file-question"></i>
        <p>No grounding sources were utilized for this response.</p>
      </div>`;
    if (window.lucide) lucide.createIcons();
    return;
  }

  inspectorSourcesList.innerHTML = "";
  sources.forEach(src => {
    const card = document.createElement("div");
    card.className = `source-card ${getInsurerClass(src.insurer)}`;
    card.id = `src-${src.citation.replace(/[\s\.]/g, "-")}`;

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
    score.textContent = `Score: ${src.score}`;

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
    inspectorTraceTimeline.innerHTML = `
      <div class="inspector-empty-state">
        <i data-lucide="network"></i>
        <p>Trace log details not available.</p>
      </div>`;
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
    let stepTitle = `Step ${idx + 1}`;
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

  const targetId = `src-${citationId.replace(/[\s\.]/g, "-")}`;
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
