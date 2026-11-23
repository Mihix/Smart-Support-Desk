
import "./style.css";

// ==================================================
// 1. CONFIGURATION AND TYPES
// ==================================================

const API_URL = "http://127.0.0.1:8000";

interface UsedFAQ {
  id: number;
  category: string;
  question: string;
  answer: string;
}

interface SuggestedReplyResponse {
  faq_found: boolean;
  suggested_reply: string;
  used_faqs: UsedFAQ[];
}

interface Ticket {
  id: number;
  customer_name: string;
  customer_email: string;
  message: string;
  category: string;
  confidence: number;
  priority: string;
  status: "OPEN" | "IN_PROGRESS" | "RESOLVED";
  created_at: string;
}

interface TicketResponse {
  total_tickets?: number;
  tickets?: Ticket[];
}

interface CreateTicketResponse {
  message: string;
  ticket_id: number;
  category: string;
  confidence: number;
  priority: string;
  status: string;
}

interface DashboardSummary {
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets: number;
  resolved_tickets: number;
}

type Page = "login" | "dashboard" | "customer";

const app = document.querySelector<HTMLDivElement>("#app");

if (!app) {
  throw new Error("App root element #app was not found.");
}

// ==================================================
// 2. APPLICATION STATE
// ==================================================

let currentPage: Page = "login";

let authHeader: string | null = null;
let loggedInUsername = "";

let tickets: Ticket[] = [];

let summary: DashboardSummary = {
  total_tickets: 0,
  open_tickets: 0,
  in_progress_tickets: 0,
  resolved_tickets: 0,
};

let selectedTicket: Ticket | null = null;

let categoryFilter = "";
let statusFilter = "";
let searchText = "";

let loading = false;
let updating = false;
let submitting = false;
let loggingIn = false;

// AI Suggested Reply state
let suggestedReplyLoading = false;
let suggestedReplyError = "";
let suggestedReplyResult: SuggestedReplyResponse | null = null;

let errorMessage = "";
let successMessage = "";
let customerError = "";
let loginError = "";

let submittedTicket: CreateTicketResponse | null = null;

const categories = [
  "ACCOUNT",
  "CANCEL",
  "CONTACT",
  "DELIVERY",
  "FEEDBACK",
  "INVOICE",
  "ORDER",
  "PAYMENT",
  "REFUND",
  "SHIPPING",
  "SUBSCRIPTION",
];

const statuses = ["OPEN", "IN_PROGRESS", "RESOLVED"] as const;

// ==================================================
// 3. HTML ESCAPING
// ==================================================

function escapeHTML(value: unknown): string {
  return String(value ?? "").replace(/[&<>"']/g, (char) => {
    const entities: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };

    return entities[char];
  });
}

// ==================================================
// 4. DATE FORMATTING
// ==================================================

function formatDate(value: string): string {
  if (!value) return "N/A";

  const normalized = value.includes("T")
    ? value
    : value.replace(" ", "T") + "Z";

  const date = new Date(normalized);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

// ==================================================
// 5. STATUS LABEL
// ==================================================

function statusLabel(status: string): string {
  switch (status) {
    case "IN_PROGRESS":
      return "In Progress";
    case "RESOLVED":
      return "Resolved";
    default:
      return "Open";
  }
}

// ==================================================
// 6. RESET AI REPLY STATE
// ==================================================

function resetSuggestedReply(): void {
  suggestedReplyLoading = false;
  suggestedReplyError = "";
  suggestedReplyResult = null;
}

// ==================================================
// 7. API REQUEST HELPER
// ==================================================

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);

  headers.set("Content-Type", "application/json");

  if (authHeader) {
    headers.set("Authorization", authHeader);
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);

    if (response.status === 401 && authHeader) {
      authHeader = null;
      loggedInUsername = "";
      selectedTicket = null;
      resetSuggestedReply();

      currentPage = "login";
      loginError = "Your session is no longer valid. Please log in again.";

      render();
    }

    throw new Error(
      errorData?.detail ||
      `API request failed: ${response.status}`,
    );
  }

  return response.json() as Promise<T>;
}

