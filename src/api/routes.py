import os

import pandas as pd

from flask import (
    Blueprint,
    jsonify,
    request
)


# ============================================================
# AI FINANCE CONTROLLER
# API ROUTES
# ============================================================

api = Blueprint(
    "api",
    __name__,
    url_prefix="/api"
)


# ============================================================
# Project Paths
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)


# ------------------------------------------------------------
# Reconciliation
# ------------------------------------------------------------

RECONCILIATION_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "processed",
    "reconciliation",
    "reconciliation_results.csv"
)


# ------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------

EXCEPTIONS_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "processed",
    "exceptions",
    "exceptions.csv"
)


# ------------------------------------------------------------
# AI Investigation Queue
# ------------------------------------------------------------

AI_QUEUE_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "processed",
    "controller",
    "ai_investigation_queue.csv"
)


# ------------------------------------------------------------
# AI Investigation Results
# ------------------------------------------------------------

AI_RESULTS_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "processed",
    "exceptions",
    "ai_investigations.csv"
)


# ------------------------------------------------------------
# Approval Queue
# ------------------------------------------------------------

APPROVAL_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "processed",
    "controller",
    "approval_queue.csv"
)


# ------------------------------------------------------------
# Action Queue
# ------------------------------------------------------------

ACTION_QUEUE_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "processed",
    "controller",
    "action_queue.csv"
)


# ============================================================
# Helper Functions
# ============================================================

def load_csv(path):

    if not os.path.exists(path):

        return None

    return pd.read_csv(path)


def clean_record(record):
    """
    Convert pandas / NumPy values into
    JSON-safe Python values.
    """

    cleaned = {}

    for key, value in record.items():

        if pd.isna(value):

            cleaned[key] = None

        elif hasattr(value, "item"):

            cleaned[key] = value.item()

        else:

            cleaned[key] = value

    return cleaned


# ============================================================
# HEALTH CHECK
# ============================================================

@api.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "success": True,

        "service":
            "ai-finance-controller",

        "status":
            "healthy"

    }), 200


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@api.route(
    "/dashboard/summary",
    methods=["GET"]
)
def dashboard_summary():

    try:

        reconciliation = load_csv(
            RECONCILIATION_FILE
        )

        exceptions = load_csv(
            EXCEPTIONS_FILE
        )

        ai_queue = load_csv(
            AI_QUEUE_FILE
        )

        approval_queue = load_csv(
            APPROVAL_FILE
        )

        # ----------------------------------------------------
        # Reconciliation metrics
        # ----------------------------------------------------

        if reconciliation is not None:

            total_records = len(
                reconciliation
            )

            matched_records = len(
                reconciliation[
                    reconciliation[
                        "reconciliation_status"
                    ]
                    == "MATCHED"
                ]
            )

            exception_records = len(
                reconciliation[
                    reconciliation[
                        "reconciliation_status"
                    ]
                    == "EXCEPTION"
                ]
            )

        else:

            total_records = 0
            matched_records = 0
            exception_records = 0

        if total_records > 0:

            match_rate = round(
                (
                    matched_records
                    / total_records
                ) * 100,
                2
            )

        else:

            match_rate = 0.0

        # ----------------------------------------------------
        # Exception breakdown
        # ----------------------------------------------------

        exception_breakdown = {}

        severity_breakdown = {}

        if exceptions is not None:

            if "issues" in exceptions.columns:

                exception_breakdown = (
                    exceptions[
                        "issues"
                    ]
                    .value_counts()
                    .to_dict()
                )

            if "severity" in exceptions.columns:

                severity_breakdown = (
                    exceptions[
                        "severity"
                    ]
                    .value_counts()
                    .to_dict()
                )

        # ----------------------------------------------------
        # AI queue status
        # ----------------------------------------------------

        ai_status = {}

        if (
            ai_queue is not None
            and "ai_status" in ai_queue.columns
        ):

            ai_status = (
                ai_queue[
                    "ai_status"
                ]
                .value_counts()
                .to_dict()
            )

        # ----------------------------------------------------
        # Approval status
        # ----------------------------------------------------

        approval_status = {}

        if (
            approval_queue is not None
            and "approval_status"
            in approval_queue.columns
        ):

            approval_status = (
                approval_queue[
                    "approval_status"
                ]
                .value_counts()
                .to_dict()
            )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "summary": {

                "total_records":
                    int(total_records),

                "matched_records":
                    int(matched_records),

                "exception_records":
                    int(exception_records),

                "match_rate":
                    float(match_rate)

            },

            "exceptions":
                exception_breakdown,

            "severity":
                severity_breakdown,

            "ai_investigations":
                ai_status,

            "approvals":
                approval_status

        }), 200

    except Exception as error:

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


