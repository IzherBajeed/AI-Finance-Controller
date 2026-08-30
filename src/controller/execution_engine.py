import os
import pandas as pd

from sandbox_client import (
    execute_sandbox_action
)


# ============================================================
# Configuration
# ============================================================

APPROVAL_FILE = (
    "data/processed/controller/"
    "approval_queue.csv"
)

OUTPUT_DIR = (
    "data/processed/controller"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "approval_queue.csv"
)


# ============================================================
# Execution Policy
# ============================================================

ALLOWED_EXECUTION_STATES = {
    "APPROVED"
}


# ============================================================
# Load Approval Queue
# ============================================================

def load_approval_queue():

    if not os.path.exists(
        APPROVAL_FILE
    ):

        raise FileNotFoundError(
            "Approval queue not found:\n"
            f"{APPROVAL_FILE}"
        )

    return pd.read_csv(
        APPROVAL_FILE,
        dtype={
            "exception_id": str,
            "approval_status": str,
            "proposed_action": str,
            "execution_result": str,
            "reviewer": str,
            "review_decision": str,
            "review_comments": str,
        }
    )


# ============================================================
# Find Exception
# ============================================================

def find_exception(
    df,
    exception_id
):

    mask = (
        df["exception_id"]
        == str(exception_id)
    )

    if not mask.any():

        raise ValueError(
            f"Exception not found: "
            f"{exception_id}"
        )

    return mask


# ============================================================
# Validate Execution Policy
# ============================================================

def validate_execution_policy(
    row
):

    approval_status = str(
        row["approval_status"]
    ).upper()

    execution_allowed = str(
        row.get(
            "execution_allowed",
            False
        )
    ).lower()

    proposed_action = str(
        row["proposed_action"]
    )

    # --------------------------------------------------------
    # Human approval check
    # --------------------------------------------------------

    if approval_status not in (
        ALLOWED_EXECUTION_STATES
    ):

        return (
            False,
            "Execution blocked: "
            "human approval is required."
        )

    # --------------------------------------------------------
    # Explicit execution permission
    # --------------------------------------------------------

    if execution_allowed != "true":

        return (
            False,
            "Execution blocked: "
            "execution permission is not enabled."
        )

    # --------------------------------------------------------
    # Prevent empty actions
    # --------------------------------------------------------

    if not proposed_action:

        return (
            False,
            "Execution blocked: "
            "no proposed action exists."
        )

    # --------------------------------------------------------
    # Prevent already completed actions
    # --------------------------------------------------------

    execution_result = str(
        row.get(
            "execution_result",
            ""
        )
    ).upper()

    if execution_result in (
        "SANDBOX_EXECUTED",
        "SANDBOX_VERIFIED",
    ):

        return (
            False,
            "Execution blocked: "
            "action has already been executed."
        )

    return (
        True,
        "Execution policy passed."
    )


# ============================================================
# Execute One Approved Action
# ============================================================

def execute_exception(
    df,
    exception_id
):

    mask = find_exception(
        df,
        exception_id
    )

    row = df.loc[
        mask
    ].iloc[0]

    # --------------------------------------------------------
    # Policy validation
    # --------------------------------------------------------

    allowed, message = (
        validate_execution_policy(
            row
        )
    )

    if not allowed:

        return {
            "success": False,
            "status": "BLOCKED",
            "exception_id": exception_id,
            "message": message
        }

    # --------------------------------------------------------
    # Extract action
    # --------------------------------------------------------

    action = str(
        row["proposed_action"]
    )

    print(
        f"\nExecuting approved action:"
        f"\n  Exception: {exception_id}"
        f"\n  Action:    {action}"
    )

    # --------------------------------------------------------
    # Call Sandbox Client
    # --------------------------------------------------------

    result = execute_sandbox_action(
        action,
        exception_id
    )

    # --------------------------------------------------------
    # Sandbox failure
    # --------------------------------------------------------

    if not result["success"]:

        df.loc[
            mask,
            "execution_result"
        ] = (
            "EXECUTION_FAILED"
        )

        return {
            "success": False,
            "status": "EXECUTION_FAILED",
            "exception_id": exception_id,
            "message": result["error"],
            "sandbox_response": result["data"]
        }

    # --------------------------------------------------------
    # Sandbox success
    # --------------------------------------------------------

    sandbox_data = result[
        "data"
    ]

    sandbox_status = str(
        sandbox_data.get(
            "status",
            ""
        )
    ).upper()

    # --------------------------------------------------------
    # Review-only action
    # --------------------------------------------------------

    if sandbox_status == "REVIEW_ONLY":

        df.loc[
            mask,
            "execution_result"
        ] = (
            "REVIEW_ONLY"
        )

        return {
            "success": True,
            "status": "REVIEW_ONLY",
            "exception_id": exception_id,
            "message": (
                "Action requires financial "
                "review and was not executed."
            ),
            "sandbox_response": sandbox_data
        }

    # --------------------------------------------------------
    # Actual sandbox execution
    # --------------------------------------------------------

    df.loc[
        mask,
        "approval_status"
    ] = "EXECUTED"

    df.loc[
        mask,
        "execution_result"
    ] = (
        "SANDBOX_EXECUTED"
    )

    return {
        "success": True,
        "status": "EXECUTED",
        "exception_id": exception_id,
        "message": (
            "Approved action executed "
            "successfully in sandbox."
        ),
        "sandbox_response": sandbox_data
    }