// ==================================================
// 8. LOGIN PAGE
// ==================================================

function renderLoginPage(): void {
  app!.innerHTML = `
    <div class="login-page">

      <div class="login-card">

        <div class="login-brand">
          <div class="brand-icon">✦</div>

          <div>
            <h2>SupportDesk</h2>
            <span>Team Workspace</span>
          </div>
        </div>

        <div class="login-heading">
          <span class="customer-eyebrow">TEAM ACCESS</span>

          <h1>Welcome back</h1>

          <p>
            Sign in to manage customer support tickets.
          </p>
        </div>

        ${
          loginError
            ? `
              <div class="error-message" role="alert">
                ${escapeHTML(loginError)}
              </div>
            `
            : ""
        }

        <form id="login-form" class="login-form">

          <div class="form-field">
            <label for="login-username">Username</label>

            <input
              id="login-username"
              name="username"
              type="text"
              placeholder="Enter your username"
              autocomplete="username"
              required
              ${loggingIn ? "disabled" : ""}
            />
          </div>

          <div class="form-field">
            <label for="login-password">Password</label>

            <input
              id="login-password"
              name="password"
              type="password"
              placeholder="Enter your password"
              autocomplete="current-password"
              required
              ${loggingIn ? "disabled" : ""}
            />
          </div>

          <button
            type="submit"
            class="login-submit-button"
            ${loggingIn ? "disabled" : ""}
          >
            ${loggingIn ? "Signing in..." : "Sign In →"}
          </button>

        </form>

        <div class="login-divider"></div>

        <div class="login-customer-link">
          <p>Are you a customer?</p>

          <button
            type="button"
            class="text-button"
            data-action="customer-page"
          >
            Submit a support ticket
          </button>
        </div>

      </div>

      <footer class="customer-footer">
        Smart Support Desk · Team Login
      </footer>

    </div>
  `;
}

// ==================================================
// 9. VERIFY TEAM LOGIN
// ==================================================

