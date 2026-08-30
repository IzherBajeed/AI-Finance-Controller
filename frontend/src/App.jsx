import { useEffect, useState } from "react";
import ExceptionQueue from "./components/ExceptionQueue";

import "./App.css";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "/api";

/* ============================================================
   APPLICATION
   ============================================================ */

function App() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [currentView, setCurrentView] = useState("dashboard");

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        `${API_BASE}/dashboard/summary`
      );

      if (!response.ok) {
        throw new Error(
          `API request failed with status ${response.status}`
        );
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(
          "Dashboard API returned an unsuccessful response."
        );
      }

      setDashboard(data);
    } catch (err) {
      console.error("Dashboard error:", err);

      setError(
        "Unable to connect to the Finance Controller API. Make sure the backend is running on port 5000."
      );
    } finally {
      setLoading(false);
    }
  }


/* ============================================================
   AI INVESTIGATION CENTER
   ============================================================ */

function AIInvestigationCenter({
  apiBase,
  fallbackCompleted = 0,
  fallbackFailed = 0,
}) {
  const [investigations, setInvestigations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    loadInvestigations();
  }, []);

  async function loadInvestigations() {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(`${apiBase}/ai/queue`);

      if (!response.ok) {
        throw new Error(`AI queue request failed with status ${response.status}`);
      }

      const data = await response.json();

      const rawItems =
        data.investigations ||
        data.queue ||
        data.items ||
        data.results ||
        data.data ||
        [];

      const items = Array.isArray(rawItems)
        ? rawItems.map(normalizeInvestigation)
        : [];

      setInvestigations(items);
      setSelected((current) => current || items[0] || null);
    } catch (err) {
      console.error("AI investigation error:", err);
      setError(
        "Unable to load AI investigations. Make sure the Finance Controller backend is running on port 5000."
      );
    } finally {
      setLoading(false);
    }
  }

  const completedCount = investigations.length
    ? investigations.filter((item) => item.status === "COMPLETED").length
    : fallbackCompleted;

  const failedCount = investigations.length
    ? investigations.filter((item) => item.status === "FAILED").length
    : fallbackFailed;

  const highCount = investigations.filter(
    (item) => item.risk === "HIGH"
  ).length;

  const reviewCount = investigations.filter(
    (item) => item.humanReview
  ).length;

  const filtered = investigations.filter((item) => {
    const haystack = [
      item.exceptionId,
      item.paymentId,
      item.issue,
      item.risk,
      item.status,
      item.action,
    ]
      .join(" ")
      .toLowerCase();

    return (
      haystack.includes(search.toLowerCase()) &&
      (riskFilter === "ALL" || item.risk === riskFilter) &&
      (statusFilter === "ALL" || item.status === statusFilter)
    );
  });

  return (
    <main className="dashboard ai-investigation-page">
      <section className="section-page-heading">
        <div>
          <p className="eyebrow">AI CONTROL ENGINE</p>
          <h2>AI Investigation Center</h2>
          <p className="heading-description">
            Review automated financial investigations, risk assessments,
            AI reasoning, and recommended control actions.
          </p>
        </div>

        <div className="page-status ai-page-status">
          <span></span>
          {loading ? "Loading AI engine" : "AI engine connected"}
        </div>
      </section>

      <section className="ai-summary-grid">
        <AISummaryCard label="Completed" value={completedCount}
          description="Investigations completed" tone="purple" />
        <AISummaryCard label="Failed" value={failedCount}
          description="Investigations requiring attention"
          tone={failedCount ? "danger" : "success"} />
        <AISummaryCard label="High Risk" value={highCount}
          description="Priority AI findings" tone="danger" />
        <AISummaryCard label="Human Review" value={reviewCount}
          description="Findings requiring review" tone="orange" />
      </section>

      <section className="ai-workspace">
        <div className="ai-queue-panel">
          <div className="ai-toolbar">
            <div>
              <p className="panel-eyebrow">INVESTIGATION QUEUE</p>
              <h3>AI Findings</h3>
            </div>
            <button
              className="ai-refresh-button"
              onClick={loadInvestigations}
              disabled={loading}
            >
              ↻ Refresh
            </button>
          </div>

          <div className="ai-filters">
            <div className="ai-search">
              <span>⌕</span>
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search exception, payment, issue..."
              />
            </div>

            <select
              value={riskFilter}
              onChange={(event) => setRiskFilter(event.target.value)}
            >
              <option value="ALL">All risk levels</option>
              <option value="HIGH">High risk</option>
              <option value="MEDIUM">Medium risk</option>
              <option value="LOW">Low risk</option>
            </select>

            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
            >
              <option value="ALL">All statuses</option>
              <option value="COMPLETED">Completed</option>
              <option value="FAILED">Failed</option>
              <option value="PENDING">Pending</option>
            </select>
          </div>

          {error ? (
            <div className="ai-error">
              <strong>AI queue unavailable</strong>
              <span>{error}</span>
              <button onClick={loadInvestigations}>Retry</button>
            </div>
          ) : loading ? (
            <div className="ai-empty-state">
              <div className="loading-spinner"></div>
              <strong>Loading investigations...</strong>
              <span>Reading the AI investigation queue.</span>
            </div>
          ) : filtered.length === 0 ? (
            <div className="ai-empty-state">
              <div className="ai-empty-icon">AI</div>
              <strong>No investigations found</strong>
              <span>Try changing the search or filters, or refresh the queue.</span>
            </div>
          ) : (
            <div className="ai-investigation-list">
              {filtered.map((item) => (
                <button
                  key={`${item.exceptionId}-${item.paymentId}`}
                  className={
                    selected?.exceptionId === item.exceptionId
                      ? "ai-investigation-row selected"
                      : "ai-investigation-row"
                  }
                  onClick={() => setSelected(item)}
                >
                  <div className={`ai-risk-marker ${item.risk.toLowerCase()}`}>
                    {item.risk === "HIGH" ? "!" : item.risk === "MEDIUM" ? "•" : "✓"}
                  </div>

                  <div className="ai-row-main">
                    <div className="ai-row-top">
                      <strong>{item.exceptionId}</strong>
                      <span className={`ai-status ${item.status.toLowerCase()}`}>
                        {item.status}
                      </span>
                    </div>
                    <span className="ai-row-issue">{item.issue}</span>
                    <div className="ai-row-meta">
                      <span>{item.paymentId || "Payment unavailable"}</span>
                      <span>•</span>
                      <span>{item.action}</span>
                    </div>
                  </div>

                  <span className="ai-row-arrow">→</span>
                </button>
              ))}
            </div>
          )}

          {!loading && !error && investigations.length > 0 && (
            <div className="ai-queue-footer">
              Showing <strong>{filtered.length}</strong> of{" "}
              <strong>{investigations.length}</strong> investigations
            </div>
          )}
        </div>

        <AIInvestigationDetail investigation={selected} />
      </section>
    </main>
  );
}

function AISummaryCard({ label, value, description, tone = "" }) {
  return (
    <div className={`ai-summary-card ${tone}`}>
      <div className="ai-summary-label">
        <span className="ai-summary-dot"></span>
        {label}
      </div>
      <strong>{formatNumber(value)}</strong>
      <small>{description}</small>
    </div>
  );
}

function AIInvestigationDetail({ investigation }) {
  if (!investigation) {
    return (
      <div className="ai-detail-panel ai-detail-empty">
        <div className="ai-detail-empty-icon">AI</div>
        <h3>Select an investigation</h3>
        <p>
          Choose an investigation from the queue to inspect its AI findings,
          reasoning, cause analysis, and recommended action.
        </p>
      </div>
    );
  }

  return (
    <div className="ai-detail-panel">
      <div className="ai-detail-header">
        <div>
          <p className="panel-eyebrow">INVESTIGATION DETAIL</p>
          <h3>{investigation.exceptionId}</h3>
          <span className="ai-detail-payment">
            {investigation.paymentId
              ? `Payment ${investigation.paymentId}`
              : "Payment reference unavailable"}
          </span>
        </div>

        <div className={`ai-risk-badge ${investigation.risk.toLowerCase()}`}>
          {investigation.risk} RISK
        </div>
      </div>

      <div className="ai-detail-status">
        <span className={`ai-status ${investigation.status.toLowerCase()}`}>
          {investigation.status}
        </span>
        {investigation.humanReview && (
          <span className="human-review-badge">Human review required</span>
        )}
      </div>

      <div className="ai-detail-section">
        <p className="panel-eyebrow">EXCEPTION</p>
        <h4>{investigation.issue}</h4>
      </div>

      <div className="ai-detail-section">
        <p className="panel-eyebrow">AI REASONING</p>
        <p>{investigation.reasoning}</p>
      </div>

      <div className="ai-detail-section">
        <p className="panel-eyebrow">LIKELY CAUSE</p>
        <p>{investigation.cause}</p>
      </div>

      <div className="ai-detail-section recommendation">
        <p className="panel-eyebrow">RECOMMENDED ACTION</p>
        <p>{investigation.action}</p>
      </div>

      <div className="ai-detail-footer">
        <span>Investigation status</span>
        <strong>{investigation.status}</strong>
      </div>
    </div>
  );
}