# ============================================================
# Verify Executed Action
# ============================================================

def verify_execution(
    df,
    exception_id
):

    mask = find_exception(
        df,
        exception_id
    )

    row = df.loc[
        mask
    ].iloc[0]

    current_status = str(
        row["approval_status"]
    ).upper()

    # --------------------------------------------------------
    # Verification requires execution
    # --------------------------------------------------------

    if current_status != "EXECUTED":

        return {
            "success": False,
            "status": "VERIFICATION_BLOCKED",
            "exception_id": exception_id,
            "message": (
                "Verification requires "
                "successful execution first."
            )
        }

    # --------------------------------------------------------
    # Sandbox verification
    # --------------------------------------------------------

    from sandbox_client import (
    check_sandbox_health
)

    health = check_sandbox_health()

    if not health["success"]:

        return {
            "success": False,
            "status": "VERIFICATION_FAILED",
            "exception_id": exception_id,
            "message": (
                "Sandbox unavailable during "
                "verification."
            )
        }

    # --------------------------------------------------------
    # Verification successful
    # --------------------------------------------------------

    df.loc[
        mask,
        "approval_status"
    ] = "VERIFIED"

    df.loc[
        mask,
        "execution_result"
    ] = (
        "SANDBOX_VERIFIED"
    )

    return {
        "success": True,
        "status": "VERIFIED",
        "exception_id": exception_id,
        "message": (
            "Sandbox execution verified."
        )
    }


# ============================================================
# Save Queue
# ============================================================

def save_queue(
    df
):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )


# ============================================================
# Demo Execution
# ============================================================

def demo_execution():

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("EXECUTION ENGINE")
    print("=" * 60)

    df = load_approval_queue()

    # --------------------------------------------------------
    # Find already approved case
    # --------------------------------------------------------

    approved = df[
        df["approval_status"]
        == "APPROVED"
    ]

    # --------------------------------------------------------
    # If no approved case exists,
    # create a safe demonstration approval.
    # --------------------------------------------------------

    if approved.empty:

        pending = df[
            df["approval_status"]
            == "PENDING_APPROVAL"
        ]

        if pending.empty:

            print(
                "\nNo case available for "
                "execution test."
            )

            return

        exception_id = str(
            pending.iloc[0][
                "exception_id"
            ]
        )

        print(
            f"\nFor demonstration only:"
            f"\nApproving {exception_id}"
        )

        df.loc[
            df["exception_id"]
            == exception_id,
            "approval_status"
        ] = "APPROVED"

        df.loc[
            df["exception_id"]
            == exception_id,
            "execution_allowed"
        ] = True

        df.loc[
            df["exception_id"]
            == exception_id,
            "reviewer"
        ] = "DEMO_REVIEWER"

        df.loc[
            df["exception_id"]
            == exception_id,
            "review_decision"
        ] = "APPROVE"

        save_queue(
            df
        )

    else:

        exception_id = str(
            approved.iloc[0][
                "exception_id"
            ]
        )

    # --------------------------------------------------------
    # Execute
    # --------------------------------------------------------

    result = execute_exception(
        df,
        exception_id
    )

    print(
        "\nExecution result:"
    )

    print(
        result
    )

    # --------------------------------------------------------
    # Save after execution
    # --------------------------------------------------------

    save_queue(
        df
    )

    # --------------------------------------------------------
    # Verify
    # --------------------------------------------------------

    if result["success"] and (
        result["status"]
        == "EXECUTED"
    ):

        verification = (
            verify_execution(
                df,
                exception_id
            )
        )

        print(
            "\nVerification result:"
        )

        print(
            verification
        )

        save_queue(
            df
        )

    print("\n" + "=" * 60)
    print("EXECUTION ENGINE TEST COMPLETED")
    print("=" * 60)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    demo_execution()