async function login(
  username: string,
  password: string,
): Promise<void> {
  if (loggingIn) return;

  loggingIn = true;
  loginError = "";
  render();

  try {
    const encodedCredentials = btoa(`${username}:${password}`);
    const temporaryHeader = `Basic ${encodedCredentials}`;

    const response = await fetch(`${API_URL}/login`, {
      method: "GET",
      headers: {
        Authorization: temporaryHeader,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);

      throw new Error(
        errorData?.detail || "Invalid username or password.",
      );
    }

    const data = await response.json();

    authHeader = temporaryHeader;
    loggedInUsername = data.username || username;

    currentPage = "dashboard";

    selectedTicket = null;
    resetSuggestedReply();

    errorMessage = "";
    successMessage = "";

    categoryFilter = "";
    statusFilter = "";
    searchText = "";

    await refreshDashboard();

  } catch (error) {
    authHeader = null;
    loggedInUsername = "";

    loginError =
      error instanceof Error
        ? error.message
        : "Unable to log in. Please try again.";

    currentPage = "login";
    render();

  } finally {
    loggingIn = false;

    if (currentPage === "login") {
      render();
    }
  }
}

// ==================================================
// 10. LOGOUT
// ==================================================

function logout(): void {
  authHeader = null;
  loggedInUsername = "";

  selectedTicket = null;
  resetSuggestedReply();

  tickets = [];

  summary = {
    total_tickets: 0,
    open_tickets: 0,
    in_progress_tickets: 0,
    resolved_tickets: 0,
  };

  categoryFilter = "";
  statusFilter = "";
  searchText = "";

  errorMessage = "";
  successMessage = "";
  loginError = "";

  currentPage = "login";

  render();
}

// ==================================================
// 11. LOAD ALL TICKETS
// ==================================================

async function loadTickets(): Promise<void> {
  const params = new URLSearchParams();

  if (categoryFilter) {
    params.set("category", categoryFilter);
  }

  if (statusFilter) {
    params.set("status", statusFilter);
  }

  const query = params.toString();

  const endpoint = query
    ? `/tickets?${query}`
    : "/tickets";

  const data = await apiRequest<TicketResponse | Ticket[]>(
    endpoint,
  );

  tickets = Array.isArray(data)
    ? data
    : data.tickets || [];
}

// ==================================================
// 12. LOAD DASHBOARD SUMMARY
// ==================================================

async function loadSummary(): Promise<void> {
  summary = await apiRequest<DashboardSummary>(
    "/dashboard/summary",
  );
}

// ==================================================
// 13. REFRESH DASHBOARD
// ==================================================

async function refreshDashboard(): Promise<void> {
  if (!authHeader) {
    currentPage = "login";
    render();
    return;
  }

  loading = true;
  errorMessage = "";
  successMessage = "";

  render();

  try {
    await Promise.all([
      loadTickets(),
      loadSummary(),
    ]);

  } catch (error) {
    errorMessage =
      error instanceof Error
        ? error.message
        : "Unable to load dashboard.";

  } finally {
    loading = false;

    if (currentPage === "dashboard") {
      render();
    }
  }
}

// ==================================================
// 14. SEARCH TICKETS
// ==================================================

function getFilteredTickets(): Ticket[] {
  const search = searchText.toLowerCase().trim();

  return tickets.filter((ticket) => {
    return (
      String(ticket.id).includes(search) ||
      ticket.customer_name.toLowerCase().includes(search) ||
      ticket.customer_email.toLowerCase().includes(search) ||
      ticket.message.toLowerCase().includes(search)
    );
  });
}

// ==================================================
// 15. SUMMARY CARD
// ==================================================

function summaryCard(
  title: string,
  value: number,
  icon: string,
  color: string,
): string {
  return `
    <div class="stat-card">
      <div>
        <p>${escapeHTML(title)}</p>
        <h2>${value}</h2>
      </div>

      <div class="stat-icon ${escapeHTML(color)}">
        ${icon}
      </div>
    </div>
  `;
}

// ==================================================
// 16. TICKET TABLE ROW
// ==================================================

function ticketRow(ticket: Ticket): string {
  return `
    <tr>
      <td>
        <strong class="ticket-id">#${ticket.id}</strong>
      </td>

      <td>
        <div class="customer-cell">
          <strong>${escapeHTML(ticket.customer_name)}</strong>
          <span>${escapeHTML(ticket.customer_email)}</span>
        </div>
      </td>

      <td>
        <span class="category-badge">
          ${escapeHTML(ticket.category)}
        </span>
      </td>

      <td>
        <span class="priority-badge ${escapeHTML(
          (ticket.priority || "MEDIUM").toLowerCase(),
        )}">
          ${escapeHTML(ticket.priority || "MEDIUM")}
        </span>
      </td>

      <td>
        <span class="status-badge ${escapeHTML(
          (ticket.status || "OPEN").toLowerCase(),
        )}">
          <span class="status-dot"></span>
          ${escapeHTML(statusLabel(ticket.status))}
        </span>
      </td>

      <td class="date-cell">
        ${escapeHTML(formatDate(ticket.created_at))}
      </td>

      <td>
        <button
          class="view-button"
          data-action="view-ticket"
          data-id="${ticket.id}"
        >
          View Details
        </button>
      </td>
    </tr>
  `;
}

// ==================================================
// 17. TICKET TABLE
// ==================================================

function renderTicketTable(): string {
  if (loading) {
    return `
      <tr>
        <td colspan="7" class="empty-state">
          Loading tickets...
        </td>
      </tr>
    `;
  }

  const filteredTickets = getFilteredTickets();

  if (filteredTickets.length === 0) {
    return `
      <tr>
        <td colspan="7" class="empty-state">
          <strong>No tickets found</strong>
          <span>Try changing your filters or search.</span>
        </td>
      </tr>
    `;
  }

  return filteredTickets.map(ticketRow).join("");
}

// ==================================================
// 18. CATEGORY FILTER OPTIONS
// ==================================================

function renderCategoryOptions(): string {
  return categories.map((category) => `
    <option
      value="${escapeHTML(category)}"
      ${categoryFilter === category ? "selected" : ""}
    >
      ${escapeHTML(category)}
    </option>
  `).join("");
}

// ==================================================
// 19. AI SUGGESTED REPLY SECTION
// ==================================================

function renderSuggestedReply(): string {
  return `
    <section class="ai-reply-section">

      <div class="ai-reply-header">
        <div>
          <span class="modal-eyebrow">AI ASSISTANT</span>

          <h3>Suggested Reply</h3>

          <p>
            Generate a response using the support FAQ knowledge base.
          </p>
        </div>
      </div>

      <button
        type="button"
        class="ai-generate-button"
        data-action="generate-reply"
        ${suggestedReplyLoading ? "disabled" : ""}
      >
        ${
          suggestedReplyLoading
            ? "Generating AI Reply..."
            : suggestedReplyResult
              ? "↻ Regenerate Reply"
              : "✦ Generate Suggested Reply"
        }
      </button>

      ${
        suggestedReplyError
          ? `
            <div class="error-message" role="alert">
              ${escapeHTML(suggestedReplyError)}
            </div>
          `
          : ""
      }

      ${
        suggestedReplyLoading
          ? `
            <div class="ai-loading">
              <span class="ai-loading-spinner"></span>
              <p>AI is preparing a suggested response...</p>
            </div>
          `
          : ""
      }

      ${
        suggestedReplyResult
          ? `
            <div class="ai-result">

              <div class="ai-result-heading">
                <strong>Generated Response</strong>

                <span class="faq-status ${
                  suggestedReplyResult.faq_found
                    ? "faq-found"
                    : "faq-not-found"
                }">
                  ${
                    suggestedReplyResult.faq_found
                      ? "FAQ Match Found"
                      : "No Matching FAQ"
                  }
                </span>
              </div>

              <div class="ai-reply-text">${escapeHTML(
                suggestedReplyResult.suggested_reply,
              )}</div>

              <div class="used-faq-section">

                <h4>FAQ Entries Used</h4>

                ${
                  suggestedReplyResult.used_faqs.length > 0
                    ? suggestedReplyResult.used_faqs.map((faq) => `
                        <div class="used-faq-card">

                          <div class="used-faq-meta">
                            <span>FAQ #${escapeHTML(faq.id)}</span>
                            <span>${escapeHTML(faq.category)}</span>
                          </div>

                          <strong>
                            ${escapeHTML(faq.question)}
                          </strong>

                          <p>${escapeHTML(faq.answer)}</p>

                        </div>
                      `).join("")
                    : `
                        <p class="no-faq-message">
                          No relevant FAQ entries were found.
                          This reply should not be treated as a
                          confirmed company policy.
                        </p>
                      `
                }

              </div>

            </div>
          `
          : ""
      }

    </section>
  `;
}

