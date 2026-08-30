import os
import pandas as pd


# ============================================================
# AI FINANCE CONTROLLER
# APPROVAL STATE MACHINE
# ============================================================


# ============================================================
# Configuration
# ============================================================

ACTION_FILE = (
    "data/processed/controller/"
    "action_queue.csv"
)

OUTPUT_DIR = (
    "data/processed/controller"
)

OUTPUT_FILE = (
    "data/processed/controller/"
    "approval_queue.csv"
)


# ============================================================
# State Definitions
# ============================================================

VALID_STATES = {
    "PENDING_APPROVAL",
    "APPROVED",
    "REJECTED",
    "EXECUTED",
    "VERIFIED",
}


ALLOWED_TRANSITIONS = {

    "PENDING_APPROVAL": {
        "APPROVED",
        "REJECTED",
    },

    "APPROVED": {
        "EXECUTED",
        "REJECTED",
    },

    "EXECUTED": {
        "VERIFIED",
    },

    "REJECTED": set(),

    "VERIFIED": set(),
}


# ============================================================
# Standardize Data Types
# ============================================================

def standardize_types(df):

    string_columns = [

        "exception_id",
        "payment_id",
        "issues",
        "proposed_action",
        "action_risk",
        "approval_status",
        "execution_result",
        "reviewer",
        "review_decision",
        "review_comments",
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
    # Boolean state
    # --------------------------------------------------------

    if "execution_allowed" not in df.columns:

        df["execution_allowed"] = False

    else:

        df["execution_allowed"] = (
            df["execution_allowed"]
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
# Load Action Queue
# ============================================================

def load_actions():

    if not os.path.exists(
        ACTION_FILE
    ):

        raise FileNotFoundError(
            f"Action queue not found:\n"
            f"{ACTION_FILE}"
        )

    df = pd.read_csv(
        ACTION_FILE
    )

    df = standardize_types(
        df
    )

    # --------------------------------------------------------
    # Initialize approval state
    # --------------------------------------------------------

    if "approval_status" not in df.columns:

        df["approval_status"] = (
            "PENDING_APPROVAL"
        )

    else:

        df["approval_status"] = (
            df["approval_status"]
            .replace(
                "",
                "PENDING_APPROVAL"
            )
        )

    # --------------------------------------------------------
    # Initialize execution state
    # --------------------------------------------------------

    if "execution_result" not in df.columns:

        df["execution_result"] = ""

    # --------------------------------------------------------
    # Set initial execution permission
    # --------------------------------------------------------

    df["execution_allowed"] = (
        df["approval_status"]
        .eq("APPROVED")
    )

    return standardize_types(
        df
    )


# ============================================================
# Validate State
# ============================================================

def validate_state(
    current_state,
    new_state
):

    current_state = str(
        current_state
    ).upper()

    new_state = str(
        new_state
    ).upper()

    if current_state not in VALID_STATES:

        return (
            False,
            f"Unknown current state: "
            f"{current_state}"
        )

    if new_state not in VALID_STATES:

        return (
            False,
            f"Unknown target state: "
            f"{new_state}"
        )

    if new_state not in (
        ALLOWED_TRANSITIONS[
            current_state
        ]
    ):

        return (
            False,
            (
                f"Invalid transition: "
                f"{current_state} → "
                f"{new_state}"
            )
        )

    return (
        True,
        "Valid state transition."
    )


# ============================================================
# Apply Approval Decision
# ============================================================

def apply_approval(
    df,
    exception_id,
    decision,
    reviewer,
    comments=""
):

    df = standardize_types(
        df.copy()
    )

    exception_id = str(
        exception_id
    )

    decision = str(
        decision
    ).upper()

    mask = (
        df["exception_id"]
        == exception_id
    )

    if not mask.any():

        raise ValueError(
            f"Exception not found: "
            f"{exception_id}"
        )

    current_state = str(
        df.loc[
            mask,
            "approval_status"
        ].iloc[0]
    ).upper()

    # --------------------------------------------------------
    # Convert decision → state
    # --------------------------------------------------------

    if decision == "APPROVE":

        new_state = "APPROVED"

    elif decision == "REJECT":

        new_state = "REJECTED"

    else:

        raise ValueError(
            "Decision must be "
            "'APPROVE' or 'REJECT'."
        )

    # --------------------------------------------------------
    # Validate transition
    # --------------------------------------------------------

    valid, message = validate_state(
        current_state,
        new_state
    )

    if not valid:

        raise ValueError(
            message
        )

    # --------------------------------------------------------
    # Apply state
    # --------------------------------------------------------

    df.loc[
        mask,
        "approval_status"
    ] = new_state

    df.loc[
        mask,
        "reviewer"
    ] = str(
        reviewer
    )

    df.loc[
        mask,
        "review_decision"
    ] = decision

    df.loc[
        mask,
        "review_comments"
    ] = str(
        comments
    )

    # --------------------------------------------------------
    # Execution permission
    # --------------------------------------------------------

    if new_state == "APPROVED":

        df.loc[
            mask,
            "execution_allowed"
        ] = True

    else:

        df.loc[
            mask,
            "execution_allowed"
        ] = False

    return standardize_types(
        df
    )


# ============================================================
# Mark Executed
# ============================================================

def mark_executed(
    df,
    exception_id
):

    df = standardize_types(
        df.copy()
    )

    exception_id = str(
        exception_id
    )

    mask = (
        df["exception_id"]
        == exception_id
    )

    if not mask.any():

        raise ValueError(
            f"Exception not found: "
            f"{exception_id}"
        )

    current_state = str(
        df.loc[
            mask,
            "approval_status"
        ].iloc[0]
    )

    valid, message = validate_state(
        current_state,
        "EXECUTED"
    )

    if not valid:

        raise ValueError(
            message
        )

    df.loc[
        mask,
        "approval_status"
    ] = "EXECUTED"

    df.loc[
        mask,
        "execution_result"
    ] = "SANDBOX_EXECUTED"

    return standardize_types(
        df
    )


# ============================================================
# Mark Verified
# ============================================================

def mark_verified(
    df,
    exception_id
):

    df = standardize_types(
        df.copy()
    )

    exception_id = str(
        exception_id
    )

    mask = (
        df["exception_id"]
        == exception_id
    )

    if not mask.any():

        raise ValueError(
            f"Exception not found: "
            f"{exception_id}"
        )

    current_state = str(
        df.loc[
            mask,
            "approval_status"
        ].iloc[0]
    )

    valid, message = validate_state(
        current_state,
        "VERIFIED"
    )

    if not valid:

        raise ValueError(
            message
        )

    df.loc[
        mask,
        "approval_status"
    ] = "VERIFIED"

    df.loc[
        mask,
        "execution_result"
    ] = "SANDBOX_VERIFIED"

    return standardize_types(
        df
    )


# ============================================================
# Save Approval Queue
# ============================================================

def save_approval_queue(
    df
):

    df = standardize_types(
        df
    )

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )


# ============================================================
# Demo State Machine
# ============================================================

def demo_state_transition():

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("APPROVAL STATE MACHINE")
    print("=" * 60)

    df = load_actions()

    print(
        f"\nAction records: "
        f"{len(df)}"
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "APPROVAL QUEUE SUMMARY"
    )

    print(
        "=" * 60
    )

    print(
        df[
            "approval_status"
        ].value_counts()
    )

    save_approval_queue(
        df
    )

    print(
        f"\nApproval queue saved to:\n"
        f"{OUTPUT_FILE}"
    )

    # --------------------------------------------------------
    # State machine demonstration
    # --------------------------------------------------------

    pending = df[
        df["approval_status"]
        == "PENDING_APPROVAL"
    ]

    if pending.empty:

        print(
            "\nNo pending approval case "
            "available for demonstration."
        )

        return

    exception_id = str(
        pending.iloc[0][
            "exception_id"
        ]
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "STATE MACHINE TEST"
    )

    print(
        "=" * 60
    )

    print(
        f"\nTesting exception: "
        f"{exception_id}"
    )

    print(
        "Initial state: "
        f"{df.loc[df['exception_id'] == exception_id, 'approval_status'].iloc[0]}"
    )

    # --------------------------------------------------------
    # Approval
    # --------------------------------------------------------

    df = apply_approval(
        df,
        exception_id,
        "APPROVE",
        "DEMO_REVIEWER",
        "Demonstration approval."
    )

    print(
        "After approval: "
        f"{df.loc[df['exception_id'] == exception_id, 'approval_status'].iloc[0]}"
    )

    # --------------------------------------------------------
    # Execution
    # --------------------------------------------------------

    df = mark_executed(
        df,
        exception_id
    )

    print(
        "After execution: "
        f"{df.loc[df['exception_id'] == exception_id, 'approval_status'].iloc[0]}"
    )

    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    df = mark_verified(
        df,
        exception_id
    )

    print(
        "After verification: "
        f"{df.loc[df['exception_id'] == exception_id, 'approval_status'].iloc[0]}"
    )

    save_approval_queue(
        df
    )

    print(
        "\nState machine test completed successfully."
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    demo_state_transition()