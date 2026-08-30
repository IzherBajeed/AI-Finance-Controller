
import { useEffect, useState } from "react";
import "./ExceptionQueue.css";

const API_BASE = "http://127.0.0.1:5000/api";
const PAGE_SIZE = 20;


/* ========================================================= */
/* MAIN COMPONENT */
/* ========================================================= */

function ExceptionQueue() {

  const [exceptions, setExceptions] = useState([]);
  const [pagination, setPagination] = useState(null);

  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);

  const [error, setError] = useState("");

  const [page, setPage] = useState(1);

  const [severity, setSeverity] = useState("");
  const [issue, setIssue] = useState("");
  const [search, setSearch] = useState("");

  const [selectedException, setSelectedException] =
    useState(null);

  const [actionLoading, setActionLoading] =
    useState(false);

  const [actionMessage, setActionMessage] =
    useState("");

  const [reviewer, setReviewer] =
    useState("FINANCE_REVIEWER");

  const [comments, setComments] =
    useState(
      "Approved for controlled sandbox execution."
    );


  /*
   * Keep the open exception modal synchronized with the backend.
   * This is especially useful when an action is executed or verified
   * from another terminal / browser action.
   */
  useEffect(() => {

    if (!selectedException) {
      return;
    }

    const exceptionId =
      selectedException.exception?.exception_id;

    if (!exceptionId) {
      return;
    }

    const intervalId =
      setInterval(() => {

        refreshSelectedException(
          exceptionId
        ).catch((err) => {
          console.error(
            "Live action refresh failed:",
            err
          );
        });

      }, 3000);

    return () => {
      clearInterval(intervalId);
    };

  }, [
    selectedException?.exception?.exception_id
  ]);


  /* ======================================================= */
  /* LOAD EXCEPTIONS */
  /* ======================================================= */

  useEffect(() => {
    loadExceptions();
  }, [page, severity, issue]);


  async function loadExceptions() {

    try {

      setLoading(true);
      setError("");

      const params =
        new URLSearchParams();

      params.set("page", page);
      params.set("limit", PAGE_SIZE);

      if (severity) {
        params.set(
          "severity",
          severity
        );
      }

      if (issue) {
        params.set(
          "issue",
          issue
        );
      }


      const response =
        await fetch(
          `${API_BASE}/exceptions?${params.toString()}`
        );


      if (!response.ok) {
        throw new Error(
          `API request failed: ${response.status}`
        );
      }


      const data =
        await response.json();


      if (!data.success) {
        throw new Error(
          "Exception API returned an unsuccessful response."
        );
      }


      setExceptions(
        data.exceptions || []
      );

      setPagination(
        data.pagination || null
      );

    } catch (err) {

      console.error(err);

      setError(
        "Unable to load the exception queue."
      );

    } finally {

      setLoading(false);

    }
  }


  /* ======================================================= */
  /* SEARCH ALL EXCEPTIONS */
  /* ======================================================= */

  async function searchAllExceptions(
    query
  ) {

    const cleanQuery =
      query.trim().toLowerCase();


    if (!cleanQuery) {
      setPage(1);
      return;
    }


    try {

      setSearching(true);
      setError("");


      const firstParams =
        new URLSearchParams();

      firstParams.set(
        "page",
        "1"
      );

      firstParams.set(
        "limit",
        PAGE_SIZE
      );


      if (severity) {
        firstParams.set(
          "severity",
          severity
        );
      }


      if (issue) {
        firstParams.set(
          "issue",
          issue
        );
      }


      const firstResponse =
        await fetch(
          `${API_BASE}/exceptions?${firstParams.toString()}`
        );


      if (!firstResponse.ok) {
        throw new Error(
          "Unable to search exceptions."
        );
      }


      const firstData =
        await firstResponse.json();


      if (!firstData.success) {
        throw new Error(
          "Exception search failed."
        );
      }


      const totalPages =
        firstData.pagination?.total_pages ||
        1;


      let allRecords =
        firstData.exceptions || [];


      if (totalPages > 1) {

        const requests = [];


        for (
          let currentPage = 2;
          currentPage <= totalPages;
          currentPage++
        ) {

          const params =
            new URLSearchParams();

          params.set(
            "page",
            currentPage
          );

          params.set(
            "limit",
            PAGE_SIZE
          );


          if (severity) {
            params.set(
              "severity",
              severity
            );
          }


          if (issue) {
            params.set(
              "issue",
              issue
            );
          }


          requests.push(
            fetch(
              `${API_BASE}/exceptions?${params.toString()}`
            )
          );

        }


        const responses =
          await Promise.all(
            requests
          );


        for (
          const response
          of responses
        ) {

          if (!response.ok) {
            continue;
          }


          const data =
            await response.json();


          if (
            data.success &&
            Array.isArray(
              data.exceptions
            )
          ) {

            allRecords = [
              ...allRecords,
              ...data.exceptions,
            ];

          }

        }

      }


      const results =
        allRecords.filter(
          (exception) =>
            matchesSearch(
              exception,
              cleanQuery
            )
        );


      setExceptions(results);


      setPagination({
        page: 1,
        limit: results.length,
        returned_records:
          results.length,
        total_pages: 1,
        total_records:
          results.length,
      });


    } catch (err) {

      console.error(err);

      setError(
        "Unable to search the exception queue."
      );

    } finally {

      setSearching(false);

    }

  }


  /* ======================================================= */
  /* SEARCH MATCH */
  /* ======================================================= */

  function matchesSearch(
    exception,
    query
  ) {

    const searchableFields = [

      exception.exception_id,
      exception.payment_id,
      exception.transaction_id,
      exception.customer_id,
      exception.invoice_id,
      exception.issues,
      exception.severity,
      exception.workflow,
      exception.payment_method,
      exception.recommended_action,
      exception.proposed_action,

    ];


    return searchableFields.some(
      (value) =>
        String(value || "")
          .toLowerCase()
          .includes(query)
    );

  }


  /* ======================================================= */
  /* SEARCH HANDLER */
  /* ======================================================= */

  function handleSearchChange(
    event
  ) {

    const value =
      event.target.value;


    setSearch(value);


    if (!value.trim()) {

      setPage(1);

      return;

    }


    searchAllExceptions(
      value
    );

  }


  /* ======================================================= */
  /* FILTERS */
  /* ======================================================= */

  function handleSeverityChange(
    event
  ) {

    setSeverity(
      event.target.value
    );

    setPage(1);
    setSearch("");

  }


  function handleIssueChange(
    event
  ) {

    setIssue(
      event.target.value
    );

    setPage(1);
    setSearch("");

  }


  function clearFilters() {

    setSeverity("");
    setIssue("");
    setSearch("");
    setPage(1);

  }


  /* ======================================================= */
  /* OPEN EXCEPTION */
  /* ======================================================= */

  async function openException(
    exceptionId
  ) {

    try {

      setError("");
      setActionMessage("");

      const response =
        await fetch(
          `${API_BASE}/exceptions/${exceptionId}`
        );


      if (!response.ok) {

        throw new Error(
          `Failed to load exception: ${response.status}`
        );

      }


      const data =
        await response.json();


      if (!data.success) {

        throw new Error(
          "Exception details could not be loaded."
        );

      }


      setSelectedException(
        data
      );

    } catch (err) {

      console.error(err);

      setError(
        "Unable to load exception details."
      );

    }

  }


  /* ======================================================= */
  /* REFRESH SELECTED EXCEPTION */
  /* ======================================================= */

  async function refreshSelectedException(
    exceptionId
  ) {

    /*
     * IMPORTANT:
     * The exception endpoint contains the exception snapshot, but the
     * controller action endpoint is the authoritative source for the
     * approval / execution / verification workflow.
     *
     * After APPROVE / EXECUTE / VERIFY, fetch BOTH endpoints and merge
     * the latest controller action into the selected exception.
     */

    const [exceptionResponse, actionResponse] =
      await Promise.all([
        fetch(
          `${API_BASE}/exceptions/${exceptionId}`,
          { cache: "no-store" }
        ),
        fetch(
          `${API_BASE}/controller/actions/${exceptionId}`,
          { cache: "no-store" }
        ),
      ]);


    if (!exceptionResponse.ok) {
      throw new Error(
        "Unable to refresh exception."
      );
    }


    const data =
      await exceptionResponse.json();


    if (!data.success) {
      throw new Error(
        "Unable to refresh exception."
      );
    }


    let latestAction =
      data.action || {};


    /*
     * The controller action endpoint is the source of truth.
     * If it is available, always prefer its action object.
     */
    if (actionResponse.ok) {

      const actionData =
        await actionResponse.json();

      if (
        actionData &&
        actionData.success &&
        actionData.action
      ) {
        latestAction =
          actionData.action;
      }
    }


    setSelectedException({
      ...data,
      action: {
        ...(data.action || {}),
        ...latestAction,
      },
    });

  }


  /* ======================================================= */
  /* APPROVE */
  /* ======================================================= */

  async function approveAction() {

    if (!selectedException) {
      return;
    }


    const exceptionId =
      selectedException.exception
        ?.exception_id;


    if (!exceptionId) {
      return;
    }


    try {

      setActionLoading(true);
      setActionMessage("");
      setError("");


      const response =
        await fetch(
          `${API_BASE}/controller/actions/${exceptionId}/approve`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              reviewer:
                reviewer.trim() ||
                "FINANCE_REVIEWER",

              comments:
                comments.trim() ||
                "Approved for controlled sandbox execution.",
            }),

          }
        );


      const data =
        await response.json();


      if (!response.ok || !data.success) {

        throw new Error(
          data.error ||
          data.message ||
          "Approval failed."
        );

      }


      setActionMessage(
        "Action approved successfully."
      );


      await refreshSelectedException(
        exceptionId
      );


    } catch (err) {

      console.error(err);

      setError(
        err.message ||
        "Unable to approve this action."
      );

    } finally {

      setActionLoading(false);

    }

  }


  /* ======================================================= */
  /* EXECUTE */
  /* ======================================================= */

  async function executeAction() {
  if (!selectedException) {
    return;
  }

  const exceptionId =
    selectedException.exception?.exception_id;

  if (!exceptionId) {
    return;
  }

  const selectedAction =
    String(
      selectedException.action?.proposed_action || ""
    ).toUpperCase();

  const selectedExecutionResult =
    String(
      selectedException.action?.execution_result || ""
    ).toUpperCase();

  const selectedIsReviewOnly =
    selectedExecutionResult === "REVIEW_ONLY" ||
    selectedAction === "REVIEW_INVOICE_DIFFERENCE" ||
    selectedAction === "REVIEW_SETTLEMENT_DIFFERENCE" ||
    selectedAction === "REVIEW_SETTLEMENT_DELAY" ||
    selectedAction === "MANUAL_FINANCIAL_REVIEW" ||
    selectedAction === "GENERAL_REVIEW";

  // Review-only actions must never enter sandbox execution.
  if (selectedIsReviewOnly) {
    setActionMessage(
      "This action is review-only. No sandbox execution is required."
    );
    return;
  }

  try {
    setActionLoading(true);
    setActionMessage("");
    setError("");

    /*
     * =====================================================
     * STEP 1 — EXECUTE SANDBOX ACTION
     * =====================================================
     */

    const executeResponse =
      await fetch(
        `${API_BASE}/controller/actions/${exceptionId}/execute`,
        {
          method: "POST",
        }
      );

    const executeData =
      await executeResponse.json();

    if (
      !executeResponse.ok ||
      !executeData.success
    ) {
      throw new Error(
        executeData.error ||
        executeData.sandbox_response?.error ||
        "Sandbox execution failed."
      );
    }

    /*
     * =====================================================
     * STEP 2 — AUTOMATIC VERIFICATION
     * =====================================================
     */

    setActionMessage(
      "Sandbox action executed. Verifying execution..."
    );

    const verifyResponse =
      await fetch(
        `${API_BASE}/controller/actions/${exceptionId}/verify`,
        {
          method: "POST",
        }
      );

    const verifyData =
      await verifyResponse.json();

    if (
      !verifyResponse.ok ||
      !verifyData.success
    ) {
      /*
       * Execution succeeded, but verification failed.
       * The UI will remain in SANDBOX_EXECUTED state
       * and the user can retry verification manually.
       */
      await refreshSelectedException(
        exceptionId
      );

      throw new Error(
        verifyData.error ||
        verifyData.message ||
        "Sandbox execution succeeded, but verification failed."
      );
    }

    /*
     * =====================================================
     * STEP 3 — REFRESH FINAL CONTROLLER STATE
     * =====================================================
     */

    setActionMessage(
      "Sandbox action executed and verified successfully."
    );

    await refreshSelectedException(
      exceptionId
    );

  } catch (err) {

    console.error(err);

    setError(
      err.message ||
      "Unable to execute this action."
    );

  } finally {

    setActionLoading(false);

  }
}


  /* ======================================================= */
  /* VERIFY */
  /* ======================================================= */

  async function verifyAction() {

    if (!selectedException) {
      return;
    }


    const exceptionId =
      selectedException.exception
        ?.exception_id;


    if (!exceptionId) {
      return;
    }

    const selectedAction =
      String(
        selectedException.action?.proposed_action || ""
      ).toUpperCase();

    const selectedExecutionResult =
      String(
        selectedException.action?.execution_result || ""
      ).toUpperCase();

    const selectedIsReviewOnly =
      selectedExecutionResult === "REVIEW_ONLY" ||
      selectedAction === "REVIEW_INVOICE_DIFFERENCE" ||
      selectedAction === "REVIEW_SETTLEMENT_DIFFERENCE" ||
      selectedAction === "REVIEW_SETTLEMENT_DELAY" ||
      selectedAction === "MANUAL_FINANCIAL_REVIEW" ||
      selectedAction === "GENERAL_REVIEW";

    if (selectedIsReviewOnly) {
      setActionMessage(
        "This action is review-only. Verification is not required."
      );
      return;
    }


    try {

      setActionLoading(true);
      setActionMessage("");
      setError("");


      const response =
        await fetch(
          `${API_BASE}/controller/actions/${exceptionId}/verify`,
          {
            method: "POST",
          }
        );


      const data =
        await response.json();


      if (!response.ok || !data.success) {

        throw new Error(
          data.error ||
          data.message ||
          "Verification failed."
        );

      }


      setActionMessage(
        "Sandbox execution verified successfully."
      );


      await refreshSelectedException(
        exceptionId
      );


    } catch (err) {

      console.error(err);

      setError(
        err.message ||
        "Unable to verify this action."
      );

    } finally {

      setActionLoading(false);

    }

  }


  /* ======================================================= */
  /* RETURN */
  /* ======================================================= */

  return (

    <div className="exception-page">


      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <div className="exception-page-header">

        <div>

          <div className="exception-title-row">

            <div>

              <p className="exception-eyebrow">
                EXCEPTION MANAGEMENT
              </p>

              <h2>
                Exception Queue
              </h2>

            </div>


            <span className="exception-live-badge">

              <span></span>

              Live API

            </span>

          </div>


          <p className="exception-description">

            Review reconciliation exceptions,
            investigate financial anomalies,
            and manage controlled approval
            workflows.

          </p>

        </div>


        <button
          className="exception-refresh"
          onClick={loadExceptions}
          disabled={loading}
        >

          {loading
            ? "Refreshing..."
            : "↻ Refresh"}

        </button>

      </div>


      {/* ================================================== */}
      {/* ERROR */}
      {/* ================================================== */}

      {error && (

        <div className="exception-error">

          <span>
            !
          </span>

          {error}

        </div>

      )}


      {/* ================================================== */}
      {/* KPI CARDS */}
      {/* ================================================== */}

      <div className="exception-kpis">

        <div className="exception-kpi">

          <span className="kpi-label">
            TOTAL EXCEPTIONS
          </span>

          <strong>
            162
          </strong>

          <small>
            Requiring control attention
          </small>

        </div>


        <div className="exception-kpi">

          <span className="kpi-label">
            HIGH RISK
          </span>

          <strong className="kpi-high">
            20
          </strong>

          <small>
            Priority exceptions
          </small>

        </div>


        <div className="exception-kpi">

          <span className="kpi-label">
            AI INVESTIGATIONS
          </span>

          <strong className="kpi-ai">
            29
          </strong>

          <small>
            Investigations completed
          </small>

        </div>


        <div className="exception-kpi">

          <span className="kpi-label">
            PENDING APPROVAL
          </span>

          <strong className="kpi-warning">
            112
          </strong>

          <small>
            Awaiting human review
          </small>

        </div>

      </div>


      {/* ================================================== */}
      {/* FILTERS */}
      {/* ================================================== */}

      <div className="exception-filter-panel">

        <div className="filter-heading">

          <div>

            <strong>
              Exception Records
            </strong>

            <span>
              Filter and investigate financial exceptions
            </span>

          </div>

        </div>


        <div className="exception-filters">


          <div className="search-wrapper">

            <span className="search-icon">
              ⌕
            </span>


            <input
              type="text"
              placeholder="Search ID, payment, invoice, customer..."
              value={search}
              onChange={
                handleSearchChange
              }
            />


            {searching && (
              <span className="search-spinner"></span>
            )}

          </div>


          <select
            value={severity}
            onChange={
              handleSeverityChange
            }
          >

            <option value="">
              All Severities
            </option>

            <option value="HIGH">
              High Risk
            </option>

            <option value="MEDIUM">
              Medium Risk
            </option>

            <option value="LOW">
              Low Risk
            </option>

          </select>


          <select
            value={issue}
            onChange={
              handleIssueChange
            }
          >

            <option value="">
              All Issues
            </option>

            <option value="AMOUNT_MISMATCH">
              Amount Mismatch
            </option>

            <option value="INVOICE_MISMATCH">
              Invoice Mismatch
            </option>

            <option value="MISSING_SETTLEMENT">
              Missing Settlement
            </option>

            <option value="DUPLICATE_PAYMENT">
              Duplicate Payment
            </option>

            <option value="DELAYED_SETTLEMENT">
              Delayed Settlement
            </option>

          </select>


          {(search ||
            severity ||
            issue) && (

            <button
              className="clear-filter"
              onClick={
                clearFilters
              }
            >
              Clear
            </button>

          )}

        </div>

      </div>


      {/* ================================================== */}
      {/* SUMMARY */}
      {/* ================================================== */}

      <div className="queue-summary">

        <div>

          {search ? (

            <>
              Search results for{" "}

              <strong>
                "{search}"
              </strong>

              <span className="summary-separator">
                •
              </span>

              {exceptions.length} found
            </>

          ) : (

            <>
              Showing{" "}

              <strong>
                {pagination?.returned_records ?? 0}
              </strong>

              {" "}of{" "}

              <strong>
                {pagination?.total_records ?? 0}
              </strong>

              {" "}exceptions
            </>

          )}

        </div>


        {!search &&
          pagination && (

            <div className="queue-page-info">

              Page{" "}

              <strong>
                {pagination.page}
              </strong>

              {" "}of{" "}

              <strong>
                {pagination.total_pages}
              </strong>

            </div>

          )}

      </div>


      {/* ================================================== */}
      {/* TABLE */}
      {/* ================================================== */}

      <div className="exception-table-container">


        {loading || searching ? (

          <div className="exception-loading">

            <div className="loading-spinner"></div>

            <strong>

              {searching
                ? "Searching all exceptions..."
                : "Loading exception queue..."}

            </strong>

            <p>

              {searching
                ? "Checking the complete financial exception dataset."
                : "Fetching live records from the controller API."}

            </p>

          </div>


        ) : exceptions.length === 0 ? (

          <div className="empty-exceptions">

            <div className="empty-icon">
              ✓
            </div>

            <h3>
              No exceptions found
            </h3>

            <p>
              Try another search term or
              adjust your filters.
            </p>


            {(search ||
              severity ||
              issue) && (

              <button
                className="empty-clear"
                onClick={
                  clearFilters
                }
              >
                Clear filters
              </button>

            )}

          </div>


        ) : (

          <table className="exception-table">

            <thead>

              <tr>

                <th>
                  Exception
                </th>

                <th>
                  Payment
                </th>

                <th>
                  Issue
                </th>

                <th>
                  Severity
                </th>

                <th>
                  Amount
                </th>

                <th>
                  Workflow
                </th>

                <th>
                  Action
                </th>

              </tr>

            </thead>


            <tbody>

              {exceptions.map(
                (exception) => (

                  <tr
                    key={
                      exception.exception_id
                    }
                  >

                    <td>

                      <button
                        className="exception-id"
                        onClick={() =>
                          openException(
                            exception.exception_id
                          )
                        }
                      >
                        {exception.exception_id}
                      </button>

                    </td>


                    <td>

                      <span className="payment-id">
                        {exception.payment_id}
                      </span>

                    </td>


                    <td>

                      <div className="issue-cell">

                        {String(
                          exception.issues || ""
                        )
                          .split(";")
                          .map(
                            (
                              item,
                              index
                            ) => (

                              <span
                                key={index}
                                className="issue-badge"
                              >
                                {formatIssue(
                                  item
                                )}
                              </span>

                            )
                          )}

                      </div>

                    </td>


                    <td>

                      <SeverityBadge
                        severity={
                          exception.severity
                        }
                      />

                    </td>


                    <td>

                      <span className="amount-cell">
                        {formatCurrency(
                          exception.amount
                        )}
                      </span>

                    </td>


                    <td>

                      <span className="workflow-badge">
                        {formatWorkflow(
                          exception.workflow
                        )}
                      </span>

                    </td>


                    <td>

                      <button
                        className="view-button"
                        onClick={() =>
                          openException(
                            exception.exception_id
                          )
                        }
                      >
                        View Details →
                      </button>

                    </td>

                  </tr>

                )
              )}

            </tbody>

          </table>

        )}

      </div>


      {/* ================================================== */}
      {/* PAGINATION */}
      {/* ================================================== */}

      {!search &&
        pagination &&
        pagination.total_pages > 1 && (

          <div className="pagination">

            <button
              disabled={
                pagination.page <= 1
              }
              onClick={() =>
                setPage(
                  pagination.page - 1
                )
              }
            >
              ← Previous
            </button>


            <div className="page-number">

              Page{" "}

              <strong>
                {pagination.page}
              </strong>

              {" "}of{" "}

              {pagination.total_pages}

            </div>


            <button
              disabled={
                pagination.page >=
                pagination.total_pages
              }
              onClick={() =>
                setPage(
                  pagination.page + 1
                )
              }
            >
              Next →
            </button>

          </div>

        )}


      {/* ================================================== */}
      {/* DETAILS MODAL */}
      {/* ================================================== */}

      {selectedException && (

        <ExceptionDetails
          data={selectedException}
          onClose={() =>
            setSelectedException(
              null
            )
          }

          actionLoading={
            actionLoading
          }

          actionMessage={
            actionMessage
          }

          reviewer={
            reviewer
          }

          setReviewer={
            setReviewer
          }

          comments={
            comments
          }

          setComments={
            setComments
          }

          onApprove={
            approveAction
          }

          onExecute={
            executeAction
          }

          onVerify={
            verifyAction
          }

        />

      )}

    </div>

  );
}