// ==================================================
// 20. TICKET DETAILS MODAL
// ==================================================

function renderModal(): string {
  if (!selectedTicket) return "";

  const ticket = selectedTicket;

  return `
    <div class="modal-overlay" data-action="close-overlay">

      <div class="ticket-modal">

        <div class="modal-header">
          <div>
            <span class="modal-eyebrow">TICKET DETAILS</span>
            <h2>Ticket #${ticket.id}</h2>
          </div>

          <button
            type="button"
            class="close-button"
            data-action="close-modal"
          >
            ✕
          </button>
        </div>

        <div class="modal-content">

          <div class="detail-customer">
            <div class="large-avatar">👤</div>

            <div>
              <h3>${escapeHTML(ticket.customer_name)}</h3>
              <p>${escapeHTML(ticket.customer_email)}</p>
            </div>
          </div>

          <div class="detail-grid">

            <div class="detail-item">
              <span>Category</span>
              <strong>${escapeHTML(ticket.category)}</strong>
            </div>

            <div class="detail-item">
              <span>Priority</span>
              <strong>${escapeHTML(ticket.priority)}</strong>
            </div>

            <div class="detail-item">
              <span>ML Confidence</span>
              <strong>
                ${(ticket.confidence * 100).toFixed(2)}%
              </strong>
            </div>

            <div class="detail-item">
              <span>Submitted Date</span>
              <strong>
                ${escapeHTML(formatDate(ticket.created_at))}
              </strong>
            </div>

          </div>

          <div class="message-box">
            <h3>Customer Message</h3>
            <p>${escapeHTML(ticket.message)}</p>
          </div>

          ${renderSuggestedReply()}

          <div class="status-update">

            <label for="ticket-status">
              Update Ticket Status
            </label>

            <select
              id="ticket-status"
              ${updating ? "disabled" : ""}
            >
              ${statuses.map((status) => `
                <option
                  value="${status}"
                  ${ticket.status === status ? "selected" : ""}
                >
                  ${statusLabel(status)}
                </option>
              `).join("")}
            </select>

            ${updating ? "<span>Updating status...</span>" : ""}

          </div>

        </div>

        <div class="modal-footer">
          <button
            type="button"
            class="secondary-button"
            data-action="close-modal"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  `;
}

