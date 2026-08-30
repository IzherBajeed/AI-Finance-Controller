import os
from datetime import datetime

import pandas as pd
from flask import Flask, jsonify, request


# ============================================================
# Configuration
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

RECONCILIATION_FILE = os.path.join(
    DATA_DIR,
    "reconciliation",
    "reconciliation_results.csv"
)

EXCEPTIONS_FILE = os.path.join(
    DATA_DIR,
    "exceptions",
    "exceptions.csv"
)

ACTIONS_FILE = os.path.join(
    DATA_DIR,
    "controller",
    "approval_queue.csv"
)

SANDBOX_DIR = os.path.join(
    DATA_DIR,
    "sandbox"
)

SANDBOX_ACTIONS_FILE = os.path.join(
    SANDBOX_DIR,
    "executed_actions.csv"
)


# ============================================================
# Flask Application
# ============================================================

app = Flask(__name__)


# ============================================================
# Helper Functions
# ============================================================

def load_csv(path):

    if not os.path.exists(path):

        return pd.DataFrame()

    return pd.read_csv(path)


def save_csv(df, path):

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True
    )

    df.to_csv(
        path,
        index=False
    )


def record_sandbox_action(
    exception_id,
    action,
    status,
    details=""
):

    actions = load_csv(
        SANDBOX_ACTIONS_FILE
    )

    new_record = pd.DataFrame([
        {
            "exception_id": exception_id,
            "action": action,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            )
        }
    ])

    actions = pd.concat(
        [
            actions,
            new_record
        ],
        ignore_index=True
    )

    save_csv(
        actions,
        SANDBOX_ACTIONS_FILE
    )


# ============================================================
# Health Check
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return jsonify({
        "service": "AI Finance Controller Sandbox",
        "status": "running",
        "environment": "sandbox"
    })


# ============================================================
# Health API
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    return jsonify({
        "status": "healthy",
        "service": "finance-sandbox",
        "timestamp": datetime.now().isoformat(
            timespec="seconds"
        )
    })


# ============================================================
# Get Transactions
# ============================================================

@app.route(
    "/api/transactions",
    methods=["GET"]
)
def get_transactions():

    df = load_csv(
        RECONCILIATION_FILE
    )

    if df.empty:

        return jsonify({
            "success": False,
            "message": "Transaction data unavailable."
        }), 404

    # Optional filtering
    status = request.args.get(
        "status"
    )

    if status:

        if "reconciliation_status" in df.columns:

            df = df[
                df[
                    "reconciliation_status"
                ].astype(str).str.upper()
                == status.upper()
            ]

    limit = request.args.get(
        "limit",
        default=100,
        type=int
    )

    limit = max(
        1,
        min(limit, 1000)
    )

    df = df.head(
        limit
    )

    return jsonify({
        "success": True,
        "count": len(df),
        "transactions": df.fillna("").to_dict(
            orient="records"
        )
    })


# ============================================================
# Get Single Transaction
# ============================================================

@app.route(
    "/api/transactions/<payment_id>",
    methods=["GET"]
)
def get_transaction(payment_id):

    df = load_csv(
        RECONCILIATION_FILE
    )

    if df.empty:

        return jsonify({
            "success": False,
            "message": "Transaction data unavailable."
        }), 404

    result = df[
        df["payment_id"].astype(str)
        == str(payment_id)
    ]

    if result.empty:

        return jsonify({
            "success": False,
            "message": "Transaction not found."
        }), 404

    return jsonify({
        "success": True,
        "transaction": result.iloc[0]
        .fillna("")
        .to_dict()
    })


# ============================================================
# Get Exceptions
# ============================================================

@app.route(
    "/api/exceptions",
    methods=["GET"]
)
def get_exceptions():

    df = load_csv(
        EXCEPTIONS_FILE
    )

    if df.empty:

        return jsonify({
            "success": False,
            "message": "Exception data unavailable."
        }), 404

    severity = request.args.get(
        "severity"
    )

    issue = request.args.get(
        "issue"
    )

    if severity:

        df = df[
            df["severity"].astype(str).str.upper()
            == severity.upper()
        ]

    if issue:

        df = df[
            df["issues"].astype(str).str.contains(
                issue,
                case=False,
                na=False
            )
        ]

    return jsonify({
        "success": True,
        "count": len(df),
        "exceptions": df.fillna("").to_dict(
            orient="records"
        )
    })


# ============================================================
# Get Single Exception
# ============================================================