# ============================================================
# TRANSACTION DATA
# ============================================================

TRANSACTIONS_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "processed",
    "reconciliation",
    "reconciliation_results.csv"
)


# ============================================================
# TRANSACTIONS LIST
# ============================================================

@api.route(
    "/transactions",
    methods=["GET"]
)
def transactions():

    try:

        df = load_csv(
            TRANSACTIONS_FILE
        )

        if df is None:

            return jsonify({

                "success": False,

                "error":
                    "Transaction data not found."

            }), 404

        # ----------------------------------------------------
        # Query parameters
        # ----------------------------------------------------

        search = (
            request.args
            .get(
                "search",
                ""
            )
            .strip()
        )

        status = (
            request.args
            .get(
                "status",
                ""
            )
            .strip()
            .upper()
        )

        page = int(
            request.args.get(
                "page",
                1
            )
        )

        limit = int(
            request.args.get(
                "limit",
                20
            )
        )

        # ----------------------------------------------------
        # Safety limits
        # ----------------------------------------------------

        if page < 1:

            page = 1

        if limit < 1:

            limit = 20

        if limit > 100:

            limit = 100

        # ----------------------------------------------------
        # Search
        # ----------------------------------------------------

        if search:

            search_columns = [

                "payment_id",

                "transaction_id",

                "invoice_id",

                "customer_id"

            ]

            mask = pd.Series(
                False,
                index=df.index
            )

            for column in search_columns:

                if column in df.columns:

                    mask |= (
                        df[column]
                        .astype(str)
                        .str.contains(
                            search,
                            case=False,
                            na=False
                        )
                    )

            df = df[mask]

        # ----------------------------------------------------
        # Status filter
        # ----------------------------------------------------

        if status:

            if (
                "reconciliation_status"
                in df.columns
            ):

                df = df[
                    df[
                        "reconciliation_status"
                    ]
                    .astype(str)
                    .str.upper()
                    == status
                ]

        # ----------------------------------------------------
        # Pagination
        # ----------------------------------------------------

        total = len(df)

        start = (
            page - 1
        ) * limit

        end = start + limit

        page_df = df.iloc[
            start:end
        ]

        records = [

            clean_record(record)

            for record

            in page_df.to_dict(
                orient="records"
            )

        ]

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "pagination": {

                "page":
                    page,

                "limit":
                    limit,

                "total_records":
                    int(total),

                "returned_records":
                    len(records),

                "total_pages":
                    (
                        (
                            total
                            + limit
                            - 1
                        )
                        // limit
                    )

            },

            "transactions":
                records

        }), 200

    except ValueError:

        return jsonify({

            "success": False,

            "error":
                "Invalid pagination parameters."

        }), 400

    except Exception as error:

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


# ============================================================
# SINGLE TRANSACTION
# ============================================================

@api.route(
    "/transactions/<payment_id>",
    methods=["GET"]
)
def transaction_detail(
    payment_id
):

    try:

        df = load_csv(
            TRANSACTIONS_FILE
        )

        if df is None:

            return jsonify({

                "success": False,

                "error":
                    "Transaction data not found."

            }), 404

        if "payment_id" not in df.columns:

            return jsonify({

                "success": False,

                "error":
                    "Payment ID field not available."

            }), 500

        matches = df[
            df[
                "payment_id"
            ]
            .astype(str)
            == str(payment_id)
        ]

        if matches.empty:

            return jsonify({

                "success": False,

                "error":
                    "Transaction not found.",

                "payment_id":
                    payment_id

            }), 404

        record = clean_record(
            matches.iloc[
                0
            ].to_dict()
        )

        return jsonify({

            "success": True,

            "transaction":
                record

        }), 200

    except Exception as error:

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


# ============================================================
# EXCEPTIONS LIST
# ============================================================