// ==================================================
// 21. CUSTOMER SUBMISSION PAGE
// PUBLIC PAGE - NO LOGIN REQUIRED
// ==================================================

function renderCustomerPage(): void {
  app!.innerHTML = `
    <div class="customer-page">

      <header class="customer-header">

        <div class="brand">
          <div class="brand-icon">✦</div>

          <div>
            <h2>SupportDesk</h2>
            <span>Customer Support Portal</span>
          </div>
        </div>

        <button
          class="secondary-button"
          data-action="${authHeader ? "dashboard" : "login-page"}"
        >
          ${authHeader ? "Back to Dashboard" : "Team Login"}
        </button>

      </header>

      <main class="customer-main">

        <div class="customer-intro">
          <span class="customer-eyebrow">
            WE ARE HERE TO HELP
          </span>

          <h1>How can we help you?</h1>

          <p>
            Submit your support request and our team
            will get back to you.
          </p>
        </div>

        ${
          submittedTicket
            ? `
              <div class="submission-success">

                <div class="success-icon">✓</div>

                <h2>Ticket submitted successfully!</h2>

                <p>
                  Thank you for contacting us.
                  Your support request has been received.
                </p>

                <div class="confirmation-details">

                  <div>
                    <span>Ticket ID</span>
                    <strong>#${submittedTicket.ticket_id}</strong>
                  </div>

                  <div>
                    <span>Predicted Category</span>
                    <strong>${escapeHTML(submittedTicket.category)}</strong>
                  </div>

                  <div>
                    <span>ML Confidence</span>
                    <strong>
                      ${(submittedTicket.confidence * 100).toFixed(2)}%
                    </strong>
                  </div>

                  <div>
                    <span>Priority</span>
                    <strong>${escapeHTML(submittedTicket.priority)}</strong>
                  </div>

                  <div>
                    <span>Status</span>
                    <strong>${escapeHTML(submittedTicket.status)}</strong>
                  </div>

                </div>

                <button
                  class="customer-submit-button"
                  data-action="new-ticket"
                >
                  Submit Another Ticket
                </button>

              </div>
            `
            : `
              <form id="customer-form" class="customer-form">

                ${
                  customerError
                    ? `
                      <div class="error-message">
                        ${escapeHTML(customerError)}
                      </div>
                    `
                    : ""
                }

                <div class="form-field">
                  <label for="customer-name">Full Name</label>

                  <input
                    id="customer-name"
                    name="name"
                    type="text"
                    placeholder="Enter your full name"
                    minlength="2"
                    maxlength="100"
                    required
                    ${submitting ? "disabled" : ""}
                  />
                </div>

                <div class="form-field">
                  <label for="customer-email">Email Address</label>

                  <input
                    id="customer-email"
                    name="email"
                    type="email"
                    placeholder="you@example.com"
                    maxlength="150"
                    required
                    ${submitting ? "disabled" : ""}
                  />
                </div>

                <div class="form-field">
                  <label for="customer-message">
                    How can we help?
                  </label>

                  <textarea
                    id="customer-message"
                    name="message"
                    placeholder="Describe your issue..."
                    minlength="3"
                    maxlength="2000"
                    rows="6"
                    required
                    ${submitting ? "disabled" : ""}
                  ></textarea>

                  <span class="field-hint">
                    Maximum 2000 characters.
                  </span>
                </div>

                <button
                  type="submit"
                  class="customer-submit-button"
                  ${submitting ? "disabled" : ""}
                >
                  ${
                    submitting
                      ? "Submitting..."
                      : "Submit Support Ticket →"
                  }
                </button>

                <p class="form-note">
                  Your message will be automatically categorized
                  by our machine learning model.
                </p>

              </form>
            `
        }

      </main>

      <footer class="customer-footer">
        Smart Support Desk · Customer Support Portal
      </footer>

    </div>
  `;
}