/* ========================================================= */
/* EXCEPTION DETAILS */
/* ========================================================= */

function ExceptionDetails({
  data,
  onClose,

  actionLoading,
  actionMessage,

  reviewer,
  setReviewer,

  comments,
  setComments,

  onApprove,
  onExecute,
  onVerify,
}) {

  const exception =
    data.exception || {};

  const action =
    data.action || {};

  const ai =
    data.ai_investigation || {};

  const approval =
    data.approval || {};


  const approvalStatus =
    String(
      approval.approval_status ||
      action.approval_status ||
      "PENDING_APPROVAL"
    ).toUpperCase();


  const actionStatus =
    String(
      action.action_status ||
      "PENDING"
    ).toUpperCase();


  const executionResult =
    String(
      action.execution_result ||
      "NOT_EXECUTED"
    ).toUpperCase();


  const isApproved =
    approvalStatus === "APPROVED" ||
    approvalStatus === "VERIFIED";


  const isVerified =
    actionStatus === "VERIFIED" ||
    executionResult === "SANDBOX_VERIFIED";

  /*
   * Review-only actions must never be sent to the sandbox.
   * These actions represent human/controller review and do not
   * require execution or post-execution verification.
   */
  const proposedAction =
    String(
      action.proposed_action || ""
    ).toUpperCase();

  const isReviewOnly =
    executionResult === "REVIEW_ONLY" ||
    proposedAction === "REVIEW_INVOICE_DIFFERENCE" ||
    proposedAction === "REVIEW_SETTLEMENT_DIFFERENCE" ||
    proposedAction === "REVIEW_SETTLEMENT_DELAY" ||
    proposedAction === "MANUAL_FINANCIAL_REVIEW" ||
    proposedAction === "GENERAL_REVIEW";

  const canApprove =
    approvalStatus === "PENDING_APPROVAL";

  const canExecute =
    isApproved &&
    !isVerified &&
    !isReviewOnly &&
    executionResult !== "SANDBOX_EXECUTED";

  const canVerify =
    executionResult === "SANDBOX_EXECUTED" &&
    !isVerified &&
    !isReviewOnly;


  return (

    <div className="modal-overlay">

      <div className="exception-modal">


        {/* ================================================= */}
        {/* HEADER */}
        {/* ================================================= */}

        <div className="modal-header">

          <div>

            <p className="modal-eyebrow">
              EXCEPTION DETAILS
            </p>


            <div className="modal-title-row">

              <h2>
                {exception.exception_id}
              </h2>


              <SeverityBadge
                severity={
                  exception.severity
                }
              />

            </div>

          </div>


          <button
            className="modal-close"
            onClick={onClose}
          >
            ×
          </button>

        </div>


        {/* ================================================= */}
        {/* FINANCIAL OVERVIEW */}
        {/* ================================================= */}

        <div className="detail-section">

          <div className="detail-grid">

            <DetailItem
              label="Payment"
              value={
                exception.payment_id
              }
            />

            <DetailItem
              label="Transaction"
              value={
                exception.transaction_id
              }
            />

            <DetailItem
              label="Invoice"
              value={
                exception.invoice_id
              }
            />

            <DetailItem
              label="Customer"
              value={
                exception.customer_id
              }
            />

            <DetailItem
              label="Amount"
              value={formatCurrency(
                exception.amount
              )}
            />

            <DetailItem
              label="Invoice Amount"
              value={formatCurrency(
                exception.invoice_amount
              )}
            />

            <DetailItem
              label="Settlement"
              value={formatCurrency(
                exception.settled_amount
              )}
            />

            <DetailItem
              label="Payment Method"
              value={
                exception.payment_method
              }
            />

          </div>

        </div>


        {/* ================================================= */}
        {/* ISSUES */}
        {/* ================================================= */}

        <div className="detail-section">

          <h3>
            Detected Issues
          </h3>


          <div className="detail-issues">

            {String(
              exception.issues || ""
            )
              .split(";")
              .map(
                (
                  item,
                  index
                ) => (

                  <span
                    key={index}
                    className="issue-badge large"
                  >
                    {formatIssue(
                      item
                    )}
                  </span>

                )
              )}

          </div>

        </div>


        {/* ================================================= */}
        {/* AI INVESTIGATION */}
        {/* ================================================= */}

        <div className="detail-section ai-detail">

          <div className="section-title-row">

            <div>

              <p className="modal-eyebrow">
                AI CONTROL ENGINE
              </p>

              <h3>
                Investigation Result
              </h3>

            </div>


            {ai.ai_status && (

              <span className="ai-status-badge">
                {ai.ai_status}
              </span>

            )}

          </div>


          {ai.likely_cause && (

            <div className="ai-block">

              <span>
                Likely Cause
              </span>

              <p>
                {ai.likely_cause}
              </p>

            </div>

          )}


          {ai.ai_reasoning && (

            <div className="ai-block">

              <span>
                AI Reasoning
              </span>

              <p>
                {ai.ai_reasoning}
              </p>

            </div>

          )}


          {ai.ai_recommended_action && (

            <div className="ai-block">

              <span>
                Recommended Action
              </span>

              <p>
                {ai.ai_recommended_action}
              </p>

            </div>

          )}


          {!ai.ai_reasoning &&
            !ai.likely_cause &&
            !ai.ai_recommended_action && (

              <div className="ai-empty">

                <span>
                  AI
                </span>

                <div>

                  <strong>
                    No separate AI investigation record
                  </strong>

                  <p>
                    This exception does not currently
                    have a standalone AI investigation
                    result.
                  </p>

                </div>

              </div>

            )}

        </div>


        {/* ================================================= */}
        {/* CONTROLLER ACTION */}
        {/* ================================================= */}

        <div className="detail-section controller-action-section">

          <div className="section-title-row">

            <div>

              <p className="modal-eyebrow">
                CONTROLLER ACTION
              </p>

              <h3>
                Approval &amp; Execution
              </h3>

            </div>


            {action.proposed_action && (

              <span className="action-badge">

                {formatAction(
                  action.proposed_action
                )}

              </span>

            )}

          </div>


          {/* --------------------------------------------- */}
          {/* WORKFLOW STATUS */}
          {/* --------------------------------------------- */}

          <div className="workflow-status">

            <WorkflowStatus
              number="01"
              label="Approval"
              status={
                approvalStatus
              }
              completed={
                isApproved
              }
              active={
                canApprove
              }
            />


            <WorkflowLine />


            <WorkflowStatus
              number="02"
              label={
                isReviewOnly
                  ? "Review"
                  : "Execution"
              }
              status={
                isReviewOnly
                  ? "REVIEW_ONLY"
                  : executionResult
              }
              completed={
                isReviewOnly ||
                executionResult ===
                  "SANDBOX_EXECUTED"
              }
              active={
                isReviewOnly
                  ? false
                  : canExecute
              }
            />


            <WorkflowLine />


            <WorkflowStatus
              number="03"
              label={
                isReviewOnly
                  ? "Complete"
                  : "Verification"
              }
              status={
                isReviewOnly
                  ? "NOT_REQUIRED"
                  : isVerified
                    ? "VERIFIED"
                    : "PENDING"
              }
              completed={
                isReviewOnly ||
                isVerified
              }
              active={
                isReviewOnly
                  ? false
                  : canVerify
              }
            />

          </div>


          {/* --------------------------------------------- */}
          {/* ACTION INFORMATION */}
          {/* --------------------------------------------- */}

          <div className="detail-grid">

            <DetailItem
              label="Action Risk"
              value={
                action.action_risk
              }
            />

            <DetailItem
              label="Approval Status"
              value={
                approvalStatus
              }
            />

            <DetailItem
              label="Action Status"
              value={
                actionStatus
              }
            />

            <DetailItem
              label="Execution Result"
              value={
                executionResult
              }
            />

          </div>


          {/* --------------------------------------------- */}
          {/* APPROVAL FORM */}
          {/* --------------------------------------------- */}

          {canApprove && (

            <div className="approval-form">

              <div className="approval-form-heading">

                <div>

                  <strong>
                    Human Review Required
                  </strong>

                  <span>
                    Approve this action before
                    any sandbox operation can run.
                  </span>

                </div>

              </div>


              <div className="form-row">

                <div className="form-field">

                  <label>
                    Reviewer
                  </label>

                  <input
                    type="text"
                    value={reviewer}
                    onChange={(event) =>
                      setReviewer(
                        event.target.value
                      )
                    }
                    placeholder="Enter reviewer name"
                    disabled={
                      actionLoading
                    }
                  />

                </div>


                <div className="form-field">

                  <label>
                    Review Comments
                  </label>

                  <input
                    type="text"
                    value={comments}
                    onChange={(event) =>
                      setComments(
                        event.target.value
                      )
                    }
                    placeholder="Add approval comments"
                    disabled={
                      actionLoading
                    }
                  />

                </div>

              </div>


              <button
                className="approve-button"
                onClick={
                  onApprove
                }
                disabled={
                  actionLoading
                }
              >

                {actionLoading
                  ? "Approving..."
                  : "✓ Approve Action"}

              </button>

            </div>

          )}


          {/* --------------------------------------------- */}
          {/* APPROVED STATE */}
          {/* --------------------------------------------- */}

          {isApproved &&
            !isVerified &&
            !isReviewOnly && (

              <div className="action-ready-box">

                <div className="action-ready-icon">
                  ✓
                </div>

                <div>

                  <strong>
                    Action Approved
                  </strong>

                  <span>
                    Human approval has been recorded.
                    The controlled sandbox action can
                    now be executed.
                  </span>

                </div>


                {canExecute && (

                  <button
                    className="execute-button"
                    onClick={
                      onExecute
                    }
                    disabled={
                      actionLoading
                    }
                  >

                    {actionLoading
                      ? "Executing..."
                      : "Execute Sandbox Action →"}

                  </button>

                )}

              </div>

            )}


          {/* --------------------------------------------- */}
          {/* REVIEW-ONLY STATE */}
          {/* --------------------------------------------- */}

          {isReviewOnly && (

            <div className="action-ready-box">

              <div className="action-ready-icon">
                ✓
              </div>

              <div>

                <strong>
                  Human Review Completed
                </strong>

                <span>
                  This controller action is review-only.
                  No automated financial operation is
                  required, so sandbox execution and
                  verification are not applicable.
                </span>

              </div>

              <span className="verified-status">
                REVIEW ONLY
              </span>

            </div>

          )}


          {/* --------------------------------------------- */}
          {/* EXECUTED STATE */}
          {/* --------------------------------------------- */}

          {executionResult ===
            "SANDBOX_EXECUTED" &&
            !isVerified && (

              <div className="verification-ready-box">

                <div className="action-ready-icon">
                  ✓
                </div>

                <div>

                  <strong>
                    Sandbox Execution Completed
                  </strong>

                  <span>
                    The controlled action was executed
                    successfully. Verify the result to
                    complete the workflow.
                  </span>

                </div>


                {canVerify && (

                  <button
                    className="verify-button"
                    onClick={
                      onVerify
                    }
                    disabled={
                      actionLoading
                    }
                  >

                    {actionLoading
                      ? "Verifying..."
                      : "Verify Execution →"}

                  </button>

                )}

              </div>

            )}


          {/* --------------------------------------------- */}
          {/* VERIFIED STATE */}
          {/* --------------------------------------------- */}

          {isVerified && (

            <div className="verified-box">

              <div className="verified-icon">
                ✓
              </div>

              <div>

                <strong>
                  Action Verified
                </strong>

                <span>
                  Sandbox execution has been successfully
                  verified by the controller.
                </span>

              </div>

              <span className="verified-status">
                SANDBOX VERIFIED
              </span>

            </div>

          )}


          {/* --------------------------------------------- */}
          {/* SUCCESS MESSAGE */}
          {/* --------------------------------------------- */}

          {actionMessage && (

            <div className="action-success-message">

              <span>
                ✓
              </span>

              {actionMessage}

            </div>

          )}

        </div>


        {/* ================================================= */}
        {/* FOOTER */}
        {/* ================================================= */}

        <div className="modal-footer">

          <button
            className="modal-secondary"
            onClick={onClose}
          >
            Close
          </button>

        </div>

      </div>

    </div>

  );
}