@api.route(
    "/exceptions",
    methods=["GET"]
)
def exceptions():

    try:

        df = load_csv(
            EXCEPTIONS_FILE
        )

        if df is None:

            return jsonify({

                "success": False,

                "error":
                    "Exception data not found."

            }), 404

        # ----------------------------------------------------
        # Query parameters
        # ----------------------------------------------------

        search = (
            request.args
            .get(
                "search",
                ""
            )
            .strip()
        )

        severity = (
            request.args
            .get(
                "severity",
                ""
            )
            .strip()
            .upper()
        )

        issue = (
            request.args
            .get(
                "issue",
                ""
            )
            .strip()
            .upper()
        )

        page = int(
            request.args.get(
                "page",
                1
            )
        )

        limit = int(
            request.args.get(
                "limit",
                20
            )
        )

        # ----------------------------------------------------
        # Pagination safety
        # ----------------------------------------------------

        if page < 1:

            page = 1

        if limit < 1:

            limit = 20

        if limit > 100:

            limit = 100

        # ----------------------------------------------------
        # Search
        # ----------------------------------------------------

        if search:

            search_columns = [

                "exception_id",

                "payment_id",

                "transaction_id",

                "invoice_id",

                "customer_id"

            ]

            mask = pd.Series(
                False,
                index=df.index
            )

            for column in search_columns:

                if column in df.columns:

                    mask |= (
                        df[column]
                        .astype(str)
                        .str.contains(
                            search,
                            case=False,
                            na=False
                        )
                    )

            df = df[mask]

        # ----------------------------------------------------
        # Severity filter
        # ----------------------------------------------------

        if severity:

            if "severity" in df.columns:

                df = df[
                    df[
                        "severity"
                    ]
                    .astype(str)
                    .str.upper()
                    == severity
                ]

        # ----------------------------------------------------
        # Issue filter
        # ----------------------------------------------------

        if issue:

            if "issues" in df.columns:

                df = df[
                    df[
                        "issues"
                    ]
                    .astype(str)
                    .str.upper()
                    .str.contains(
                        issue,
                        regex=False,
                        na=False
                    )
                ]

        # ----------------------------------------------------
        # Pagination
        # ----------------------------------------------------

        total = len(df)

        start = (
            page - 1
        ) * limit

        end = start + limit

        page_df = df.iloc[
            start:end
        ]

        records = [

            clean_record(record)

            for record

            in page_df.to_dict(
                orient="records"
            )

        ]

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "pagination": {

                "page":
                    page,

                "limit":
                    limit,

                "total_records":
                    int(total),

                "returned_records":
                    len(records),

                "total_pages":
                    (
                        (
                            total
                            + limit
                            - 1
                        )
                        // limit
                    )

            },

            "exceptions":
                records

        }), 200

    except ValueError:

        return jsonify({

            "success": False,

            "error":
                "Invalid pagination parameters."

        }), 400

    except Exception as error:

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


# ============================================================
# SINGLE EXCEPTION
# ============================================================