// ==================================================
// 22. MAIN DASHBOARD
// ==================================================

function render(): void {
  if (currentPage === "login") {
    renderLoginPage();
    return;
  }

  if (currentPage === "customer") {
    renderCustomerPage();
    return;
  }

  if (!authHeader) {
    currentPage = "login";
    renderLoginPage();
    return;
  }

  const filteredTickets = getFilteredTickets();

  app!.innerHTML = `
    <div class="dashboard">

      <aside class="sidebar">

        <div class="brand">
          <div class="brand-icon">✦</div>

          <div>
            <h2>SupportDesk</h2>
            <span>Team Workspace</span>
          </div>
        </div>

        <p class="sidebar-label">WORKSPACE</p>

        <div class="nav-item active">
          <span>▦</span>
          Dashboard
        </div>

        <div class="nav-item">
          <span>▤</span>
          All Tickets
        </div>

        <div class="sidebar-bottom">

          <div class="support-profile">
            <div class="avatar">ST</div>

            <div>
              <strong>${escapeHTML(loggedInUsername)}</strong>
              <span>Support Team</span>
            </div>
          </div>

        </div>

      </aside>

      <main class="main-content">

        <header class="topbar">

          <div>
            <p class="breadcrumb">Workspace / Dashboard</p>

            <h1>Support Dashboard</h1>

            <p class="page-description">
              Manage and monitor customer support tickets.
            </p>
          </div>

          <div class="topbar-actions">

            <button
              class="customer-nav-button"
              data-action="customer-page"
            >
              + Submit Ticket
            </button>

            <button
              class="refresh-button"
              data-action="refresh"
              ${loading ? "disabled" : ""}
            >
              ↻ Refresh
            </button>

            <button
              class="secondary-button"
              data-action="logout"
            >
              Logout
            </button>

          </div>

        </header>

        ${errorMessage ? `
          <div class="error-message">
            ${escapeHTML(errorMessage)}
          </div>
        ` : ""}

        ${successMessage ? `
          <div class="success-message">
            ${escapeHTML(successMessage)}
          </div>
        ` : ""}

        <section class="stats-grid">

          ${summaryCard("Total Tickets", summary.total_tickets, "▤", "blue")}
          ${summaryCard("Open Tickets", summary.open_tickets, "◷", "orange")}
          ${summaryCard("In Progress", summary.in_progress_tickets, "↻", "purple")}
          ${summaryCard("Resolved", summary.resolved_tickets, "✓", "green")}

        </section>

        <section class="ticket-section">

          <div class="section-header">

            <div>
              <h2>Customer Tickets</h2>

              <p>
                View and manage submitted support requests.
              </p>
            </div>

            <span class="ticket-count">
              ${filteredTickets.length} tickets
            </span>

          </div>

          <div class="filter-bar">

            <form id="search-form" class="search-box">

              <input
                id="search-input"
                type="search"
                placeholder="Search tickets or customers..."
                value="${escapeHTML(searchText)}"
              />

              <button type="submit">Search</button>

            </form>

            <div class="filter-select">

              <select id="category-filter">
                <option value="">All Categories</option>
                ${renderCategoryOptions()}
              </select>

            </div>

            <div class="filter-select">

              <select id="status-filter">

                <option value="">All Statuses</option>

                ${statuses.map((status) => `
                  <option
                    value="${status}"
                    ${statusFilter === status ? "selected" : ""}
                  >
                    ${statusLabel(status)}
                  </option>
                `).join("")}

              </select>

            </div>

          </div>

          <div class="table-wrapper">

            <table class="ticket-table">

              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Customer</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Submitted</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                ${renderTicketTable()}
              </tbody>

            </table>

          </div>

        </section>

        <footer class="footer">
          Smart Support Desk · Customer Support Management
        </footer>

      </main>

      ${renderModal()}

    </div>
  `;
}