@app.route(
    "/api/exceptions/<exception_id>",
    methods=["GET"]
)
def get_exception(exception_id):

    df = load_csv(
        EXCEPTIONS_FILE
    )

    if df.empty:

        return jsonify({
            "success": False,
            "message": "Exception data unavailable."
        }), 404

    result = df[
        df["exception_id"].astype(str)
        == str(exception_id)
    ]

    if result.empty:

        return jsonify({
            "success": False,
            "message": "Exception not found."
        }), 404

    return jsonify({
        "success": True,
        "exception": result.iloc[0]
        .fillna("")
        .to_dict()
    })


# ============================================================
# Get Approval Queue
# ============================================================

@app.route(
    "/api/approvals",
    methods=["GET"]
)
def get_approvals():

    df = load_csv(
        ACTIONS_FILE
    )

    if df.empty:

        return jsonify({
            "success": False,
            "message": "Approval queue unavailable."
        }), 404

    status = request.args.get(
        "status"
    )

    if status:

        df = df[
            df["approval_status"].astype(str).str.upper()
            == status.upper()
        ]

    return jsonify({
        "success": True,
        "count": len(df),
        "approvals": df.fillna("").to_dict(
            orient="records"
        )
    })


# ============================================================
# Verify Settlement — Sandbox
# ============================================================

@app.route(
    "/api/actions/verify-settlement",
    methods=["POST"]
)
def verify_settlement():

    data = request.get_json(
        silent=True
    ) or {}

    exception_id = data.get(
        "exception_id"
    )

    if not exception_id:

        return jsonify({
            "success": False,
            "message": "exception_id is required."
        }), 400

    df = load_csv(
        EXCEPTIONS_FILE
    )

    if df.empty:

        return jsonify({
            "success": False,
            "message": "Exception data unavailable."
        }), 404

    result = df[
        df["exception_id"].astype(str)
        == str(exception_id)
    ]

    if result.empty:

        return jsonify({
            "success": False,
            "message": "Exception not found."
        }), 404

    exception = result.iloc[0]

    record_sandbox_action(
        exception_id,
        "VERIFY_SETTLEMENT",
        "SANDBOX_EXECUTED",
        (
            f"Settlement verification requested "
            f"for payment {exception['payment_id']}"
        )
    )

    return jsonify({
        "success": True,
        "environment": "sandbox",
        "action": "VERIFY_SETTLEMENT",
        "exception_id": exception_id,
        "payment_id": exception["payment_id"],
        "status": "SANDBOX_EXECUTED",
        "message": (
            "Settlement verification simulated successfully."
        )
    })


# ============================================================
# Investigate Duplicate — Sandbox
# ============================================================

@app.route(
    "/api/actions/investigate-duplicate",
    methods=["POST"]
)
def investigate_duplicate():

    data = request.get_json(
        silent=True
    ) or {}

    exception_id = data.get(
        "exception_id"
    )

    if not exception_id:

        return jsonify({
            "success": False,
            "message": "exception_id is required."
        }), 400

    df = load_csv(
        EXCEPTIONS_FILE
    )

    if df.empty:

        return jsonify({
            "success": False,
            "message": "Exception data unavailable."
        }), 404

    result = df[
        df["exception_id"].astype(str)
        == str(exception_id)
    ]

    if result.empty:

        return jsonify({
            "success": False,
            "message": "Exception not found."
        }), 404

    exception = result.iloc[0]

    record_sandbox_action(
        exception_id,
        "INVESTIGATE_DUPLICATE",
        "SANDBOX_EXECUTED",
        (
            f"Duplicate investigation requested "
            f"for payment {exception['payment_id']}"
        )
    )

    return jsonify({
        "success": True,
        "environment": "sandbox",
        "action": "INVESTIGATE_DUPLICATE",
        "exception_id": exception_id,
        "payment_id": exception["payment_id"],
        "status": "SANDBOX_EXECUTED",
        "message": (
            "Duplicate payment investigation "
            "simulated successfully."
        )
    })


# ============================================================
# Get Sandbox Actions
# ============================================================

@app.route(
    "/api/sandbox/actions",
    methods=["GET"]
)
def get_sandbox_actions():

    df = load_csv(
        SANDBOX_ACTIONS_FILE
    )

    if df.empty:

        return jsonify({
            "success": True,
            "count": 0,
            "actions": []
        })

    return jsonify({
        "success": True,
        "count": len(df),
        "actions": df.fillna("").to_dict(
            orient="records"
        )
    })


# ============================================================
# Run Application
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("FINANCE SANDBOX API")
    print("=" * 60)

    print(
        "\nEnvironment: SANDBOX"
    )

    print(
        "\nStarting server..."
    )

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )