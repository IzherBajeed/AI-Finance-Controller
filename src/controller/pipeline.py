import os
import sys
import subprocess


# ============================================================
# AI FINANCE CONTROLLER
# DETECTION & INVESTIGATION QUEUE PIPELINE
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)


# ============================================================
# Run Pipeline Step
# ============================================================

def run_step(
    step_number,
    total_steps,
    name,
    script
):

    print("\n" + "=" * 60)

    print(
        f"[{step_number}/{total_steps}] {name}"
    )

    print("=" * 60)

    script_path = os.path.join(
        PROJECT_ROOT,
        script
    )

    if not os.path.exists(
        script_path
    ):

        raise FileNotFoundError(
            f"Pipeline script not found:\n"
            f"{script_path}"
        )

    result = subprocess.run(
        [
            sys.executable,
            script_path
        ],
        cwd=PROJECT_ROOT
    )

    if result.returncode != 0:

        print(
            f"\n❌ Step failed: {name}"
        )

        raise RuntimeError(
            f"Pipeline stopped because "
            f"'{script}' failed."
        )

    print(
        f"\n✓ {name} completed"
    )


# ============================================================
# Main Detection Pipeline
# ============================================================

def run_pipeline():

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("DETECTION & INVESTIGATION QUEUE PIPELINE")
    print("=" * 60)

    total_steps = 6

    # --------------------------------------------------------
    # Step 1 — Validate
    # --------------------------------------------------------

    run_step(
        1,
        total_steps,
        "DATA VALIDATION",
        "src/data/validate.py"
    )

    # --------------------------------------------------------
    # Step 2 — Normalize
    # --------------------------------------------------------

    run_step(
        2,
        total_steps,
        "DATA NORMALIZATION",
        "src/data/normalize.py"
    )

    # --------------------------------------------------------
    # Step 3 — Reconciliation
    # --------------------------------------------------------

    run_step(
        3,
        total_steps,
        "FINANCIAL RECONCILIATION",
        "src/reconciliation/reconcile.py"
    )

    # --------------------------------------------------------
    # Step 4 — Exception Context
    # --------------------------------------------------------

    run_step(
        4,
        total_steps,
        "EXCEPTION CONTEXT GENERATION",
        "src/agents/exception_context.py"
    )

    # --------------------------------------------------------
    # Step 5 — Controller
    # --------------------------------------------------------

    run_step(
        5,
        total_steps,
        "EXCEPTION PRIORITIZATION",
        "src/controller/controller.py"
    )

    # --------------------------------------------------------
    # Step 6 — AI Investigation Queue
    # --------------------------------------------------------

    run_step(
        6,
        total_steps,
        "AI INVESTIGATION QUEUE",
        "src/controller/ai_queue.py"
    )

    # --------------------------------------------------------
    # Pipeline Complete
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("DETECTION PIPELINE COMPLETED")
    print("=" * 60)

    print(
        "\nFinancial data has been:"
    )

    print(
        "  ✓ Validated"
    )

    print(
        "  ✓ Normalized"
    )

    print(
        "  ✓ Reconciled"
    )

    print(
        "  ✓ Analyzed for exceptions"
    )

    print(
        "  ✓ Prioritized"
    )

    print(
        "  ✓ Routed to investigation queues"
    )

    print("\nGenerated control artifacts:")

    print(
        "  ✓ Reconciliation results"
    )

    print(
        "  ✓ Exception context"
    )

    print(
        "  ✓ Controller queue"
    )

    print(
        "  ✓ AI investigation queue"
    )

    print("\nNext stage:")

    print(
        "  AI Worker → AI Results → Action Engine"
    )

    print(
        "\nAfter AI investigation:"
    )

    print(
        "  Action Proposal → Human Approval → "
        "Execution → Verification"
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    try:

        run_pipeline()

    except Exception as error:

        print("\n" + "=" * 60)
        print("DETECTION PIPELINE FAILED")
        print("=" * 60)

        print(
            f"\nError: {error}"
        )

        sys.exit(1)