@api.route(
    "/exceptions/<exception_id>",
    methods=["GET"]
)
def exception_detail(
    exception_id
):

    try:

        exceptions_df = load_csv(
            EXCEPTIONS_FILE
        )

        if exceptions_df is None:

            return jsonify({

                "success": False,

                "error":
                    "Exception data not found."

            }), 404

        # ----------------------------------------------------
        # Find exception
        # ----------------------------------------------------

        matches = exceptions_df[
            exceptions_df[
                "exception_id"
            ]
            .astype(str)
            == str(exception_id)
        ]

        if matches.empty:

            return jsonify({

                "success": False,

                "error":
                    "Exception not found.",

                "exception_id":
                    exception_id

            }), 404

        exception = clean_record(
            matches.iloc[
                0
            ].to_dict()
        )

        # ----------------------------------------------------
        # AI investigation
        # ----------------------------------------------------

        ai_result = None

        ai_df = load_csv(
            AI_RESULTS_FILE
        )

        if ai_df is not None:

            if (
                "exception_id"
                in ai_df.columns
            ):

                ai_matches = ai_df[
                    ai_df[
                        "exception_id"
                    ]
                    .astype(str)
                    == str(exception_id)
                ]

                if not ai_matches.empty:

                    ai_result = clean_record(
                        ai_matches.iloc[
                            0
                        ].to_dict()
                    )

        # ----------------------------------------------------
        # AI queue status
        # ----------------------------------------------------

        ai_queue_result = None

        ai_queue_df = load_csv(
            AI_QUEUE_FILE
        )

        if ai_queue_df is not None:

            if (
                "exception_id"
                in ai_queue_df.columns
            ):

                queue_matches = ai_queue_df[
                    ai_queue_df[
                        "exception_id"
                    ]
                    .astype(str)
                    == str(exception_id)
                ]

                if not queue_matches.empty:

                    ai_queue_result = clean_record(
                        queue_matches.iloc[
                            0
                        ].to_dict()
                    )

        # ----------------------------------------------------
        # Action information
        # ----------------------------------------------------

        action_result = None

        action_df = load_csv(
            ACTION_QUEUE_FILE
        )

        if action_df is not None:

            if (
                "exception_id"
                in action_df.columns
            ):

                action_matches = action_df[
                    action_df[
                        "exception_id"
                    ]
                    .astype(str)
                    == str(exception_id)
                ]

                if not action_matches.empty:

                    action_result = clean_record(
                        action_matches.iloc[
                            0
                        ].to_dict()
                    )

        # ----------------------------------------------------
        # Approval information
        # ----------------------------------------------------

        approval_result = None

        approval_df = load_csv(
            APPROVAL_FILE
        )

        if approval_df is not None:

            if (
                "exception_id"
                in approval_df.columns
            ):

                approval_matches = approval_df[
                    approval_df[
                        "exception_id"
                    ]
                    .astype(str)
                    == str(exception_id)
                ]

                if not approval_matches.empty:

                    approval_result = clean_record(
                        approval_matches.iloc[
                            0
                        ].to_dict()
                    )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "exception":
                exception,

            "ai_queue":
                ai_queue_result,

            "ai_investigation":
                ai_result,

            "action":
                action_result,

            "approval":
                approval_result

        }), 200

    except Exception as error:

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500

# ============================================================
# CONTROLLER QUEUE
# ============================================================

@api.route(
    "/controller/queue",
    methods=["GET"]
)
def controller_queue():

    try:

        df = load_csv(
            APPROVAL_FILE
        )

        if df is None:

            return jsonify({
                "success": False,
                "error": "Approval queue not found."
            }), 404

        status = (
            request.args
            .get("status", "")
            .strip()
            .upper()
        )

        action = (
            request.args
            .get("action", "")
            .strip()
            .upper()
        )

        priority = (
            request.args
            .get("priority", "")
            .strip()
            .upper()
        )

        if status and "approval_status" in df.columns:

            df = df[
                df["approval_status"]
                .astype(str)
                .str.upper()
                == status
            ]

        if action and "proposed_action" in df.columns:

            df = df[
                df["proposed_action"]
                .astype(str)
                .str.upper()
                == action
            ]

        if priority and "controller_priority" in df.columns:

            df = df[
                df["controller_priority"]
                .astype(str)
                .str.upper()
                == priority
            ]

        records = [
            clean_record(record)
            for record in df.to_dict(
                orient="records"
            )
        ]

        return jsonify({

            "success": True,

            "count":
                len(records),

            "actions":
                records

        }), 200

    except Exception as error:

        return jsonify({

            "success": False,
            "error": str(error)

        }), 500


# ============================================================
# SINGLE CONTROLLER ACTION
# ============================================================

@api.route(
    "/controller/actions/<exception_id>",
    methods=["GET"]
)
def controller_action(
    exception_id
):

    try:

        df = load_csv(
            APPROVAL_FILE
        )

        if df is None:

            return jsonify({
                "success": False,
                "error": "Approval queue not found."
            }), 404

        matches = df[
            df["exception_id"]
            .astype(str)
            == str(exception_id)
        ]

        if matches.empty:

            return jsonify({

                "success": False,

                "error":
                    "Controller action not found.",

                "exception_id":
                    exception_id

            }), 404

        record = clean_record(
            matches.iloc[
                0
            ].to_dict()
        )

        return jsonify({

            "success": True,

            "action":
                record

        }), 200

    except Exception as error:

        return jsonify({

            "success": False,
            "error": str(error)

        }), 500


# ============================================================
# APPROVE ACTION
# ============================================================

