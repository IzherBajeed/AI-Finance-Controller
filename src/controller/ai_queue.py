import os
import pandas as pd


# ============================================================
# Configuration
# ============================================================

CONTROLLER_FILE = (
    "data/processed/controller/"
    "controller_queue.csv"
)

OUTPUT_DIR = (
    "data/processed/controller"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "ai_investigation_queue.csv"
)


# ============================================================
# Build AI Investigation Queue
# ============================================================

def build_ai_queue():

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("AI INVESTIGATION QUEUE")
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

    print(
        f"\nController records: "
        f"{len(controller)}"
    )

    # --------------------------------------------------------
    # Select only AI cases
    # --------------------------------------------------------

    ai_queue = controller[
        controller["workflow"]
        == "AI_INVESTIGATION"
    ].copy()

    print(
        f"AI investigation cases: "
        f"{len(ai_queue)}"
    )

    # --------------------------------------------------------
    # Preserve existing AI processing state
    # --------------------------------------------------------

    if os.path.exists(
        OUTPUT_FILE
    ):

        existing = pd.read_csv(
            OUTPUT_FILE
        )

        existing_states = existing[
            [
                "exception_id",
                "ai_status",
                "ai_attempts",
                "ai_result_available",
                "ai_error",
            ]
        ].copy()

        ai_queue = ai_queue.merge(
            existing_states,
            on="exception_id",
            how="left"
        )

    # --------------------------------------------------------
    # Initialize new cases
    # --------------------------------------------------------

    ai_queue[
        "ai_status"
    ] = ai_queue[
        "ai_status"
    ].fillna(
        "PENDING"
    )

    ai_queue[
        "ai_attempts"
    ] = pd.to_numeric(
        ai_queue[
            "ai_attempts"
        ],
        errors="coerce"
    ).fillna(0).astype(int)

    ai_queue[
        "ai_result_available"
    ] = ai_queue[
        "ai_result_available"
    ].fillna(
        False
    )

    ai_queue[
        "ai_error"
    ] = ai_queue[
        "ai_error"
    ].fillna(
        ""
    )

    # --------------------------------------------------------
    # Ensure correct types
    # --------------------------------------------------------

    ai_queue[
        "ai_result_available"
    ] = (
        ai_queue[
            "ai_result_available"
        ]
        .astype(str)
        .str.lower()
        .map({
            "true": True,
            "false": False
        })
        .fillna(False)
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    ai_queue.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("AI QUEUE SUMMARY")
    print("=" * 60)

    print(
        "\nStatus:"
    )

    print(
        ai_queue[
            "ai_status"
        ].value_counts()
    )

    print(
        "\nPriority:"
    )

    print(
        ai_queue[
            "controller_priority"
        ].value_counts()
    )

    print(
        f"\nQueue saved to:\n"
        f"{OUTPUT_FILE}"
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    build_ai_queue()