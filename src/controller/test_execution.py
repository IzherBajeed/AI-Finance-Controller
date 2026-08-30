import pandas as pd

from approval_engine import apply_approval
from execution_engine import execute_exception
from execution_engine import verify_execution


# ============================================================
# Configuration
# ============================================================

APPROVAL_FILE = (
    "data/processed/controller/"
    "approval_queue.csv"
)

TEST_EXCEPTION_ID = "EXC00003"


# ============================================================
# Main Test
# ============================================================

def main():

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("END-TO-END EXECUTION TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Load approval queue
    # --------------------------------------------------------

    df = pd.read_csv(
        APPROVAL_FILE,
        dtype={
            "exception_id": str,
            "payment_id": str,
            "issues": str,
            "proposed_action": str,
            "approval_status": str,
            "execution_result": str,
            "reviewer": str,
            "review_decision": str,
            "review_comments": str,
        }
    )

    # Keep execution permission as boolean
    if "execution_allowed" in df.columns:

        df["execution_allowed"] = (
            df["execution_allowed"]
            .astype(str)
            .str.lower()
            .map({
                "true": True,
                "false": False
            })
            .fillna(False)
        )

    print(
        f"\nTesting exception: "
        f"{TEST_EXCEPTION_ID}"
    )

    # --------------------------------------------------------
    # Display current state
    # --------------------------------------------------------

    row = df[
        df["exception_id"]
        == TEST_EXCEPTION_ID
    ]

    if row.empty:

        raise ValueError(
            "Test exception not found."
        )

    print(
        "\nCurrent state:"
    )

    print(
        row[
            [
                "exception_id",
                "payment_id",
                "issues",
                "proposed_action",
                "approval_status",
            ]
        ].to_string(index=False)
    )

    # --------------------------------------------------------
    # HUMAN APPROVAL
    # --------------------------------------------------------

    print(
        "\n" + "-" * 60
    )

    print(
        "STEP 1: HUMAN APPROVAL"
    )

    df = apply_approval(
        df,
        TEST_EXCEPTION_ID,
        "APPROVE",
        "DEMO_FINANCE_REVIEWER",
        "Approved for controlled sandbox execution."
    )

    print(
        "Approval status: "
        f"{df.loc[df['exception_id'] == TEST_EXCEPTION_ID, 'approval_status'].iloc[0]}"
    )

    print(
        "Execution allowed: "
        f"{df.loc[df['exception_id'] == TEST_EXCEPTION_ID, 'execution_allowed'].iloc[0]}"
    )

    # --------------------------------------------------------
    # EXECUTION
    # --------------------------------------------------------

    print(
        "\n" + "-" * 60
    )

    print(
        "STEP 2: EXECUTION ENGINE"
    )

    result = execute_exception(
        df,
        TEST_EXCEPTION_ID
    )

    print(
        "\nExecution response:"
    )

    print(
        result
    )

    if not result["success"]:

        print(
            "\nExecution did not complete."
        )

        df.to_csv(
            APPROVAL_FILE,
            index=False
        )

        return

    # --------------------------------------------------------
    # VERIFICATION
    # --------------------------------------------------------

    if result["status"] == "EXECUTED":

        print(
            "\n" + "-" * 60
        )

        print(
            "STEP 3: VERIFICATION"
        )

        verification = verify_execution(
            df,
            TEST_EXCEPTION_ID
        )

        print(
            "\nVerification response:"
        )

        print(
            verification
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    df.to_csv(
        APPROVAL_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Final state
    # --------------------------------------------------------

    final_row = df[
        df["exception_id"]
        == TEST_EXCEPTION_ID
    ].iloc[0]

    print(
        "\n" + "=" * 60
    )

    print(
        "FINAL STATE"
    )

    print(
        f"Exception:          "
        f"{final_row['exception_id']}"
    )

    print(
        f"Action:             "
        f"{final_row['proposed_action']}"
    )

    print(
        f"Approval status:    "
        f"{final_row['approval_status']}"
    )

    print(
        f"Execution result:   "
        f"{final_row['execution_result']}"
    )

    print(
        f"Reviewer:           "
        f"{final_row['reviewer']}"
    )

    print(
        f"Decision:           "
        f"{final_row['review_decision']}"
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "END-TO-END EXECUTION TEST COMPLETED"
    )

    print(
        "=" * 60
    )


if __name__ == "__main__":

    main()