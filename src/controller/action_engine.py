import os
import pandas as pd


# ============================================================
# AI FINANCE CONTROLLER
# ACTION & APPROVAL ENGINE
# ============================================================


# ============================================================
# Configuration
# ============================================================

CONTROLLER_FILE = (
    "data/processed/controller/"
    "controller_queue.csv"
)

AI_QUEUE_FILE = (
    "data/processed/controller/"
    "ai_investigation_queue.csv"
)

AI_RESULTS_FILE = (
    "data/processed/exceptions/"
    "ai_investigations.csv"
)

OUTPUT_DIR = (
    "data/processed/controller"
)

OUTPUT_FILE = (
    "data/processed/controller/"
    "action_queue.csv"
)


# ============================================================
# Action Definitions
# ============================================================

REVIEW_ACTIONS = {

    "AMOUNT_MISMATCH":
        "REVIEW_SETTLEMENT_DIFFERENCE",

    "INVOICE_MISMATCH":
        "REVIEW_INVOICE_DIFFERENCE",

    "MISSING_SETTLEMENT":
        "VERIFY_SETTLEMENT",

    "DELAYED_SETTLEMENT":
        "REVIEW_SETTLEMENT_DELAY",

    "DUPLICATE_PAYMENT":
        "INVESTIGATE_DUPLICATE",
}


# ============================================================
# Standardize Types
# ============================================================

def standardize_types(df):

    string_columns = [

        "exception_id",
        "payment_id",
        "transaction_id",
        "invoice_id",
        "customer_id",

        "payment_date",
        "settlement_date",

        "issues",
        "severity",

        "investigation_summary",
        "recommended_action",

        "payment_method",
        "currency",

        "controller_priority",
        "workflow",
        "automation_status",
        "queue_status",
        "controller_version",

        "ai_risk_level",
        "likely_cause",
        "ai_reasoning",
        "ai_recommended_action",

        "proposed_action",
        "action_risk",
        "approval_required",
        "action_status",

        "reviewer",
        "review_decision",
        "review_comments",
        "execution_result",
    ]

    for column in string_columns:

        if column not in df.columns:

            df[column] = ""

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
        )

    # --------------------------------------------------------
    # Boolean columns
    # --------------------------------------------------------

    boolean_columns = [
        "requires_human_review",
        "execution_allowed",
    ]

    for column in boolean_columns:

        if column not in df.columns:

            df[column] = False

        else:

            df[column] = (
                df[column]
                .astype(str)
                .str.strip()
                .str.lower()
                .map({
                    "true": True,
                    "1": True,
                    "yes": True,
                    "false": False,
                    "0": False,
                    "no": False,
                })
                .fillna(False)
                .astype(bool)
            )

    return df


# ============================================================
# Determine Action
# ============================================================

def determine_action(
    issue_string
):

    issues = str(
        issue_string
    ).split(";")

    # --------------------------------------------------------
    # Priority order
    #
    # Duplicate payment is treated first because a duplicate
    # can also produce a missing settlement on the duplicate.
    # --------------------------------------------------------

    priority = [
        "DUPLICATE_PAYMENT",
        "MISSING_SETTLEMENT",
        "AMOUNT_MISMATCH",
        "INVOICE_MISMATCH",
        "DELAYED_SETTLEMENT",
    ]

    for issue in priority:

        if issue in issues:

            return REVIEW_ACTIONS[
                issue
            ]

    return "MANUAL_FINANCIAL_REVIEW"


# ============================================================
# Determine Action Risk
# ============================================================

def determine_action_risk(
    action,
    severity
):

    severity = str(
        severity
    ).upper()

    # --------------------------------------------------------
    # High-risk actions
    # --------------------------------------------------------

    if action in {
        "INVESTIGATE_DUPLICATE",
        "VERIFY_SETTLEMENT",
    }:

        if severity == "HIGH":

            return "HIGH"

        return "MEDIUM"

    # --------------------------------------------------------
    # Review actions
    # --------------------------------------------------------

    if action == "REVIEW_SETTLEMENT_DIFFERENCE":

        return "LOW"

    if action == "REVIEW_SETTLEMENT_DELAY":

        return "MEDIUM"

    if action == "REVIEW_INVOICE_DIFFERENCE":

        return "MEDIUM"

    return "HIGH"


# ============================================================
# Determine Approval Requirement
# ============================================================

def determine_approval_requirement(
    action_risk
):

    action_risk = str(
        action_risk
    ).upper()

    if action_risk == "LOW":

        return "NOT_REQUIRED"

    return "REQUIRED"


# ============================================================
# Determine Initial Action Status
# ============================================================

def determine_action_status(
    approval_required
):

    approval_required = str(
        approval_required
    ).upper()

    if approval_required == "REQUIRED":

        return "PENDING_APPROVAL"

    return "READY_FOR_REVIEW"


# ============================================================
# Build Action Queue
# ============================================================