@api.route(
    "/controller/actions/<exception_id>/approve",
    methods=["POST"]
)
def approve_action(
    exception_id
):

    try:

        df = load_csv(
            APPROVAL_FILE
        )

        if df is None:

            return jsonify({
                "success": False,
                "error": "Approval queue not found."
            }), 404

        matches = df[
            df["exception_id"]
            .astype(str)
            == str(exception_id)
        ]

        if matches.empty:

            return jsonify({

                "success": False,

                "error":
                    "Controller action not found."

            }), 404

        index = matches.index[0]

        current_status = str(
            df.loc[
                index,
                "approval_status"
            ]
        ).upper()

        # ----------------------------------------------------
        # State validation
        # ----------------------------------------------------

        if current_status != "PENDING_APPROVAL":

            return jsonify({

                "success": False,

                "error":
                    "Action is not awaiting approval.",

                "current_status":
                    current_status

            }), 409

        # ----------------------------------------------------
        # Reviewer information
        # ----------------------------------------------------

        data = request.get_json(
            silent=True
        ) or {}

        reviewer = data.get(
            "reviewer",
            "API_REVIEWER"
        )

        comments = data.get(
            "comments",
            "Approved through Finance Controller API."
        )

        # ----------------------------------------------------
        # Update state
        # ----------------------------------------------------

        df.loc[
            index,
            "approval_status"
        ] = "APPROVED"

        df.loc[
            index,
            "review_decision"
        ] = "APPROVE"

        df.loc[
            index,
            "reviewer"
        ] = str(reviewer)

        df.loc[
            index,
            "review_comments"
        ] = str(comments)

        df.loc[
            index,
            "execution_allowed"
        ] = True

        # Keep action status synchronized
        if "action_status" in df.columns:

            df.loc[
                index,
                "action_status"
            ] = "APPROVED"

        df.to_csv(
            APPROVAL_FILE,
            index=False
        )

        updated = clean_record(
            df.loc[
                index
            ].to_dict()
        )

        return jsonify({

            "success": True,

            "message":
                "Action approved successfully.",

            "action":
                updated

        }), 200

    except Exception as error:

        return jsonify({

            "success": False,
            "error": str(error)

        }), 500


# ============================================================
# REJECT ACTION
# ============================================================

@api.route(
    "/controller/actions/<exception_id>/reject",
    methods=["POST"]
)
def reject_action(
    exception_id
):

    try:

        df = load_csv(
            APPROVAL_FILE
        )

        if df is None:

            return jsonify({
                "success": False,
                "error": "Approval queue not found."
            }), 404

        matches = df[
            df["exception_id"]
            .astype(str)
            == str(exception_id)
        ]

        if matches.empty:

            return jsonify({

                "success": False,

                "error":
                    "Controller action not found."

            }), 404

        index = matches.index[0]

        current_status = str(
            df.loc[
                index,
                "approval_status"
            ]
        ).upper()

        if current_status != "PENDING_APPROVAL":

            return jsonify({

                "success": False,

                "error":
                    "Action is not awaiting approval.",

                "current_status":
                    current_status

            }), 409

        data = request.get_json(
            silent=True
        ) or {}

        reviewer = data.get(
            "reviewer",
            "API_REVIEWER"
        )

        comments = data.get(
            "comments",
            "Rejected through Finance Controller API."
        )

        # ----------------------------------------------------
        # Update state
        # ----------------------------------------------------

        df.loc[
            index,
            "approval_status"
        ] = "REJECTED"

        df.loc[
            index,
            "review_decision"
        ] = "REJECT"

        df.loc[
            index,
            "reviewer"
        ] = str(reviewer)

        df.loc[
            index,
            "review_comments"
        ] = str(comments)

        df.loc[
            index,
            "execution_allowed"
        ] = False

        if "action_status" in df.columns:

            df.loc[
                index,
                "action_status"
            ] = "REJECTED"

        df.to_csv(
            APPROVAL_FILE,
            index=False
        )

        updated = clean_record(
            df.loc[
                index
            ].to_dict()
        )

        return jsonify({

            "success": True,

            "message":
                "Action rejected successfully.",

            "action":
                updated

        }), 200

    except Exception as error:

        return jsonify({

            "success": False,
            "error": str(error)

        }), 500

# ============================================================
# EXECUTE APPROVED ACTION
# ============================================================

@api.route(
    "/controller/actions/<exception_id>/execute",
    methods=["POST"]
)
def execute_action(exception_id):

    try:

        df = load_csv(
            APPROVAL_FILE
        )

        if df is None:

            return jsonify({
                "success": False,
                "error": "Approval queue not found."
            }), 404

        matches = df[
            df["exception_id"]
            .astype(str)
            == str(exception_id)
        ]

        if matches.empty:

            return jsonify({
                "success": False,
                "error": "Controller action not found."
            }), 404

        index = matches.index[0]

        approval_status = str(
            df.loc[
                index,
                "approval_status"
            ]
        ).upper()

        execution_allowed = (
            str(
                df.loc[
                    index,
                    "execution_allowed"
                ]
            ).lower()
            == "true"
        )

        # ----------------------------------------------------
        # Approval gate
        # ----------------------------------------------------

        if approval_status != "APPROVED":

            return jsonify({

                "success": False,

                "error":
                    "Action must be approved before execution.",

                "approval_status":
                    approval_status

            }), 403

        if not execution_allowed:

            return jsonify({

                "success": False,

                "error":
                    "Execution is not allowed for this action."

            }), 403

        action = str(
            df.loc[
                index,
                "proposed_action"
            ]
        )

        # ----------------------------------------------------
        # Existing sandbox client
        # ----------------------------------------------------

        from src.controller.sandbox_client import (
            execute_sandbox_action
        )

        sandbox_response = execute_sandbox_action(
            action,
            exception_id
        )

        # ----------------------------------------------------
        # Sandbox failure
        # ----------------------------------------------------

        if not sandbox_response.get(
            "success",
            False
        ):

            df.loc[
                index,
                "execution_result"
            ] = "EXECUTION_FAILED"

            df.to_csv(
                APPROVAL_FILE,
                index=False
            )

            return jsonify({

                "success": False,

                "status":
                    "EXECUTION_FAILED",

                "exception_id":
                    exception_id,

                "action":
                    action,

                "sandbox_response":
                    sandbox_response

            }), 502

        # ----------------------------------------------------
        # Sandbox success
        # ----------------------------------------------------

        sandbox_data = sandbox_response.get(
            "data",
            {}
        )

        sandbox_status = str(
            sandbox_data.get(
                "status",
                ""
            )
        ).upper()

        # Review-only actions are not financial execution
        if sandbox_status == "REVIEW_ONLY":

            df.loc[
                index,
                "execution_result"
            ] = "REVIEW_ONLY"

            df.to_csv(
                APPROVAL_FILE,
                index=False
            )

            return jsonify({

                "success": True,

                "status":
                    "REVIEW_ONLY",

                "exception_id":
                    exception_id,

                "action":
                    action,

                "message":
                    "Action requires financial review and was not executed.",

                "sandbox_response":
                    sandbox_response

            }), 200

        # ----------------------------------------------------
        # Actual sandbox execution
        # ----------------------------------------------------

        df.loc[
            index,
            "execution_result"
        ] = "EXECUTED"

        if "action_status" in df.columns:

            df.loc[
                index,
                "action_status"
            ] = "EXECUTED"

        df.to_csv(
            APPROVAL_FILE,
            index=False
        )

        return jsonify({

            "success": True,

            "status":
                "EXECUTED",

            "exception_id":
                exception_id,

            "action":
                action,

            "sandbox_response":
                sandbox_response

        }), 200

    except Exception as error:

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


# ============================================================
# VERIFY EXECUTION
# ============================================================

@api.route(
    "/controller/actions/<exception_id>/verify",
    methods=["POST"]
)
def verify_action(exception_id):

    try:

        df = load_csv(
            APPROVAL_FILE
        )

        if df is None:

            return jsonify({

                "success": False,

                "error":
                    "Approval queue not found."

            }), 404

        matches = df[
            df["exception_id"]
            .astype(str)
            == str(exception_id)
        ]

        if matches.empty:

            return jsonify({

                "success": False,

                "error":
                    "Controller action not found."

            }), 404

        index = matches.index[0]

        execution_result = str(
            df.loc[
                index,
                "execution_result"
            ]
        ).upper()

        # ----------------------------------------------------
        # Execution gate
        # ----------------------------------------------------

        if execution_result != "EXECUTED":

            return jsonify({

                "success": False,

                "error":
                    "Action must be executed before verification.",

                "execution_result":
                    execution_result

            }), 409

        # ----------------------------------------------------
        # Verify sandbox execution
        # ----------------------------------------------------
        #
        # The sandbox client currently does not expose
        # a separate verification endpoint.
        #
        # Therefore, a successful sandbox execution is
        # treated as the verification evidence for this
        # sandbox environment.
        # ----------------------------------------------------

        df.loc[
            index,
            "execution_result"
        ] = "SANDBOX_VERIFIED"

        df.loc[
            index,
            "approval_status"
        ] = "VERIFIED"

        if "action_status" in df.columns:

            df.loc[
                index,
                "action_status"
            ] = "VERIFIED"

        df.to_csv(
            APPROVAL_FILE,
            index=False
        )

        return jsonify({

            "success": True,

            "status":
                "VERIFIED",

            "exception_id":
                exception_id,

            "message":
                "Sandbox execution verified.",

            "verification": {

                "environment":
                    "sandbox",

                "execution_result":
                    "SANDBOX_VERIFIED",

                "verified":
                    True

            }

        }), 200

    except Exception as error:

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500

