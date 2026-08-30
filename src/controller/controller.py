import os
import pandas as pd


# ============================================================
# Configuration
# ============================================================

INPUT_FILE = (
    "data/processed/exceptions/"
    "exceptions.csv"
)

OUTPUT_DIR = (
    "data/processed/controller"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "controller_queue.csv"
)


# ============================================================
# Load Exceptions
# ============================================================

def load_exceptions():

    return pd.read_csv(
        INPUT_FILE
    )


# ============================================================
# Determine Priority
# ============================================================

def determine_priority(row):

    severity = str(
        row["severity"]
    )

    amount = abs(
        float(row["amount"])
    )

    issues = str(
        row["issues"]
    )

    # --------------------------------------------------------
    # Critical financial exposure
    # --------------------------------------------------------

    if amount >= 100000:

        return "CRITICAL"

    # --------------------------------------------------------
    # Missing settlement
    # --------------------------------------------------------

    if "MISSING_SETTLEMENT" in issues:

        if amount >= 50000:
            return "HIGH"

        return "MEDIUM"

    # --------------------------------------------------------
    # Duplicate payment
    # --------------------------------------------------------

    if "DUPLICATE_PAYMENT" in issues:

        if amount >= 50000:
            return "HIGH"

        return "MEDIUM"

    # --------------------------------------------------------
    # Multiple simultaneous issues
    # --------------------------------------------------------

    if ";" in issues:

        return "HIGH"

    # --------------------------------------------------------
    # Existing severity
    # --------------------------------------------------------

    if severity == "HIGH":
        return "HIGH"

    if severity == "MEDIUM":
        return "MEDIUM"

    return "LOW"


# ============================================================
# Decide Workflow
# ============================================================

def determine_workflow(row):

    priority = row[
        "controller_priority"
    ]

    issues = str(
        row["issues"]
    )

    # --------------------------------------------------------
    # Critical / high risk
    # --------------------------------------------------------

    if priority in [
        "CRITICAL",
        "HIGH"
    ]:

        return "AI_INVESTIGATION"

    # --------------------------------------------------------
    # Complex cases
    # --------------------------------------------------------

    if ";" in issues:

        return "AI_INVESTIGATION"

    # --------------------------------------------------------
    # Medium risk
    # --------------------------------------------------------

    if priority == "MEDIUM":

        return "HUMAN_REVIEW"

    # --------------------------------------------------------
    # Low risk
    # --------------------------------------------------------

    return "RULE_BASED_REVIEW"


# ============================================================
# Determine Automation Permission
# ============================================================

def determine_automation(row):

    workflow = row[
        "workflow"
    ]

    # --------------------------------------------------------
    # AI investigation
    # --------------------------------------------------------

    if workflow == "AI_INVESTIGATION":

        return "NOT_AUTOMATED"

    # --------------------------------------------------------
    # Human review
    # --------------------------------------------------------

    if workflow == "HUMAN_REVIEW":

        return "NOT_AUTOMATED"

    # --------------------------------------------------------
    # Rule-based
    # --------------------------------------------------------

    return "SAFE_REVIEW_ONLY"


# ============================================================
# Build Controller Queue
# ============================================================

def build_controller_queue():

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("CONTROLLER ORCHESTRATOR")
    print("=" * 60)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = load_exceptions()

    print(
        f"\nExceptions loaded: "
        f"{len(df)}"
    )

    # --------------------------------------------------------
    # Priority
    # --------------------------------------------------------

    df[
        "controller_priority"
    ] = df.apply(
        determine_priority,
        axis=1
    )

    # --------------------------------------------------------
    # Workflow
    # --------------------------------------------------------

    df[
        "workflow"
    ] = df.apply(
        determine_workflow,
        axis=1
    )

    # --------------------------------------------------------
    # Automation
    # --------------------------------------------------------

    df[
        "automation_status"
    ] = df.apply(
        determine_automation,
        axis=1
    )

    # --------------------------------------------------------
    # Queue status
    # --------------------------------------------------------

    df[
        "queue_status"
    ] = "PENDING"

    # --------------------------------------------------------
    # Controller timestamp
    # --------------------------------------------------------

    df[
        "controller_version"
    ] = "v1.0"

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("CONTROLLER QUEUE")
    print("=" * 60)

    print("\nPriority distribution:")

    print(
        df[
            "controller_priority"
        ].value_counts()
    )

    print("\nWorkflow distribution:")

    print(
        df[
            "workflow"
        ].value_counts()
    )

    print("\nAutomation status:")

    print(
        df[
            "automation_status"
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

    build_controller_queue()