def build_action_queue():

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("ACTION & APPROVAL ENGINE")
    print("=" * 60)

    # --------------------------------------------------------
    # Load controller queue
    # --------------------------------------------------------

    if not os.path.exists(
        CONTROLLER_FILE
    ):

        raise FileNotFoundError(
            f"Controller queue not found:\n"
            f"{CONTROLLER_FILE}"
        )

    controller = pd.read_csv(
        CONTROLLER_FILE
    )

    controller = standardize_types(
        controller
    )

    print(
        f"\nController records: "
        f"{len(controller)}"
    )

    # --------------------------------------------------------
    # Load current AI queue
    # --------------------------------------------------------

    if os.path.exists(
        AI_QUEUE_FILE
    ):

        ai_queue = pd.read_csv(
            AI_QUEUE_FILE
        )

        ai_queue = standardize_types(
            ai_queue
        )

    else:

        ai_queue = pd.DataFrame()

    # --------------------------------------------------------
    # Load actual AI results
    # --------------------------------------------------------

    if os.path.exists(
        AI_RESULTS_FILE
    ):

        ai_results = pd.read_csv(
            AI_RESULTS_FILE
        )

        ai_results = standardize_types(
            ai_results
        )

        print(
            f"AI result records: "
            f"{len(ai_results)}"
        )

    else:

        ai_results = pd.DataFrame()

        print(
            "AI result records: 0"
        )

    # --------------------------------------------------------
    # Start with controller records
    # --------------------------------------------------------

    action_queue = controller.copy()

    # --------------------------------------------------------
    # Add AI information only from actual results
    # --------------------------------------------------------

    if not ai_results.empty:

        ai_columns = [

            "exception_id",
            "ai_risk_level",
            "likely_cause",
            "ai_reasoning",
            "ai_recommended_action",
            "requires_human_review",
        ]

        available = [
            column
            for column in ai_columns
            if column in ai_results.columns
        ]

        if "exception_id" in available:

            ai_data = (
                ai_results[
                    available
                ]
                .drop_duplicates(
                    subset=["exception_id"]
                )
            )

            # Remove potentially stale controller AI fields
            for column in available:

                if column == "exception_id":

                    continue

                if column in action_queue.columns:

                    action_queue.drop(
                        columns=[column],
                        inplace=True
                    )

            action_queue = action_queue.merge(
                ai_data,
                on="exception_id",
                how="left"
            )

    # --------------------------------------------------------
    # Ensure AI fields exist
    # --------------------------------------------------------

    for column in [
        "ai_risk_level",
        "likely_cause",
        "ai_reasoning",
        "ai_recommended_action",
    ]:

        if column not in action_queue.columns:

            action_queue[column] = ""

    if "requires_human_review" not in action_queue.columns:

        action_queue[
            "requires_human_review"
        ] = False

    # --------------------------------------------------------
    # Standardize AI fields
    # --------------------------------------------------------

    action_queue = standardize_types(
        action_queue
    )

    # --------------------------------------------------------
    # Determine proposed actions
    # --------------------------------------------------------

    action_queue[
        "proposed_action"
    ] = action_queue[
        "issues"
    ].apply(
        determine_action
    )

    # --------------------------------------------------------
    # Determine risk
    # --------------------------------------------------------

    action_queue[
        "action_risk"
    ] = action_queue.apply(
        lambda row:
        determine_action_risk(
            row["proposed_action"],
            row["severity"]
        ),
        axis=1
    )

    # --------------------------------------------------------
    # Determine approval requirement
    # --------------------------------------------------------

    action_queue[
        "approval_required"
    ] = action_queue[
        "action_risk"
    ].apply(
        determine_approval_requirement
    )

    # --------------------------------------------------------
    # Determine initial status
    # --------------------------------------------------------

    action_queue[
        "action_status"
    ] = action_queue[
        "approval_required"
    ].apply(
        determine_action_status
    )

    # --------------------------------------------------------
    # Execution is NEVER automatically allowed
    # --------------------------------------------------------

    action_queue[
        "execution_allowed"
    ] = False

    # --------------------------------------------------------
    # Review fields
    # --------------------------------------------------------

    if "reviewer" not in action_queue.columns:

        action_queue["reviewer"] = ""

    if "review_decision" not in action_queue.columns:

        action_queue["review_decision"] = ""

    if "review_comments" not in action_queue.columns:

        action_queue["review_comments"] = ""

    if "execution_result" not in action_queue.columns:

        action_queue["execution_result"] = ""

    # --------------------------------------------------------
    # Controller metadata
    # --------------------------------------------------------

    action_queue[
        "action_engine_version"
    ] = "1.0"

    # --------------------------------------------------------
    # Final type normalization
    # --------------------------------------------------------

    action_queue = standardize_types(
        action_queue
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    action_queue.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "ACTION QUEUE SUMMARY"
    )

    print(
        "=" * 60
    )

    print(
        "\nProposed actions:"
    )

    print(
        action_queue[
            "proposed_action"
        ].value_counts()
    )

    print(
        "\nAction risk:"
    )

    print(
        action_queue[
            "action_risk"
        ].value_counts()
    )

    print(
        "\nApproval requirement:"
    )

    print(
        action_queue[
            "approval_required"
        ].value_counts()
    )

    print(
        "\nAction status:"
    )

    print(
        action_queue[
            "action_status"
        ].value_counts()
    )

    print(
        "\nExecution allowed:"
    )

    print(
        action_queue[
            "execution_allowed"
        ].value_counts()
    )

    print(
        f"\nAction queue saved to:\n"
        f"{OUTPUT_FILE}"
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    build_action_queue()