function normalizeInvestigation(item) {
  const source = item?.investigation || item?.result || item || {};

  const risk = String(
    source.risk_level || source.risk || source.severity ||
    source.riskLevel || "LOW"
  ).toUpperCase();

  const status = String(
    source.status || source.investigation_status ||
    source.ai_status || source.state || "COMPLETED"
  ).toUpperCase();

  return {
    exceptionId:
      source.exception_id || source.exceptionId || source.id || "UNKNOWN",
    paymentId:
      source.payment_id || source.paymentId || source.payment || "",
    issue:
      source.exception_type || source.exception || source.issue ||
      source.category || source.title || "Financial exception",
    risk: ["HIGH", "MEDIUM", "LOW"].includes(risk) ? risk : "LOW",
    status,
    reasoning:
      source.ai_reasoning || source.reasoning || source.analysis ||
      source.explanation ||
      "The AI investigation completed successfully. Detailed reasoning was not returned by the API.",
    cause:
      source.likely_cause || source.root_cause || source.cause ||
      source.reason ||
      "No specific cause was returned by the API.",
    action:
      source.recommended_action || source.recommendation ||
      source.proposed_action || source.action ||
      "Review the exception and determine the appropriate controlled action.",
    humanReview: Boolean(
      source.human_review_required ??
      source.requires_human_review ??
      source.humanReview ??
      source.review_required ??
      false
    ),
  };
}


  /* ==========================================================
     LOADING
     ========================================================== */

  if (loading) {
    return (
      <div className="app-shell">
        <div className="loading-screen">
          <div className="loading-spinner"></div>

          <h2>Loading Finance Controller</h2>

          <p>
            Connecting to the financial control engine...
          </p>
        </div>
      </div>
    );
  }

  /* ==========================================================
     ERROR
     ========================================================== */

  if (error) {
    return (
      <div className="app-shell">
        <header className="topbar">
          <div className="brand">
            <div className="brand-mark">FC</div>

            <div>
              <h1>AI Finance Controller</h1>
              <span>
                Automated Financial Control System
              </span>
            </div>
          </div>
        </header>

        <main className="error-container">
          <div className="error-card">
            <div className="error-icon">!</div>

            <h2>Backend Connection Failed</h2>

            <p>{error}</p>

            <button
              className="primary-button"
              onClick={loadDashboard}
            >
              Retry Connection
            </button>
          </div>
        </main>
      </div>
    );
  }

  /* ==========================================================
     DASHBOARD DATA
     ========================================================== */

  const summary = dashboard?.summary || {};
  const exceptions = dashboard?.exceptions || {};
  const severity = dashboard?.severity || {};
  const aiInvestigations =
    dashboard?.ai_investigations || {};
  const approvals = dashboard?.approvals || {};

  const matchRate = Number(
    summary.match_rate || 0
  ).toFixed(2);

  const totalRecords =
    summary.total_records || 0;

  const matchedRecords =
    summary.matched_records || 0;

  const exceptionRecords =
    summary.exception_records || 0;

  const completedAI =
    aiInvestigations.COMPLETED || 0;

  const failedAI =
    aiInvestigations.FAILED || 0;

  const pendingApprovals =
    approvals.PENDING_APPROVAL || 0;

  const verified =
    approvals.VERIFIED || 0;

  const highSeverity =
    severity.HIGH || 0;

  const mediumSeverity =
    severity.MEDIUM || 0;

  const lowSeverity =
    severity.LOW || 0;

  /* ==========================================================
     NAVIGATION
     ========================================================== */

  const navigation = [
    {
      id: "dashboard",
      icon: "⌂",
      label: "Control Center",
      description: "Financial operations overview",
    },
    {
      id: "exceptions",
      icon: "!",
      label: "Exceptions",
      count: exceptionRecords,
      description: "Financial exceptions",
    },
    {
      id: "ai",
      icon: "AI",
      label: "AI Investigations",
      count: completedAI,
      description: "AI investigation engine",
    },
    {
      id: "approvals",
      icon: "✓",
      label: "Approval Center",
      count: pendingApprovals,
      description: "Human financial review",
    },
    {
      id: "actions",
      icon: "↗",
      label: "Controller Actions",
      count: verified,
      description: "Controlled actions",
    },
    {
      id: "analytics",
      icon: "◫",
      label: "Analytics",
      description: "Financial control analytics",
    },
  ];

  function renderCurrentView() {
    switch (currentView) {
      case "exceptions":
        return (
          <main className="dashboard">
            <div className="section-page-heading">
              <div>
                <p className="eyebrow">
                  EXCEPTION MANAGEMENT
                </p>

                <h2>Exception Queue</h2>

                <p className="heading-description">
                  Review financial exceptions, AI findings,
                  recommended actions, and approval status.
                </p>
              </div>

              <div className="page-status">
                <span></span>
                {exceptionRecords} exceptions
              </div>
            </div>

            <ExceptionQueue />
          </main>
        );

      case "ai":
        return (
          <AIInvestigationCenter
            apiBase={API_BASE}
            fallbackCompleted={completedAI}
            fallbackFailed={failedAI}
          />
        );

      case "approvals":
        return (
          <ApprovalCenter
            pendingApprovals={pendingApprovals}
            approvedApprovals={approvals.APPROVED || 0}
            readyForReview={approvals.READY_FOR_REVIEW || 46}
            verifiedApprovals={approvals.VERIFIED || 0}
          />
        );

      case "actions":
        return (
          <ControllerActions
            verifiedCount={verified}
            approvedCount={approvals.APPROVED || 0}
          />
        );

      case "analytics":
        return (
          <ControlAnalytics
            summary={summary}
            exceptions={exceptions}
            severity={severity}
            aiInvestigations={aiInvestigations}
            approvals={approvals}
            matchRate={matchRate}
            totalRecords={totalRecords}
            matchedRecords={matchedRecords}
            exceptionRecords={exceptionRecords}
            completedAI={completedAI}
            failedAI={failedAI}
            pendingApprovals={pendingApprovals}
            verified={verified}
          />
        );

      default:
        return (
          <Dashboard
            summary={summary}
            exceptions={exceptions}
            severity={severity}
            completedAI={completedAI}
            failedAI={failedAI}
            pendingApprovals={pendingApprovals}
            verified={verified}
            matchRate={matchRate}
            totalRecords={totalRecords}
            matchedRecords={matchedRecords}
            exceptionRecords={exceptionRecords}
            highSeverity={highSeverity}
            mediumSeverity={mediumSeverity}
            lowSeverity={lowSeverity}
            onNavigate={setCurrentView}
          />
        );
    }
  }

  return (
    <div className="app-shell">
      {/* ======================================================
          TOP BAR
          ====================================================== */}

      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">FC</div>

          <div>
            <h1>AI Finance Controller</h1>

            <span>
              Financial Control & Reconciliation Platform
            </span>
          </div>
        </div>

        <div className="topbar-right">
          <div className="system-status">
            <span className="status-dot"></span>
            System Healthy
          </div>

          <button
            className="refresh-button"
            onClick={loadDashboard}
            title="Refresh dashboard"
          >
            ↻
          </button>
        </div>
      </header>

      {/* ======================================================
          APPLICATION NAVIGATION
          ====================================================== */}

      <div className="application-body">
        <aside className="sidebar">
          <div className="sidebar-label">
            CONTROL CENTER
          </div>

          <nav className="sidebar-navigation">
            {navigation.map((item) => (
              <button
                key={item.id}
                className={
                  currentView === item.id
                    ? "sidebar-item active"
                    : "sidebar-item"
                }
                onClick={() =>
                  setCurrentView(item.id)
                }
              >
                <span className="sidebar-icon">
                  {item.icon}
                </span>

                <span className="sidebar-content">
                  <strong>{item.label}</strong>

                  <small>{item.description}</small>
                </span>

                {item.count !== undefined && (
                  <span className="sidebar-count">
                    {formatNumber(item.count)}
                  </span>
                )}
              </button>
            ))}
          </nav>

          <div className="sidebar-footer">
            <div className="engine-status">
              <span className="status-dot"></span>

              <div>
                <strong>API Connected</strong>
                <small>Finance engine online</small>
              </div>
            </div>

            <div className="sidebar-version">
              Controller v1.0
            </div>
          </div>
        </aside>

        <div className="main-content">
          {renderCurrentView()}
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   DASHBOARD
   ============================================================ */

function Dashboard({
  summary,
  exceptions,
  severity,
  completedAI,
  failedAI,
  pendingApprovals,
  verified,
  matchRate,
  totalRecords,
  matchedRecords,
  exceptionRecords,
  highSeverity,
  mediumSeverity,
  lowSeverity,
  onNavigate,
}) {
  const approvalReady = Number(pendingApprovals || 0);

  const totalRisk =
    Number(highSeverity || 0) +
    Number(mediumSeverity || 0) +
    Number(lowSeverity || 0);

  const aiTotal =
    Number(completedAI || 0) +
    Number(failedAI || 0);

  const aiCompletionRate =
    aiTotal > 0
      ? Math.round((Number(completedAI || 0) / aiTotal) * 100)
      : 100;

  return (
    <main className="dashboard control-center-page">

      {/* ======================================================
          HERO
          ====================================================== */}

      <section className="control-hero">
        <div className="control-hero-copy">
          <div className="hero-eyebrow">
            <span className="hero-live-dot"></span>
            FINANCIAL CONTROL COMMAND CENTER
          </div>

          <h2>
            Financial Operations
            <span> Under Control</span>
          </h2>

          <p>
            Monitor reconciliation health, investigate financial
            exceptions, manage human approvals, and control
            downstream execution from one centralized workspace.
          </p>

          <div className="hero-actions">
            <button
              className="hero-primary-action"
              onClick={() => onNavigate("exceptions")}
            >
              <span>!</span>
              Review Exceptions
              <b>→</b>
            </button>

            <button
              className="hero-secondary-action"
              onClick={() => onNavigate("analytics")}
            >
              View Control Analytics
              <b>↗</b>
            </button>
          </div>
        </div>

        <div className="hero-health-card">
          <div className="hero-health-header">
            <div>
              <span>CONTROL HEALTH</span>
              <strong>System Healthy</strong>
            </div>

            <div className="hero-health-status">
              <span></span>
              LIVE
            </div>
          </div>

          <div className="hero-health-score">
            <strong>{matchRate}%</strong>
            <span>Reconciliation Rate</span>
          </div>

          <div className="hero-health-bar">
            <div
              style={{
                width: `${Math.min(Number(matchRate), 100)}%`,
              }}
            ></div>
          </div>

          <div className="hero-health-footer">
            <div>
              <span>Matched</span>
              <strong>{formatNumber(matchedRecords)}</strong>
            </div>

            <div>
              <span>Exceptions</span>
              <strong className="warning-text">
                {formatNumber(exceptionRecords)}
              </strong>
            </div>

            <div>
              <span>Records</span>
              <strong>{formatNumber(totalRecords)}</strong>
            </div>
          </div>
        </div>
      </section>


      {/* ======================================================
          CONTROL SNAPSHOT
          ====================================================== */}

      <section className="control-section-heading">
        <div>
          <p className="eyebrow">CONTROL SNAPSHOT</p>
          <h3>What needs attention</h3>
        </div>

        <div className="control-section-status">
          <span></span>
          Live controller data
        </div>
      </section>

      <section className="command-grid">

        <button
          className="command-card exception-command"
          onClick={() => onNavigate("exceptions")}
        >
          <div className="command-card-top">
            <div className="command-icon danger">!</div>
            <span className="command-arrow">→</span>
          </div>

          <div className="command-value">
            {formatNumber(exceptionRecords)}
          </div>

          <strong>Financial Exceptions</strong>

          <span>Records requiring control attention</span>

          <div className="command-progress">
            <div
              style={{
                width: `${Math.min(
                  (Number(exceptionRecords) /
                    Math.max(Number(totalRecords), 1)) *
                    100,
                  100
                )}%`,
              }}
            ></div>
          </div>
        </button>


        <button
          className="command-card approval-command"
          onClick={() => onNavigate("approvals")}
        >
          <div className="command-card-top">
            <div className="command-icon orange">✓</div>
            <span className="command-arrow">→</span>
          </div>

          <div className="command-value">
            {formatNumber(approvalReady)}
          </div>

          <strong>Human Approvals</strong>

          <span>Financial actions awaiting review</span>

          <div className="command-meta">
            <span>REVIEW QUEUE</span>
            <b>{approvalReady > 0 ? "ACTION REQUIRED" : "CLEAR"}</b>
          </div>
        </button>


        <button
          className="command-card ai-command"
          onClick={() => onNavigate("ai")}
        >
          <div className="command-card-top">
            <div className="command-icon purple">AI</div>
            <span className="command-arrow">→</span>
          </div>

          <div className="command-value">
            {formatNumber(completedAI)}
          </div>

          <strong>AI Investigations</strong>

          <span>Automated financial investigations completed</span>

          <div className="command-meta">
            <span>COMPLETION</span>
            <b>{aiCompletionRate}%</b>
          </div>
        </button>


        <button
          className="command-card risk-command"
          onClick={() => onNavigate("exceptions")}
        >
          <div className="command-card-top">
            <div className="command-icon red">!</div>
            <span className="command-arrow">→</span>
          </div>

          <div className="command-value">
            {formatNumber(highSeverity)}
          </div>

          <strong>High Risk Exposure</strong>

          <span>Priority exceptions requiring attention</span>

          <div className="command-meta">
            <span>TOTAL RISK RECORDS</span>
            <b>{formatNumber(totalRisk)}</b>
          </div>
        </button>
      </section>


      {/* ======================================================
          CORE METRICS
          ====================================================== */}

      <section className="control-section-heading metrics-heading">
        <div>
          <p className="eyebrow">FINANCIAL CONTROL METRICS</p>
          <h3>Reconciliation performance</h3>
        </div>

        <button
          className="text-link"
          onClick={() => onNavigate("analytics")}
        >
          Open full analytics →
        </button>
      </section>

      <section className="stats-grid control-metrics-grid">
        <StatCard
          label="Total Records"
          value={formatNumber(totalRecords)}
          description="Financial records processed"
          icon="▣"
          onClick={() => onNavigate("analytics")}
        />

        <StatCard
          label="Matched Records"
          value={formatNumber(matchedRecords)}
          description="Successfully reconciled"
          icon="✓"
          tone="success"
          onClick={() => onNavigate("analytics")}
        />

        <StatCard
          label="Match Rate"
          value={`${matchRate}%`}
          description="Overall reconciliation health"
          icon="%"
          tone="blue"
          onClick={() => onNavigate("analytics")}
        />

        <StatCard
          label="Verified Actions"
          value={formatNumber(verified)}
          description="Sandbox actions verified"
          icon="✓"
          tone="success"
          onClick={() => onNavigate("actions")}
        />
      </section>


      {/* ======================================================
          RISK + AI
          ====================================================== */}

      <section className="analytics-grid control-analytics-grid">

        <div className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">RISK PROFILE</p>
              <h3>Exception Severity</h3>
            </div>

            <button
              className="panel-action"
              onClick={() => onNavigate("exceptions")}
            >
              Review →
            </button>
          </div>

          <div className="severity-container">
            <SeverityRow
              label="High"
              value={highSeverity}
              total={exceptionRecords}
              className="high"
            />

            <SeverityRow
              label="Medium"
              value={mediumSeverity}
              total={exceptionRecords}
              className="medium"
            />

            <SeverityRow
              label="Low"
              value={lowSeverity}
              total={exceptionRecords}
              className="low"
            />
          </div>

          <div className="severity-summary">
            <div>
              <strong>{highSeverity}</strong>
              <span>High Risk</span>
            </div>

            <div>
              <strong>{mediumSeverity}</strong>
              <span>Medium Risk</span>
            </div>

            <div>
              <strong>{lowSeverity}</strong>
              <span>Low Risk</span>
            </div>
          </div>
        </div>


        <div className="panel ai-panel">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">AI CONTROL ENGINE</p>
              <h3>Investigation Status</h3>
            </div>

            <div className="ai-badge">AI</div>
          </div>

          <div className="ai-status-main">
            <div className="ai-number">
              {formatNumber(completedAI)}
            </div>

            <div>
              <strong>Investigations completed</strong>

              <span>
                {failedAI === 0
                  ? "All queued investigations completed successfully."
                  : `${failedAI} investigation(s) require attention.`}
              </span>
            </div>
          </div>

          <div className="ai-progress">
            <div className="progress-track">
              <div
                className="ai-progress-fill"
                style={{
                  width: `${aiCompletionRate}%`,
                }}
              ></div>
            </div>
          </div>

          <div className="ai-footer">
            <span>Completed</span>
            <strong>{completedAI}</strong>

            <span>Failed</span>

            <strong
              className={
                failedAI > 0
                  ? "danger-text"
                  : "success-text"
              }
            >
              {failedAI}
            </strong>
          </div>

          <button
            className="ai-panel-action"
            onClick={() => onNavigate("ai")}
          >
            Open AI Investigation Center →
          </button>
        </div>
      </section>


      {/* ======================================================
          CONTROL PIPELINE
          ====================================================== */}

      <section className="panel pipeline-panel">
        <div className="panel-header">
          <div>
            <p className="panel-eyebrow">CONTROL PIPELINE</p>
            <h3>End-to-End Finance Workflow</h3>
          </div>

          <span className="pipeline-status">ACTIVE</span>
        </div>

        <div className="pipeline">
          <PipelineStep
            number="01"
            title="Validate"
            description="Validate financial data"
            completed
          />

          <PipelineConnector />

          <PipelineStep
            number="02"
            title="Reconcile"
            description="Match financial records"
            completed
          />

          <PipelineConnector />

          <PipelineStep
            number="03"
            title="Investigate"
            description="AI analyzes exceptions"
            completed
          />

          <PipelineConnector />

          <PipelineStep
            number="04"
            title="Approve"
            description={`${approvalReady} awaiting review`}
            active
          />

          <PipelineConnector />

          <PipelineStep
            number="05"
            title="Execute"
            description="Controlled sandbox action"
          />

          <PipelineConnector />

          <PipelineStep
            number="06"
            title="Verify"
            description="Confirm execution result"
          />
        </div>
      </section>


      {/* ======================================================
          QUICK ACTIONS
          ====================================================== */}

      <section className="quick-actions control-quick-actions">

        <button
          className="quick-action"
          onClick={() => onNavigate("exceptions")}
        >
          <span className="quick-action-icon">!</span>

          <div>
            <strong>Review Exceptions</strong>
            <span>
              Investigate {exceptionRecords} financial issues
            </span>
          </div>

          <b>→</b>
        </button>


        <button
          className="quick-action"
          onClick={() => onNavigate("approvals")}
        >
          <span className="quick-action-icon approval">✓</span>

          <div>
            <strong>Approval Queue</strong>
            <span>
              {approvalReady} actions awaiting review
            </span>
          </div>

          <b>→</b>
        </button>


        <button
          className="quick-action"
          onClick={() => onNavigate("actions")}
        >
          <span className="quick-action-icon ai">↗</span>

          <div>
            <strong>Controller Actions</strong>
            <span>
              Review controlled execution workflows
            </span>
          </div>

          <b>→</b>
        </button>


        <button
          className="quick-action"
          onClick={() => onNavigate("analytics")}
        >
          <span className="quick-action-icon">◫</span>

          <div>
            <strong>Control Analytics</strong>
            <span>
              Explore financial control metrics
            </span>
          </div>

          <b>→</b>
        </button>
      </section>


      {/* ======================================================
          FOOTER
          ====================================================== */}

      <footer className="dashboard-footer">
        <span>AI Finance Controller</span>

        <span>
          Financial Control &amp; Reconciliation Platform
        </span>

        <span>
          <i className="footer-status-dot"></i>
          API Connected
        </span>
      </footer>
    </main>
  );
}

/* ============================================================
   CONTROLLER ACTIONS
   ============================================================ */

function ControllerActions({ verifiedCount = 4, approvedCount = 3 }) {
  const [filter, setFilter] = useState("ALL");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState("EXC00005");

  const actions = [
    { id:"EXC00005", payment:"PAY00025", issue:"Missing Settlement", risk:"HIGH", status:"APPROVED", execution:"SANDBOX_EXECUTED", verification:"VERIFIED", action:"VERIFY_SETTLEMENT", amount:28148.20, reviewer:"FINANCE_REVIEWER", age:"18 min ago", description:"Settlement verification was approved and executed safely in the sandbox." },
    { id:"EXC00009", payment:"PAY00029", issue:"Invoice Mismatch", risk:"MEDIUM", status:"APPROVED", execution:"REVIEW_ONLY", verification:"PENDING", action:"REVIEW_INVOICE_DIFFERENCE", amount:42180.00, reviewer:"FINANCE_REVIEWER", age:"32 min ago", description:"Invoice difference is approved for review-only processing." },
    { id:"EXC00012", payment:"PAY00032", issue:"Amount Mismatch", risk:"HIGH", status:"PENDING", execution:"NOT_EXECUTED", verification:"PENDING", action:"REVIEW_AMOUNT_DIFFERENCE", amount:72535.57, reviewer:"—", age:"41 min ago", description:"Amount variance is awaiting human approval before controlled execution." },
    { id:"EXC00018", payment:"PAY00038", issue:"Duplicate Payment", risk:"HIGH", status:"READY", execution:"NOT_EXECUTED", verification:"PENDING", action:"HOLD_PAYMENT", amount:18500.00, reviewer:"—", age:"55 min ago", description:"Potential duplicate payment is ready for controller review." },
    { id:"EXC00024", payment:"PAY00044", issue:"Delayed Settlement", risk:"MEDIUM", status:"PENDING", execution:"NOT_EXECUTED", verification:"PENDING", action:"VERIFY_SETTLEMENT", amount:15420.75, reviewer:"—", age:"1 hr ago", description:"Settlement verification is awaiting approval." },
    { id:"EXC00031", payment:"PAY00051", issue:"Invoice Mismatch", risk:"LOW", status:"READY", execution:"NOT_EXECUTED", verification:"PENDING", action:"REVIEW_INVOICE_DIFFERENCE", amount:9275.00, reviewer:"—", age:"1 hr ago", description:"Low-risk invoice variance is ready for review." },
    { id:"EXC00037", payment:"PAY00057", issue:"Missing Settlement", risk:"HIGH", status:"APPROVED", execution:"SANDBOX_EXECUTED", verification:"VERIFIED", action:"VERIFY_SETTLEMENT", amount:60320.00, reviewer:"FINANCE_REVIEWER", age:"2 hrs ago", description:"Sandbox settlement verification completed and verified." },
    { id:"EXC00042", payment:"PAY00062", issue:"Amount Mismatch", risk:"MEDIUM", status:"APPROVED", execution:"SANDBOX_EXECUTED", verification:"PENDING", action:"REVIEW_AMOUNT_DIFFERENCE", amount:12980.40, reviewer:"FINANCE_REVIEWER", age:"2 hrs ago", description:"Approved action has been executed in the controlled sandbox." },
    { id:"EXC00051", payment:"PAY00071", issue:"Duplicate Payment", risk:"HIGH", status:"READY", execution:"NOT_EXECUTED", verification:"PENDING", action:"HOLD_PAYMENT", amount:44890.00, reviewer:"—", age:"3 hrs ago", description:"Duplicate payment control is ready for execution after approval." },
    { id:"EXC00064", payment:"PAY00084", issue:"Delayed Settlement", risk:"LOW", status:"VERIFIED", execution:"SANDBOX_EXECUTED", verification:"VERIFIED", action:"VERIFY_SETTLEMENT", amount:7640.00, reviewer:"FINANCE_REVIEWER", age:"4 hrs ago", description:"Controlled sandbox execution and verification completed." },
    { id:"EXC00081", payment:"PAY00101", issue:"Invoice Mismatch", risk:"LOW", status:"VERIFIED", execution:"REVIEW_ONLY", verification:"VERIFIED", action:"REVIEW_INVOICE_DIFFERENCE", amount:11200.00, reviewer:"FINANCE_REVIEWER", age:"Yesterday", description:"Review-only action was completed and verified." },
  ];

  const filtered = actions.filter((item) => {
    const haystack = `${item.id} ${item.payment} ${item.issue} ${item.action} ${item.execution} ${item.verification}`.toLowerCase();
    return haystack.includes(search.toLowerCase()) &&
      (filter === "ALL" || item.status === filter) &&
      (riskFilter === "ALL" || item.risk === riskFilter);
  });

  const selected = actions.find((item) => item.id === selectedId) || actions[0];
  const executed = actions.filter((x) => x.execution === "SANDBOX_EXECUTED").length;
  const verified = actions.filter((x) => x.verification === "VERIFIED").length;
  const pendingExecution = actions.filter((x) => x.execution === "NOT_EXECUTED").length;

  return (
    <main className="dashboard controller-actions-page">
      <section className="section-page-heading">
        <div>
          <p className="eyebrow">CONTROLLED EXECUTION</p>
          <h2>Controller Actions</h2>
          <p className="heading-description">Track approved financial actions through sandbox execution and final verification.</p>
        </div>
        <div className="page-status actions-page-status"><span></span>Execution control online</div>
      </section>

      <section className="actions-summary-grid">
        <ActionSummaryCard label="Approved" value={approvedCount} tone="blue" detail="Authorized actions" />
        <ActionSummaryCard label="Ready to Execute" value={pendingExecution} tone="orange" detail="Awaiting controlled execution" />
        <ActionSummaryCard label="Sandbox Executed" value={executed} tone="purple" detail="Execution completed" />
        <ActionSummaryCard label="Verified" value={verifiedCount || verified} tone="green" detail="Execution results verified" />
      </section>

      <section className="actions-workspace">
        <div className="actions-queue-panel">
          <div className="actions-toolbar">
            <div><p className="panel-eyebrow">ACTION QUEUE</p><h3>Controlled Actions</h3></div>
            <span className="actions-record-count">{filtered.length} records</span>
          </div>

          <div className="actions-filters">
            <div className="actions-search"><span>⌕</span><input value={search} onChange={(e)=>setSearch(e.target.value)} placeholder="Search exception, payment, action..." /></div>
            <select value={filter} onChange={(e)=>setFilter(e.target.value)}>
              <option value="ALL">All stages</option><option value="PENDING">Pending approval</option><option value="READY">Ready</option><option value="APPROVED">Approved</option><option value="VERIFIED">Verified</option>
            </select>
            <select value={riskFilter} onChange={(e)=>setRiskFilter(e.target.value)}>
              <option value="ALL">All risk</option><option value="HIGH">High</option><option value="MEDIUM">Medium</option><option value="LOW">Low</option>
            </select>
          </div>

          <div className="actions-list">
            {filtered.map((item) => (
              <button key={item.id} className={selectedId===item.id ? "action-row selected" : "action-row"} onClick={()=>setSelectedId(item.id)}>
                <div className={`action-marker ${item.risk.toLowerCase()}`}>{item.risk === "HIGH" ? "!" : item.risk === "MEDIUM" ? "•" : "✓"}</div>
                <div className="action-row-main">
                  <div className="action-row-top"><strong>{item.id}</strong><span className={`action-stage ${item.status.toLowerCase()}`}>{formatActionStatus(item.status)}</span></div>
                  <span className="action-row-issue">{item.issue}</span>
                  <div className="action-row-meta"><span>{item.action}</span><span>•</span><span>{item.payment}</span></div>
                </div>
                <div className="action-row-right"><strong>₹{item.amount.toLocaleString("en-IN", {minimumFractionDigits:2})}</strong><span>{item.execution === "SANDBOX_EXECUTED" ? "Executed" : item.execution === "REVIEW_ONLY" ? "Review only" : "Not executed"}</span></div>
                <span className="action-arrow">→</span>
              </button>
            ))}
          </div>
        </div>

        <ActionDetail action={selected} />
      </section>
    </main>
  );
}

function ActionSummaryCard({label,value,detail,tone}) {
  return <div className={`action-summary-card ${tone}`}><div><span className="action-summary-dot"></span>{label}</div><strong>{formatNumber(value)}</strong><small>{detail}</small></div>;
}

function ActionDetail({ action }) {
  const executionDone = action.execution === "SANDBOX_EXECUTED" || action.execution === "REVIEW_ONLY";
  const verificationDone = action.verification === "VERIFIED";
  const approved = ["APPROVED","VERIFIED"].includes(action.status);

  return (
    <div className="action-detail-panel">
      <div className="action-detail-header">
        <div><p className="panel-eyebrow">ACTION DETAIL</p><h3>{action.id}</h3><span>{action.payment} · {action.age}</span></div>
        <div className={`action-risk-badge ${action.risk.toLowerCase()}`}>{action.risk} RISK</div>
      </div>

      <div className="action-detail-status"><span className={`action-stage ${action.status.toLowerCase()}`}>{formatActionStatus(action.status)}</span><span className="action-live-dot"></span>Controlled workflow</div>

      <div className="action-flow">
        <ActionFlowStep number="01" label="Approval" state={approved ? "done" : "active"} text={approved ? "Approved" : "Awaiting approval"} />
        <span>→</span>
        <ActionFlowStep number="02" label="Execution" state={executionDone ? "done" : approved ? "active" : "locked"} text={action.execution === "REVIEW_ONLY" ? "Review only" : executionDone ? "Sandbox executed" : "Not executed"} />
        <span>→</span>
        <ActionFlowStep number="03" label="Verification" state={verificationDone ? "done" : executionDone ? "active" : "locked"} text={verificationDone ? "Verified" : "Pending"} />
      </div>

      <div className="action-detail-grid">
        <ActionDetailItem label="Exception" value={action.issue} />
        <ActionDetailItem label="Payment" value={action.payment} />
        <ActionDetailItem label="Amount" value={`₹${action.amount.toLocaleString("en-IN", {minimumFractionDigits:2})}`} />
        <ActionDetailItem label="Proposed Action" value={action.action} />
        <ActionDetailItem label="Reviewer" value={action.reviewer} />
        <ActionDetailItem label="Execution" value={action.execution} />
      </div>

      <div className="action-description"><p className="panel-eyebrow">CONTROL CONTEXT</p><p>{action.description}</p></div>

      <div className="action-status-banner">
        <div className={`action-banner-icon ${verificationDone ? "verified" : executionDone ? "executed" : approved ? "approved" : "pending"}`}>{verificationDone ? "✓" : executionDone ? "✓" : approved ? "✓" : "!"}</div>
        <div><strong>{verificationDone ? "Action Verified" : executionDone ? "Sandbox Execution Complete" : approved ? "Action Approved" : "Approval Required"}</strong><span>{verificationDone ? "The controlled execution result has been verified." : executionDone ? "The action has completed its controlled execution stage." : approved ? "The action is authorized and ready for controlled execution." : "Human approval is required before execution."}</span></div>
      </div>
    </div>
  );
}

function ActionFlowStep({number,label,state,text}) { return <div className={`action-flow-step ${state}`}><div>{state === "done" ? "✓" : number}</div><strong>{label}</strong><span>{text}</span></div>; }
function ActionDetailItem({label,value}) { return <div className="action-detail-item"><span>{label}</span><strong>{value}</strong></div>; }
function formatActionStatus(status) { return String(status || "").replaceAll("_", " "); }

/* ============================================================
   PLACEHOLDER PAGE
   ============================================================ */

function ApprovalCenter({
  pendingApprovals = 110,
  approvedApprovals = 2,
  readyForReview = 46,
  verifiedApprovals = 4,
}) {
  const [filter, setFilter] = useState("PENDING_APPROVAL");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState("EXC00005");

  const approvalRecords = [
    { id: "EXC00005", payment: "PAY00025", issue: "Missing Settlement", risk: "HIGH", status: "PENDING_APPROVAL", action: "VERIFY_SETTLEMENT", amount: 28148.20, reviewer: "—", age: "18 min ago", description: "Settlement record is missing for a completed payment." },
    { id: "EXC00009", payment: "PAY00029", issue: "Invoice Mismatch", risk: "MEDIUM", status: "APPROVED", action: "REVIEW_INVOICE_DIFFERENCE", amount: 42180.00, reviewer: "FINANCE_REVIEWER", age: "32 min ago", description: "Invoice amount differs from the recorded payment amount." },
    { id: "EXC00012", payment: "PAY00032", issue: "Amount Mismatch", risk: "HIGH", status: "PENDING_APPROVAL", action: "REVIEW_AMOUNT_DIFFERENCE", amount: 72535.57, reviewer: "—", age: "41 min ago", description: "Transaction amount requires human validation before action." },
    { id: "EXC00018", payment: "PAY00038", issue: "Duplicate Payment", risk: "HIGH", status: "READY_FOR_REVIEW", action: "HOLD_PAYMENT", amount: 18500.00, reviewer: "—", age: "55 min ago", description: "Potential duplicate payment detected by the control engine." },
    { id: "EXC00024", payment: "PAY00044", issue: "Delayed Settlement", risk: "MEDIUM", status: "PENDING_APPROVAL", action: "VERIFY_SETTLEMENT", amount: 15420.75, reviewer: "—", age: "1 hr ago", description: "Settlement has not arrived within the expected processing window." },
    { id: "EXC00031", payment: "PAY00051", issue: "Invoice Mismatch", risk: "LOW", status: "READY_FOR_REVIEW", action: "REVIEW_INVOICE_DIFFERENCE", amount: 9275.00, reviewer: "—", age: "1 hr ago", description: "Small invoice variance requires controller review." },
    { id: "EXC00037", payment: "PAY00057", issue: "Missing Settlement", risk: "HIGH", status: "PENDING_APPROVAL", action: "VERIFY_SETTLEMENT", amount: 60320.00, reviewer: "—", age: "2 hrs ago", description: "Payment exists but the settlement record is unavailable." },
    { id: "EXC00042", payment: "PAY00062", issue: "Amount Mismatch", risk: "MEDIUM", status: "PENDING_APPROVAL", action: "REVIEW_AMOUNT_DIFFERENCE", amount: 12980.40, reviewer: "—", age: "2 hrs ago", description: "Reconciled values differ and need human confirmation." },
    { id: "EXC00051", payment: "PAY00071", issue: "Duplicate Payment", risk: "HIGH", status: "READY_FOR_REVIEW", action: "HOLD_PAYMENT", amount: 44890.00, reviewer: "—", age: "3 hrs ago", description: "A matching payment pattern was flagged as a duplicate." },
    { id: "EXC00064", payment: "PAY00084", issue: "Delayed Settlement", risk: "LOW", status: "APPROVED", action: "VERIFY_SETTLEMENT", amount: 7640.00, reviewer: "FINANCE_REVIEWER", age: "4 hrs ago", description: "Settlement delay reviewed and approved for controlled verification." },
    { id: "EXC00072", payment: "PAY00092", issue: "Missing Settlement", risk: "MEDIUM", status: "PENDING_APPROVAL", action: "VERIFY_SETTLEMENT", amount: 33210.90, reviewer: "—", age: "5 hrs ago", description: "Settlement requires a controller decision." },
    { id: "EXC00081", payment: "PAY00101", issue: "Invoice Mismatch", risk: "LOW", status: "VERIFIED", action: "REVIEW_INVOICE_DIFFERENCE", amount: 11200.00, reviewer: "FINANCE_REVIEWER", age: "Yesterday", description: "Invoice difference was reviewed and the controlled action verified." },
  ];

  const visibleRecords = approvalRecords.filter((item) => {
    const haystack = `${item.id} ${item.payment} ${item.issue} ${item.action} ${item.status}`.toLowerCase();
    return (
      haystack.includes(search.toLowerCase()) &&
      (filter === "ALL" || item.status === filter) &&
      (riskFilter === "ALL" || item.risk === riskFilter)
    );
  });

  const selected = approvalRecords.find((item) => item.id === selectedId) || approvalRecords[0];

  const statusCounts = {
    PENDING_APPROVAL: pendingApprovals,
    READY_FOR_REVIEW: readyForReview,
    APPROVED: approvedApprovals,
    VERIFIED: verifiedApprovals,
  };

  return (
    <main className="dashboard approval-page">
      <section className="section-page-heading">
        <div>
          <p className="eyebrow">HUMAN CONTROL</p>
          <h2>Approval Center</h2>
          <p className="heading-description">
            Review financial actions, assess control risk, and authorize approved workflows before execution.
          </p>
        </div>
        <div className="page-status approval-page-status">
          <span></span>
          Human review queue
        </div>
      </section>

      <section className="approval-summary-grid">
        <ApprovalSummary label="Pending Approval" value={pendingApprovals} tone="orange" active={filter === "PENDING_APPROVAL"} onClick={() => setFilter("PENDING_APPROVAL")} />
        <ApprovalSummary label="Ready for Review" value={readyForReview} tone="blue" active={filter === "READY_FOR_REVIEW"} onClick={() => setFilter("READY_FOR_REVIEW")} />
        <ApprovalSummary label="Approved" value={approvedApprovals} tone="green" active={filter === "APPROVED"} onClick={() => setFilter("APPROVED")} />
        <ApprovalSummary label="Verified" value={verifiedApprovals} tone="purple" active={filter === "VERIFIED"} onClick={() => setFilter("VERIFIED")} />
      </section>

      <section className="approval-workspace">
        <div className="approval-queue-panel">
          <div className="approval-panel-header">
            <div>
              <p className="panel-eyebrow">APPROVAL QUEUE</p>
              <h3>Financial Actions</h3>
            </div>
            <span className="approval-total">{statusCounts[filter] ?? approvalRecords.length} records</span>
          </div>

          <div className="approval-filters">
            <div className="approval-search">
              <span>⌕</span>
              <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search exception, payment, action..." />
            </div>
            <select value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="ALL">All statuses</option>
              <option value="PENDING_APPROVAL">Pending approval</option>
              <option value="READY_FOR_REVIEW">Ready for review</option>
              <option value="APPROVED">Approved</option>
              <option value="VERIFIED">Verified</option>
            </select>
            <select value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
              <option value="ALL">All risk</option>
              <option value="HIGH">High risk</option>
              <option value="MEDIUM">Medium risk</option>
              <option value="LOW">Low risk</option>
            </select>
          </div>

          <div className="approval-list">
            {visibleRecords.map((item) => (
              <button key={item.id} className={`approval-row ${selectedId === item.id ? "selected" : ""}`} onClick={() => setSelectedId(item.id)}>
                <div className={`approval-risk-icon ${item.risk.toLowerCase()}`}>{item.risk === "HIGH" ? "!" : item.risk === "MEDIUM" ? "•" : "✓"}</div>
                <div className="approval-row-main">
                  <div className="approval-row-title">
                    <strong>{item.id}</strong>
                    <span className={`approval-status ${item.status.toLowerCase()}`}>{formatApprovalStatus(item.status)}</span>
                  </div>
                  <span className="approval-row-issue">{item.issue}</span>
                  <div className="approval-row-meta"><span>{item.payment}</span><span>•</span><span>{item.action}</span><span>•</span><span>{item.age}</span></div>
                </div>
                <div className="approval-row-amount">₹{item.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</div>
                <span className="approval-row-arrow">→</span>
              </button>
            ))}
            {visibleRecords.length === 0 && (
              <div className="approval-empty"><div>✓</div><strong>No approval records found</strong><span>Try changing the status, risk filter, or search term.</span></div>
            )}
          </div>
        </div>

        <ApprovalDetail approval={selected} />
      </section>
    </main>
  );
}

function ApprovalSummary({ label, value, tone, active, onClick }) {
  return (
    <button className={`approval-summary-card ${tone} ${active ? "active" : ""}`} onClick={onClick}>
      <div className="approval-summary-top"><span className="approval-summary-dot"></span><span>{label}</span></div>
      <strong>{formatNumber(value)}</strong>
      <small>Human control workflow</small>
    </button>
  );
}

function ApprovalDetail({ approval }) {
  if (!approval) return null;

  const isPending = approval.status === "PENDING_APPROVAL" || approval.status === "READY_FOR_REVIEW";
  const isApproved = approval.status === "APPROVED" || approval.status === "VERIFIED";
  const isVerified = approval.status === "VERIFIED";

  return (
    <div className="approval-detail-panel">
      <div className="approval-detail-header">
        <div>
          <p className="panel-eyebrow">APPROVAL DETAIL</p>
          <h3>{approval.id}</h3>
          <span>Payment {approval.payment}</span>
        </div>
        <span className={`approval-risk-badge ${approval.risk.toLowerCase()}`}>{approval.risk} RISK</span>
      </div>

      <div className="approval-detail-status-row">
        <span className={`approval-status ${approval.status.toLowerCase()}`}>{formatApprovalStatus(approval.status)}</span>
        <span className="approval-age">{approval.age}</span>
      </div>

      <div className="approval-detail-grid">
        <ApprovalDetailItem label="Exception" value={approval.issue} />
        <ApprovalDetailItem label="Payment" value={approval.payment} />
        <ApprovalDetailItem label="Amount" value={`₹${approval.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`} />
        <ApprovalDetailItem label="Proposed Action" value={approval.action} />
      </div>

      <div className="approval-detail-section">
        <p className="panel-eyebrow">CONTROL ASSESSMENT</p>
        <h4>Why this requires approval</h4>
        <p>{approval.description}</p>
      </div>

      <div className="approval-flow">
        <ApprovalStep number="01" label="AI Analysis" state="complete" text="Finding assessed" />
        <span className="approval-flow-line"></span>
        <ApprovalStep number="02" label="Human Approval" state={isApproved ? "complete" : "current"} text={isApproved ? "Decision recorded" : "Decision required"} />
        <span className="approval-flow-line"></span>
        <ApprovalStep number="03" label="Execution" state={isVerified ? "complete" : "pending"} text={isVerified ? "Verified" : "Awaiting action"} />
      </div>

      <div className={`approval-decision-box ${isApproved ? "approved" : "pending"}`}>
        <div className="approval-decision-icon">{isApproved ? "✓" : "!"}</div>
        <div>
          <strong>{isVerified ? "Action Verified" : isApproved ? "Action Approved" : "Human Decision Required"}</strong>
          <p>{isVerified ? "The controlled action has completed its verification stage." : isApproved ? `Reviewed by ${approval.reviewer}. The controlled action is authorized for the next stage.` : "This financial action is waiting for an authorized reviewer."}</p>
        </div>
        <span className="approval-reviewer">{approval.reviewer === "—" ? "UNASSIGNED" : approval.reviewer}</span>
      </div>

      {isPending && (
        <div className="approval-detail-actions">
          <button className="approval-secondary-button">Review Evidence</button>
          <button className="approval-primary-button">Review & Approve →</button>
        </div>
      )}
    </div>
  );
}

function ApprovalDetailItem({ label, value }) {
  return <div className="approval-detail-item"><span>{label}</span><strong>{value}</strong></div>;
}

function ApprovalStep({ number, label, state, text }) {
  return <div className={`approval-step ${state}`}><div className="approval-step-number">{state === "complete" ? "✓" : number}</div><strong>{label}</strong><span>{text}</span></div>;
}

function formatApprovalStatus(status) {
  return String(status || "").replaceAll("_", " ");
}


/* ============================================================
   CONTROL ANALYTICS
   ============================================================ */

function ControlAnalytics({
  summary,
  exceptions,
  severity,
  aiInvestigations,
  approvals,
  matchRate,
  totalRecords,
  matchedRecords,
  exceptionRecords,
  completedAI,
  failedAI,
  pendingApprovals,
  verified,
}) {
  const high = Number(severity.HIGH || 0);
  const medium = Number(severity.MEDIUM || 0);
  const low = Number(severity.LOW || 0);

  const exceptionTypes = [
    ["Amount Mismatch", exceptions.AMOUNT_MISMATCH || 0],
    ["Invoice Mismatch", exceptions.INVOICE_MISMATCH || 0],
    ["Missing Settlement", exceptions.MISSING_SETTLEMENT || 0],
    ["Delayed Settlement", exceptions.DELAYED_SETTLEMENT || 0],
    ["Duplicate Payment", exceptions.DUPLICATE_PAYMENT || 0],
    ["Settlement + Duplicate", exceptions["MISSING_SETTLEMENT;DUPLICATE_PAYMENT"] || 0],
  ];

  const maxException = Math.max(
    ...exceptionTypes.map(([, value]) => Number(value)),
    1
  );

  const totalSeverity = high + medium + low;
  const approvalTotal =
    Number(approvals.PENDING_APPROVAL || 0) +
    Number(approvals.READY_FOR_REVIEW || 0) +
    Number(approvals.APPROVED || 0) +
    Number(approvals.VERIFIED || 0);

  const completedPct =
    completedAI + failedAI > 0
      ? Math.round((completedAI / (completedAI + failedAI)) * 100)
      : 100;

  return (
    <main className="dashboard analytics-page">
      <section className="section-page-heading">
        <div>
          <p className="eyebrow">FINANCIAL INTELLIGENCE</p>
          <h2>TEST ANALYTICS PAGE</h2>
          <p className="heading-description">
            Understand reconciliation health, exception patterns, risk exposure,
            AI performance, and the human control pipeline.
          </p>
        </div>

        <div className="page-status analytics-status">
          <span></span>
          Live control metrics
        </div>
      </section>

      <section className="analytics-kpi-grid">
        <AnalyticsKpi
          label="Reconciliation Rate"
          value={`${matchRate}%`}
          description={`${formatNumber(matchedRecords)} of ${formatNumber(totalRecords)} records matched`}
          tone="blue"
        />
        <AnalyticsKpi
          label="Exceptions"
          value={exceptionRecords}
          description="Financial records requiring attention"
          tone="orange"
        />
        <AnalyticsKpi
          label="AI Investigations"
          value={completedAI}
          description={`${completedPct}% completion rate`}
          tone="purple"
        />
        <AnalyticsKpi
          label="Pending Controls"
          value={pendingApprovals}
          description="Awaiting human financial review"
          tone="red"
        />
      </section>

      <section className="analytics-main-grid">
        <div className="analytics-card reconciliation-card">
          <AnalyticsCardHeading
            eyebrow="RECONCILIATION"
            title="Financial Control Health"
            right={`${matchRate}%`}
          />

          <div className="health-meter">
            <div
              className="health-meter-fill"
              style={{ width: `${Math.min(Number(matchRate), 100)}%` }}
            ></div>
          </div>

          <div className="health-center">
            <strong>{matchRate}%</strong>
            <span>Overall reconciliation rate</span>
          </div>

          <div className="health-breakdown">
            <AnalyticsMetric label="Matched" value={matchedRecords} tone="green" />
            <AnalyticsMetric label="Exceptions" value={exceptionRecords} tone="red" />
            <AnalyticsMetric label="Total Records" value={totalRecords} />
          </div>
        </div>

        <div className="analytics-card">
          <AnalyticsCardHeading
            eyebrow="RISK PROFILE"
            title="Exception Severity"
            right={`${formatNumber(totalSeverity)} total`}
          />

          <div className="severity-visual">
            <div
              className="severity-ring"
              style={{
                background: `conic-gradient(
                  var(--red) 0 ${(high / Math.max(totalSeverity, 1)) * 100}%,
                  var(--orange) ${(high / Math.max(totalSeverity, 1)) * 100}% ${((high + medium) / Math.max(totalSeverity, 1)) * 100}%,
                  var(--green) ${((high + medium) / Math.max(totalSeverity, 1)) * 100}% 100%
                )`,
              }}
            >
              <div>
                <strong>{formatNumber(totalSeverity)}</strong>
                <span>exceptions</span>
              </div>
            </div>

            <div className="severity-legend">
              <AnalyticsSeverityRow label="High Risk" value={high} tone="red" total={totalSeverity} />
              <AnalyticsSeverityRow label="Medium Risk" value={medium} tone="orange" total={totalSeverity} />
              <AnalyticsSeverityRow label="Low Risk" value={low} tone="green" total={totalSeverity} />
            </div>
          </div>
        </div>
      </section>

      <section className="analytics-two-column">
        <div className="analytics-card">
          <AnalyticsCardHeading
            eyebrow="EXCEPTION ANALYSIS"
            title="Exception Distribution"
            right={`${formatNumber(exceptionRecords)} total`}
          />

          <div className="exception-bars">
            {exceptionTypes.map(([label, value]) => {
              const numericValue = Number(value);
              const percentage = Math.round(
                (numericValue / Math.max(exceptionRecords, 1)) * 100
              );

              return (
                <div className="exception-bar-row" key={label}>
                  <div className="exception-bar-label">
                    <span>{label}</span>
                    <strong>{numericValue}</strong>
                  </div>
                  <div className="exception-bar-track">
                    <div
                      className="exception-bar-fill"
                      style={{
                        width: `${(numericValue / maxException) * 100}%`,
                      }}
                    ></div>
                  </div>
                  <small>{percentage}%</small>
                </div>
              );
            })}
          </div>
        </div>

        <div className="analytics-card">
          <AnalyticsCardHeading
            eyebrow="CONTROL PIPELINE"
            title="Approval Activity"
            right={`${formatNumber(approvalTotal)} actions`}
          />

          <div className="pipeline-list">
            <PipelineRow
              number="01"
              label="Pending Approval"
              value={approvals.PENDING_APPROVAL || 0}
              tone="orange"
            />
            <PipelineRow
              number="02"
              label="Ready for Review"
              value={approvals.READY_FOR_REVIEW || 0}
              tone="blue"
            />
            <PipelineRow
              number="03"
              label="Approved"
              value={approvals.APPROVED || 0}
              tone="purple"
            />
            <PipelineRow
              number="04"
              label="Verified"
              value={approvals.VERIFIED || 0}
              tone="green"
            />
          </div>
        </div>
      </section>

      <section className="analytics-bottom-grid">
        <div className="analytics-card ai-performance-card">
          <AnalyticsCardHeading
            eyebrow="AI CONTROL ENGINE"
            title="Investigation Performance"
            right={`${formatNumber(completedAI + failedAI)} processed`}
          />

          <div className="ai-performance">
            <div className="ai-performance-score">
              <div className="ai-score-ring">
                <strong>{completedPct}%</strong>
              </div>
              <div>
                <strong>Investigation completion</strong>
                <span>AI findings processed by the control engine</span>
              </div>
            </div>

            <div className="ai-performance-stats">
              <AnalyticsMetric label="Completed" value={completedAI} tone="green" />
              <AnalyticsMetric label="Failed" value={failedAI} tone="red" />
              <AnalyticsMetric label="Verified Actions" value={verified} tone="purple" />
            </div>
          </div>
        </div>

        <div className="analytics-card insight-card">
          <div className="insight-icon">◈</div>
          <p className="panel-eyebrow">CONTROL INSIGHT</p>
          <h3>Reconciliation remains the primary health indicator.</h3>
          <p>
            {matchRate}% of financial records are currently reconciled. The
            remaining {formatNumber(exceptionRecords)} exception records are
            distributed across {formatNumber(totalSeverity)} severity-classified
            control findings.
          </p>
          <div className="insight-tags">
            <span>{high} high risk</span>
            <span>{pendingApprovals} pending review</span>
            <span>{completedAI} AI completed</span>
          </div>
        </div>
      </section>
    </main>
  );
}

function AnalyticsKpi({ label, value, description, tone = "blue" }) {
  return (
    <div className={`analytics-kpi ${tone}`}>
      <div className="analytics-kpi-label">
        <span></span>
        {label}
      </div>
      <strong>{typeof value === "string" ? value : formatNumber(value)}</strong>
      <small>{description}</small>
    </div>
  );
}

function AnalyticsCardHeading({ eyebrow, title, right }) {
  return (
    <div className="analytics-card-heading">
      <div>
        <p className="panel-eyebrow">{eyebrow}</p>
        <h3>{title}</h3>
      </div>
      {right && <span>{right}</span>}
    </div>
  );
}

function AnalyticsMetric({ label, value, tone = "" }) {
  return (
    <div className={`analytics-metric ${tone}`}>
      <span>{label}</span>
      <strong>{formatNumber(value)}</strong>
    </div>
  );
}

function AnalyticsSeverityRow({ label, value, tone, total }) {
  const percentage = Math.round((Number(value) / Math.max(total, 1)) * 100);

  return (
    <div className="severity-row">
      <div>
        <span className={`severity-dot ${tone}`}></span>
        <span>{label}</span>
      </div>
      <strong>{formatNumber(value)}</strong>
      <small>{percentage}%</small>
    </div>
  );
}

function PipelineRow({ number, label, value, tone }) {
  return (
    <div className="pipeline-row">
      <span className={`pipeline-number ${tone}`}>{number}</span>
      <div className="pipeline-info">
        <strong>{label}</strong>
        <div>
          <span className={`pipeline-dot ${tone}`}></span>
          Control workflow
        </div>
      </div>
      <strong className="pipeline-value">{formatNumber(value)}</strong>
    </div>
  );
}


function PlaceholderPage({
  eyebrow,
  title,
  description,
  icon,
  metric,
  metricLabel,
  secondaryMetric,
  secondaryLabel,
  color = "blue",
}) {
  return (
    <main className="dashboard">
      <section className="section-page-heading">
        <div>
          <p className="eyebrow">{eyebrow}</p>

          <h2>{title}</h2>

          <p className="heading-description">
            {description}
          </p>
        </div>

        <div className="page-status">
          <span></span>
          Module ready
        </div>
      </section>

      <section className="module-hero">
        <div className={`module-icon ${color}`}>
          {icon}
        </div>

        <div className="module-copy">
          <p className="panel-eyebrow">
            CONTROL MODULE
          </p>

          <h3>{title}</h3>

          <p>
            This module is connected to the Finance
            Controller architecture and is ready for the
            next implementation stage.
          </p>

          <div className="module-badge">
            Backend connected
          </div>
        </div>
      </section>

      <section className="module-metrics">
        <div className="module-metric-card">
          <span>{metricLabel}</span>

          <strong>{formatNumber(metric)}</strong>

          <small>Live controller data</small>
        </div>

        <div className="module-metric-card">
          <span>{secondaryLabel}</span>

          <strong>
            {formatNumber(secondaryMetric)}
          </strong>

          <small>Live controller data</small>
        </div>

        <div className="module-metric-card">
          <span>System Status</span>

          <strong className="success-text">
            ONLINE
          </strong>

          <small>API responding normally</small>
        </div>
      </section>

      <section className="module-roadmap">
        <div>
          <p className="panel-eyebrow">
            NEXT DEVELOPMENT STAGE
          </p>

          <h3>Module capabilities</h3>
        </div>

        <div className="roadmap-grid">
          <RoadmapItem
            title="Live Data"
            description="Connected to the existing finance controller API."
            completed
          />

          <RoadmapItem
            title="Advanced Filtering"
            description="Filter and search operational records."
          />

          <RoadmapItem
            title="Detailed Analytics"
            description="Visualize control metrics and trends."
          />

          <RoadmapItem
            title="Workflow Actions"
            description="Execute the appropriate controlled workflow."
          />
        </div>
      </section>
    </main>
  );
}

/* ============================================================
   ROADMAP ITEM
   ============================================================ */

function RoadmapItem({
  title,
  description,
  completed = false,
}) {
  return (
    <div className="roadmap-item">
      <div
        className={
          completed
            ? "roadmap-check completed"
            : "roadmap-check"
        }
      >
        {completed ? "✓" : "○"}
      </div>

      <div>
        <strong>{title}</strong>

        <span>{description}</span>
      </div>
    </div>
  );
}

/* ============================================================
   STAT CARD
   ============================================================ */

function StatCard({
  label,
  value,
  description,
  icon,
  tone = "",
  onClick,
}) {
  return (
    <button
      className={`stat-card ${tone}`}
      onClick={onClick}
    >
      <div className="stat-top">
        <div className="stat-icon">{icon}</div>

        <span className="stat-label">{label}</span>

        <span className="stat-arrow">↗</span>
      </div>

      <div className="stat-value">{value}</div>

      <div className="stat-description">
        {description}
      </div>
    </button>
  );
}

/* ============================================================
   EXCEPTION ROW
   ============================================================ */

function ExceptionRow({
  label,
  value,
  total,
}) {
  const percentage =
    total > 0
      ? Math.min((value / total) * 100, 100)
      : 0;

  return (
    <div className="exception-row">
      <div className="exception-row-top">
        <span>{label}</span>

        <strong>{value}</strong>
      </div>

      <div className="mini-progress">
        <div
          style={{
            width: `${percentage}%`,
          }}
        ></div>
      </div>
    </div>
  );
}

/* ============================================================
   SEVERITY ROW
   ============================================================ */

function SeverityRow({
  label,
  value,
  total,
  className,
}) {
  const percentage =
    total > 0
      ? Math.min((value / total) * 100, 100)
      : 0;

  return (
    <div className="severity-row">
      <div className="severity-label">
        <span
          className={`severity-dot ${className}`}
        ></span>

        <span>{label}</span>

        <strong>{value}</strong>
      </div>

      <div className="severity-track">
        <div
          className={`severity-fill ${className}`}
          style={{
            width: `${percentage}%`,
          }}
        ></div>
      </div>
    </div>
  );
}

/* ============================================================
   PIPELINE STEP
   ============================================================ */

function PipelineStep({
  number,
  title,
  description,
  completed = false,
  active = false,
}) {
  return (
    <div
      className={`pipeline-step ${
        completed ? "completed" : ""
      } ${active ? "active" : ""}`}
    >
      <div className="pipeline-number">
        {completed ? "✓" : number}
      </div>

      <strong>{title}</strong>

      <span>{description}</span>
    </div>
  );
}

/* ============================================================
   PIPELINE CONNECTOR
   ============================================================ */

function PipelineConnector() {
  return (
    <div className="pipeline-connector">
      →
    </div>
  );
}

/* ============================================================
   NUMBER FORMAT
   ============================================================ */

function formatNumber(value) {
  return Number(value || 0).toLocaleString(
    "en-IN"
  );
}

export default App;