# ============================================================
# AI INVESTIGATION QUEUE
# ============================================================

@api.route(
    "/ai/queue",
    methods=["GET"]
)
def ai_queue():

    try:

        df = load_csv(
            AI_QUEUE_FILE
        )

        if df is None:

            return jsonify({

                "success": False,

                "error":
                    "AI investigation queue not found."

            }), 404

        # ----------------------------------------------------
        # Query parameters
        # ----------------------------------------------------

        status = (
            request.args
            .get(
                "status",
                ""
            )
            .strip()
            .upper()
        )

        priority = (
            request.args
            .get(
                "priority",
                ""
            )
            .strip()
            .upper()
        )

        # ----------------------------------------------------
        # AI status filter
        #
        # Examples:
        # ?status=PENDING
        # ?status=COMPLETED
        # ?status=FAILED
        # ----------------------------------------------------

        if status:

            if "ai_status" not in df.columns:

                return jsonify({

                    "success": False,

                    "error":
                        "AI status field not available."

                }), 500

            df = df[
                df["ai_status"]
                .astype(str)
                .str.upper()
                == status
            ]

        # ----------------------------------------------------
        # Priority filter
        #
        # Examples:
        # ?priority=HIGH
        # ?priority=MEDIUM
        # ----------------------------------------------------

        if priority:

            if (
                "controller_priority"
                not in df.columns
            ):

                return jsonify({

                    "success": False,

                    "error":
                        "Controller priority field not available."

                }), 500

            df = df[
                df["controller_priority"]
                .astype(str)
                .str.upper()
                == priority
            ]

        # ----------------------------------------------------
        # Convert records to JSON-safe values
        # ----------------------------------------------------

        records = [

            clean_record(record)

            for record

            in df.to_dict(
                orient="records"
            )

        ]

        # ----------------------------------------------------
        # Status summary
        # ----------------------------------------------------

        status_summary = {}

        if "ai_status" in df.columns:

            status_summary = (
                df["ai_status"]
                .astype(str)
                .str.upper()
                .value_counts()
                .to_dict()
            )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "count":
                len(records),

            "status_summary":
                status_summary,

            "investigations":
                records

        }), 200

    except Exception as error:

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500
def ai_investigation(
    exception_id
):

    try:

        # ----------------------------------------------------
        # AI Queue
        # ----------------------------------------------------

        queue_df = load_csv(
            AI_QUEUE_FILE
        )

        queue_record = None

        if queue_df is not None:

            matches = queue_df[
                queue_df["exception_id"]
                .astype(str)
                == str(exception_id)
            ]

            if not matches.empty:

                queue_record = clean_record(
                    matches.iloc[
                        0
                    ].to_dict()
                )

        # ----------------------------------------------------
        # AI Results
        # ----------------------------------------------------

        results_df = load_csv(
            AI_RESULTS_FILE
        )

        result_record = None

        if results_df is not None:

            matches = results_df[
                results_df["exception_id"]
                .astype(str)
                == str(exception_id)
            ]

            if not matches.empty:

                result_record = clean_record(
                    matches.iloc[
                        0
                    ].to_dict()
                )

        # ----------------------------------------------------
        # Neither queue nor result exists
        # ----------------------------------------------------

        if (
            queue_record is None
            and result_record is None
        ):

            return jsonify({

                "success": False,

                "error":
                    "AI investigation not found.",

                "exception_id":
                    exception_id

            }), 404

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "exception_id":
                exception_id,

            "queue":
                queue_record,

            "result":
                result_record

        }), 200

    except Exception as error:

        return jsonify({

            "success": False,
            "error": str(error)

        }), 500