/* ========================================================= */
/* WORKFLOW STATUS */
/* ========================================================= */

function WorkflowStatus({
  number,
  label,
  status,
  completed,
  active,
}) {

  return (

    <div
      className={`workflow-status-step ${
        completed
          ? "completed"
          : ""
      } ${
        active
          ? "active"
          : ""
      }`}
    >

      <div className="workflow-status-number">

        {completed
          ? "✓"
          : number}

      </div>


      <div>

        <strong>
          {label}
        </strong>

        <span>
          {formatStatus(
            status
          )}
        </span>

      </div>

    </div>

  );
}


/* ========================================================= */
/* WORKFLOW LINE */
/* ========================================================= */

function WorkflowLine() {

  return (
    <div className="workflow-line">
      →
    </div>
  );

}


/* ========================================================= */
/* SEVERITY */
/* ========================================================= */

function SeverityBadge({
  severity,
}) {

  const value =
    String(
      severity || "UNKNOWN"
    ).toUpperCase();


  return (

    <span
      className={`severity-badge ${value.toLowerCase()}`}
    >

      <span className="severity-badge-dot"></span>

      {value}

    </span>

  );

}


/* ========================================================= */
/* DETAIL ITEM */
/* ========================================================= */

function DetailItem({
  label,
  value,
}) {

  return (

    <div className="detail-item">

      <span>
        {label}
      </span>

      <strong>

        {value === null ||
        value === undefined ||
        value === ""
          ? "—"
          : value}

      </strong>

    </div>

  );

}


/* ========================================================= */
/* FORMATTING */
/* ========================================================= */

function formatCurrency(
  value
) {

  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {

    return "—";

  }


  const number =
    Number(value);


  if (
    Number.isNaN(number)
  ) {

    return String(value);

  }


  return new Intl.NumberFormat(
    "en-IN",
    {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }
  ).format(number);

}


function formatIssue(
  issue
) {

  return String(
    issue || ""
  )
    .replaceAll(
      "_",
      " "
    )
    .toLowerCase()
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase()
    );

}


function formatWorkflow(
  workflow
) {

  return String(
    workflow || "—"
  ).replaceAll(
    "_",
    " "
  );

}


function formatAction(
  action
) {

  return String(
    action || ""
  ).replaceAll(
    "_",
    " "
  );

}


function formatStatus(
  status
) {

  return String(
    status || "PENDING"
  )
    .replaceAll(
      "_",
      " "
    );

}


export default ExceptionQueue;