// ==================================================
// 23. GENERATE AI SUGGESTED REPLY
// ==================================================

async function generateSuggestedReply(): Promise<void> {
  if (!selectedTicket || suggestedReplyLoading) {
    return;
  }

  const ticket = selectedTicket;

  suggestedReplyLoading = true;
  suggestedReplyError = "";
  suggestedReplyResult = null;

  render();

  try {
    const result = await apiRequest<SuggestedReplyResponse>(
      "/suggested-reply",
      {
        method: "POST",

        body: JSON.stringify({
          message: ticket.message,
          category: ticket.category,
        }),
      },
    );

    // Store the result only if the same ticket is still open.
    if (selectedTicket?.id === ticket.id) {
      suggestedReplyResult = result;
    }

  } catch (error) {
    if (selectedTicket?.id === ticket.id) {
      suggestedReplyError =
        error instanceof Error
          ? error.message
          : "Unable to generate suggested reply.";
    }

  } finally {
    suggestedReplyLoading = false;

    if (
      currentPage === "dashboard" &&
      selectedTicket?.id === ticket.id
    ) {
      render();
    }
  }
}

// ==================================================
// 24. OPEN INDIVIDUAL TICKET
// ==================================================

async function openTicket(ticketId: number): Promise<void> {
  try {
    errorMessage = "";
    successMessage = "";

    resetSuggestedReply();

    const ticket = await apiRequest<Ticket>(
      `/tickets/${ticketId}`,
    );

    selectedTicket = ticket;

    render();

  } catch (error) {
    errorMessage =
      error instanceof Error
        ? error.message
        : "Unable to load ticket.";

    render();
  }
}

// ==================================================
// 25. UPDATE TICKET STATUS
// ==================================================

async function updateTicketStatus(
  newStatus: string,
): Promise<void> {
  if (!selectedTicket || updating) return;

  if (!statuses.includes(newStatus as typeof statuses[number])) {
    return;
  }

  if (selectedTicket.status === newStatus) return;

  const ticketId = selectedTicket.id;

  try {
    updating = true;
    errorMessage = "";
    successMessage = "";

    render();

    await apiRequest(
      `/tickets/${ticketId}/status`,
      {
        method: "PATCH",
        body: JSON.stringify({
          status: newStatus,
        }),
      },
    );

    await Promise.all([
      loadTickets(),
      loadSummary(),
    ]);

    selectedTicket = await apiRequest<Ticket>(
      `/tickets/${ticketId}`,
    );

    successMessage =
      `Ticket #${ticketId} updated successfully!`;

  } catch (error) {
    errorMessage =
      error instanceof Error
        ? error.message
        : "Unable to update ticket status.";

  } finally {
    updating = false;

    if (currentPage === "dashboard") {
      render();
    }
  }
}

// ==================================================
// 26. CLICK EVENT HANDLER
// ==================================================

app.addEventListener("click", async (event) => {
  const target = event.target;

  if (!(target instanceof HTMLElement)) return;

  const button = target.closest<HTMLElement>(
    "[data-action]",
  );

  if (!button) return;

  const action = button.dataset.action;

  // Open customer submission page.
  if (action === "customer-page") {
    currentPage = "customer";
    customerError = "";
    submittedTicket = null;
    selectedTicket = null;
    resetSuggestedReply();

    render();
    return;
  }

  // Return to dashboard.
  if (action === "dashboard") {
    if (!authHeader) {
      currentPage = "login";
      render();
      return;
    }

    currentPage = "dashboard";
    selectedTicket = null;
    resetSuggestedReply();

    await refreshDashboard();
    return;
  }

  // Go to login page.
  if (action === "login-page") {
    currentPage = "login";
    loginError = "";
    render();
    return;
  }

  // Logout.
  if (action === "logout") {
    logout();
    return;
  }

  // Submit another customer ticket.
  if (action === "new-ticket") {
    submittedTicket = null;
    customerError = "";

    render();
    return;
  }

  // Refresh dashboard.
  if (action === "refresh") {
    await refreshDashboard();
    return;
  }

  // View individual ticket.
  if (action === "view-ticket") {
    const ticketId = Number(button.dataset.id);

    if (Number.isInteger(ticketId) && ticketId > 0) {
      await openTicket(ticketId);
    }

    return;
  }

  // Generate AI suggested reply.
  if (action === "generate-reply") {
    await generateSuggestedReply();
    return;
  }

  // Close ticket modal.
  if (action === "close-modal") {
    selectedTicket = null;
    resetSuggestedReply();

    render();
    return;
  }

  // Close modal by clicking overlay.
  if (action === "close-overlay" && target === button) {
    selectedTicket = null;
    resetSuggestedReply();

    render();
    return;
  }
});

// ==================================================
// 27. FORM SUBMISSION HANDLER
// ==================================================

app.addEventListener("submit", async (event) => {
  const target = event.target;

  if (!(target instanceof HTMLFormElement)) return;

  event.preventDefault();

  // ----------------------------------------------
  // TEAM LOGIN FORM
  // ----------------------------------------------

  if (target.id === "login-form") {
    if (loggingIn) return;

    const formData = new FormData(target);

    const username = String(
      formData.get("username") || "",
    ).trim();

    const password = String(
      formData.get("password") || "",
    );

    if (!username || !password) {
      loginError = "Please enter your username and password.";
      render();
      return;
    }

    await login(username, password);
    return;
  }

  // ----------------------------------------------
  // CUSTOMER TICKET SUBMISSION FORM
  // ----------------------------------------------

  if (target.id === "customer-form") {
    if (submitting) return;

    const formData = new FormData(target);

    const name = String(
      formData.get("name") || "",
    ).trim();

    const email = String(
      formData.get("email") || "",
    ).trim();

    const message = String(
      formData.get("message") || "",
    ).trim();

    if (
      name.length < 2 ||
      message.length < 3 ||
      !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)
    ) {
      customerError =
        "Please enter valid name, email and message details.";

      render();
      return;
    }

    submitting = true;
    customerError = "";

    render();

    try {
      submittedTicket = await apiRequest<CreateTicketResponse>(
        "/tickets",
        {
          method: "POST",

          body: JSON.stringify({
            name,
            email,
            message,
          }),
        },
      );

    } catch (error) {
      customerError =
        error instanceof Error
          ? error.message
          : "Unable to submit your ticket.";

    } finally {
      submitting = false;

      if (currentPage === "customer") {
        render();
      }
    }

    return;
  }

  // ----------------------------------------------
  // DASHBOARD SEARCH FORM
  // ----------------------------------------------

  if (target.id === "search-form") {
    const input = app!.querySelector<HTMLInputElement>(
      "#search-input",
    );

    searchText = input?.value || "";

    render();
  }
});

// ==================================================
// 28. FILTER AND STATUS EVENT HANDLER
// ==================================================

app.addEventListener("change", async (event) => {
  const target = event.target;

  if (!(target instanceof HTMLSelectElement)) return;

  // Category filter.
  if (target.id === "category-filter") {
    categoryFilter = target.value;

    await refreshDashboard();
    return;
  }

  // Status filter.
  if (target.id === "status-filter") {
    statusFilter = target.value;

    await refreshDashboard();
    return;
  }

  // Ticket status update.
  if (target.id === "ticket-status") {
    await updateTicketStatus(target.value);
  }
});

// ==================================================
// 29. START APPLICATION
// ==================================================

currentPage = "login";

render();
