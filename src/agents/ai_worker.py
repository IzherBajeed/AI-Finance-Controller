import os
import json
import pandas as pd


# ============================================================
# AI FINANCE CONTROLLER
# AI INVESTIGATION WORKER
# ============================================================

QUEUE_FILE = (
    "data/processed/controller/"
    "ai_investigation_queue.csv"
)

RESULT_DIR = (
    "data/processed/exceptions"
)

RESULT_FILE = (
    "data/processed/exceptions/"
    "ai_investigations.csv"
)


# ============================================================
# Standardize Queue Types
# ============================================================

def standardize_queue(df):

    string_columns = [
        "exception_id",
        "payment_id",
        "transaction_id",
        "invoice_id",
        "customer_id",
        "issues",
        "severity",
        "controller_priority",
        "workflow",
        "ai_status",
        "ai_error",
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
    # Attempts
    # --------------------------------------------------------

    if "ai_attempts" not in df.columns:

        df["ai_attempts"] = 0

    df["ai_attempts"] = (
        pd.to_numeric(
            df["ai_attempts"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    # --------------------------------------------------------
    # Result availability
    # --------------------------------------------------------

    if "ai_result_available" not in df.columns:

        df["ai_result_available"] = False

    df["ai_result_available"] = (
        df["ai_result_available"]
        .astype(str)
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
# Load Queue
# ============================================================

def load_queue():

    if not os.path.exists(
        QUEUE_FILE
    ):

        raise FileNotFoundError(
            f"AI investigation queue not found:\n"
            f"{QUEUE_FILE}"
        )

    df = pd.read_csv(
        QUEUE_FILE
    )

    return standardize_queue(
        df
    )


# ============================================================
# Load Existing Results
# ============================================================

def load_results():

    if not os.path.exists(
        RESULT_FILE
    ):

        return pd.DataFrame()

    df = pd.read_csv(
        RESULT_FILE
    )

    if "exception_id" not in df.columns:

        return pd.DataFrame()

    df["exception_id"] = (
        df["exception_id"]
        .fillna("")
        .astype(str)
    )

    return df


# ============================================================
# Convert AI Result to Standard Format
# ============================================================

def normalize_ai_result(
    exception,
    result
):

    # --------------------------------------------------------
    # Result may already be a dictionary
    # --------------------------------------------------------

    if isinstance(
        result,
        dict
    ):

        normalized = result.copy()

    else:

        # ----------------------------------------------------
        # Try JSON parsing
        # ----------------------------------------------------

        try:

            normalized = json.loads(
                str(result)
            )

        except Exception:

            normalized = {
                "risk_level": "MEDIUM",
                "likely_cause": "",
                "reasoning": str(result),
                "recommended_action": "",
                "requires_human_review": True,
            }

    # --------------------------------------------------------
    # Required fields
    # --------------------------------------------------------

    risk_level = str(
        normalized.get(
            "risk_level",
            "MEDIUM"
        )
    ).upper()

    if risk_level not in {
        "LOW",
        "MEDIUM",
        "HIGH",
    }:

        risk_level = "MEDIUM"

    likely_cause = str(
        normalized.get(
            "likely_cause",
            ""
        )
    )

    reasoning = str(
        normalized.get(
            "reasoning",
            ""
        )
    )

    recommended_action = str(
        normalized.get(
            "recommended_action",
            ""
        )
    )

    requires_human_review = (
        normalized.get(
            "requires_human_review",
            True
        )
    )

    if isinstance(
        requires_human_review,
        str
    ):

        requires_human_review = (
            requires_human_review
            .strip()
            .lower()
            in {
                "true",
                "1",
                "yes",
            }
        )

    return {

        "exception_id":
            str(
                exception[
                    "exception_id"
                ]
            ),

        "payment_id":
            str(
                exception[
                    "payment_id"
                ]
            ),

        "issues":
            str(
                exception[
                    "issues"
                ]
            ),

        "ai_status":
            "COMPLETED",

        "ai_risk_level":
            risk_level,

        "likely_cause":
            likely_cause,

        "ai_reasoning":
            reasoning,

        "ai_recommended_action":
            recommended_action,

        "requires_human_review":
            bool(
                requires_human_review
            ),
    }


# ============================================================
# Investigate One Exception
# ============================================================

def investigate_one(exception):

    # --------------------------------------------------------
    # Import existing investigation agent
    #
    # IMPORTANT:
    # Use the full package path so this works when the worker
    # is executed from the project root.
    # --------------------------------------------------------

    try:

        from src.agents.investigation_agent import (
            investigate_exception
        )

    except ImportError as error:

        raise ImportError(
            "Could not import "
            "src.agents.investigation_agent. "
            "Make sure investigation_agent.py "
            "exists inside src/agents/."
        ) from error

    # --------------------------------------------------------
    # Run AI investigation
    #
    # Existing agent returns:
    #
    # (
    #     status,
    #     result_dictionary,
    #     error_message
    # )
    # --------------------------------------------------------

    result = investigate_exception(
        exception
    )

    # --------------------------------------------------------
    # Validate return structure
    # --------------------------------------------------------

    if not isinstance(
        result,
        tuple
    ):

        raise TypeError(
            "Investigation agent returned "
            f"unexpected type: "
            f"{type(result).__name__}"
        )

    if len(result) != 3:

        raise ValueError(
            "Unexpected investigation "
            f"result format. Expected 3 "
            f"values, received {len(result)}."
        )

    status, result_data, error_message = result

    # --------------------------------------------------------
    # Validate status
    # --------------------------------------------------------

    status = str(
        status
    ).upper()

    if status != "COMPLETED":

        error_message = str(
            error_message
        ).strip()

        if not error_message:

            error_message = (
                "AI investigation did not "
                f"complete successfully. "
                f"Status: {status}"
            )

        raise RuntimeError(
            error_message
        )

    # --------------------------------------------------------
    # Validate result dictionary
    # --------------------------------------------------------

    if not isinstance(
        result_data,
        dict
    ):

        raise TypeError(
            "AI investigation result "
            "must be a dictionary."
        )

    # --------------------------------------------------------
    # Normalize result
    # --------------------------------------------------------

    return normalize_ai_result(
        exception,
        result_data
    )


# ============================================================
# Process Queue
# ============================================================

def process_queue(
    max_cases=None
):

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("AI INVESTIGATION WORKER")
    print("=" * 60)

    queue = load_queue()

    existing_results = load_results()

    # --------------------------------------------------------
    # Existing successful results
    # --------------------------------------------------------

    completed_ids = set()

    if not existing_results.empty:

        if "ai_status" in existing_results.columns:

            completed = existing_results[
                existing_results[
                    "ai_status"
                ]
                .astype(str)
                .str.upper()
                == "COMPLETED"
            ]

            completed_ids = set(
                completed[
                    "exception_id"
                ]
                .astype(str)
            )

    # --------------------------------------------------------
    # Find cases that need processing
    #
    # Retry:
    #   PENDING
    #   FAILED
    #
    # Skip:
    #   COMPLETED
    # --------------------------------------------------------

    process_mask = (
        queue[
            "ai_status"
        ]
        .astype(str)
        .str.upper()
        .isin(
            [
                "PENDING",
                "FAILED",
            ]
        )
    )

    pending = queue[
        process_mask
    ].copy()

    # Don't process already completed cases
    pending = pending[
        ~pending[
            "exception_id"
        ]
        .astype(str)
        .isin(
            completed_ids
        )
    ]

    if max_cases is not None:

        pending = pending.head(
            max_cases
        )

    print(
        f"\nQueue records: "
        f"{len(queue)}"
    )

    print(
        f"Investigations to process: "
        f"{len(pending)}"
    )

    # --------------------------------------------------------
    # Breakdown
    # --------------------------------------------------------

    if not pending.empty:

        print(
            "\nProcessing status:"
        )

        print(
            pending[
                "ai_status"
            ]
            .astype(str)
            .str.upper()
            .value_counts()
        )

    if pending.empty:

        print(
            "\nNo AI investigations "
            "require processing."
        )

        return

    # --------------------------------------------------------
    # Process cases
    # --------------------------------------------------------

    results = []

    for index, exception in pending.iterrows():

        exception_id = str(
            exception[
                "exception_id"
            ]
        )

        print(
            "\n" + "-" * 60
        )

        print(
            "Processing:"
        )

        print(
            f"Exception: "
            f"{exception_id}"
        )

        print(
            f"Payment:   "
            f"{exception['payment_id']}"
        )

        print(
            f"Issue:     "
            f"{exception['issues']}"
        )

        print(
            f"Previous status: "
            f"{exception['ai_status']}"
        )

        # ----------------------------------------------------
        # Increment attempts
        # ----------------------------------------------------

        queue.loc[
            index,
            "ai_attempts"
        ] += 1

        try:

            # ------------------------------------------------
            # AI investigation
            # ------------------------------------------------

            result = investigate_one(
                exception
            )

            # ------------------------------------------------
            # Add result
            # ------------------------------------------------

            results.append(
                result
            )

            # ------------------------------------------------
            # Update queue
            # ------------------------------------------------

            queue.loc[
                index,
                "ai_status"
            ] = "COMPLETED"

            queue.loc[
                index,
                "ai_result_available"
            ] = True

            queue.loc[
                index,
                "ai_error"
            ] = ""

            print(
                "\n✓ Investigation completed"
            )

            print(
                f"Risk: "
                f"{result['ai_risk_level']}"
            )

            print(
                f"Human review: "
                f"{result['requires_human_review']}"
            )

        except Exception as error:

            queue.loc[
                index,
                "ai_status"
            ] = "FAILED"

            queue.loc[
                index,
                "ai_result_available"
            ] = False

            queue.loc[
                index,
                "ai_error"
            ] = str(
                error
            )

            print(
                "\n✗ Investigation failed"
            )

            print(
                f"Error: {error}"
            )

    # --------------------------------------------------------
    # Save new results
    # --------------------------------------------------------

    if results:

        new_results = pd.DataFrame(
            results
        )

        if existing_results.empty:

            final_results = new_results

        else:

            # Remove any old result for the
            # same exception before inserting
            # the newest successful result.

            existing_results = (
                existing_results[
                    ~existing_results[
                        "exception_id"
                    ]
                    .astype(str)
                    .isin(
                        new_results[
                            "exception_id"
                        ]
                        .astype(str)
                    )
                ]
            )

            final_results = pd.concat(
                [
                    existing_results,
                    new_results,
                ],
                ignore_index=True
            )

        os.makedirs(
            RESULT_DIR,
            exist_ok=True
        )

        final_results.to_csv(
            RESULT_FILE,
            index=False
        )

    # --------------------------------------------------------
    # Save queue
    # --------------------------------------------------------

    queue = standardize_queue(
        queue
    )

    queue.to_csv(
        QUEUE_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "AI WORKER SUMMARY"
    )

    print(
        "=" * 60
    )

    print(
        "\nQueue status:"
    )

    print(
        queue[
            "ai_status"
        ].value_counts()
    )

    print(
        "\nResults saved to:"
    )

    print(
        RESULT_FILE
    )

    print(
        "\nQueue updated:"
    )

    print(
        QUEUE_FILE
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    try:

        process_queue()

    except Exception as error:

        print(
            "\n" + "=" * 60
        )

        print(
            "AI WORKER FAILED"
        )

        print(
            "=" * 60
        )

        print(
            f"\nError: {error}"
        )

        raise