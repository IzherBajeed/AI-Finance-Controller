import os
import pandas as pd


# ============================================================
# Configuration
# ============================================================

INPUT_FILE = (
    "data/processed/reconciliation/"
    "reconciliation_results.csv"
)

OUTPUT_DIR = "data/processed/exceptions"

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "exceptions.csv"
)


# ============================================================
# Load Reconciliation Results
# ============================================================

def load_reconciliation():

    return pd.read_csv(
        INPUT_FILE
    )


# ============================================================
# Calculate Financial Differences
# ============================================================

def calculate_differences(df):

    df = df.copy()

    # Settlement difference
    df["settlement_difference"] = (
        df["amount"]
        - df["settled_amount"]
    )

    # Invoice difference
    df["invoice_difference"] = (
        df["amount"]
        - df["invoice_amount"]
    )

    # Settlement delay
    df["payment_date"] = pd.to_datetime(
        df["payment_date"],
        errors="coerce"
    )

    df["settlement_date"] = pd.to_datetime(
        df["settlement_date"],
        errors="coerce"
    )

    df["settlement_delay_days"] = (
        df["settlement_date"]
        - df["payment_date"]
    ).dt.days

    return df


# ============================================================
# Calculate Exception Severity
# ============================================================

def calculate_severity(row):

    issues = str(
        row["issues"]
    )

    amount = abs(
        float(row["amount"])
    )

    settlement_difference = abs(
        float(row["settlement_difference"])
    )

    # Missing settlement
    if "MISSING_SETTLEMENT" in issues:

        if amount >= 100000:
            return "CRITICAL"

        elif amount >= 50000:
            return "HIGH"

        else:
            return "MEDIUM"

    # Multiple issues
    issue_count = len(
        issues.split(";")
    )

    if issue_count >= 2:

        return "HIGH"

    # Large financial difference
    if settlement_difference >= 10000:

        return "HIGH"

    if settlement_difference >= 5000:

        return "MEDIUM"

    # Duplicate payment
    if "DUPLICATE_PAYMENT" in issues:

        if amount >= 50000:
            return "HIGH"

        return "MEDIUM"

    # Invoice mismatch
    if "INVOICE_MISMATCH" in issues:

        return "MEDIUM"

    # Delayed settlement
    if "DELAYED_SETTLEMENT" in issues:

        return "MEDIUM"

    return "LOW"


# ============================================================
# Generate Investigation Summary
# ============================================================

def generate_summary(row):

    issues = str(
        row["issues"]
    )

    payment_id = row["payment_id"]

    amount = row["amount"]

    settlement_amount = row[
        "settled_amount"
    ]

    invoice_amount = row[
        "invoice_amount"
    ]

    summary_parts = []

    # --------------------------------------------------------
    # Missing settlement
    # --------------------------------------------------------

    if "MISSING_SETTLEMENT" in issues:

        summary_parts.append(
            f"Payment {payment_id} "
            f"for ₹{amount:,.2f} "
            f"has no settlement record."
        )

    # --------------------------------------------------------
    # Amount mismatch
    # --------------------------------------------------------

    if "AMOUNT_MISMATCH" in issues:

        difference = abs(
            row["settlement_difference"]
        )

        summary_parts.append(
            f"Payment amount is "
            f"₹{amount:,.2f}, while "
            f"settled amount is "
            f"₹{settlement_amount:,.2f}, "
            f"creating a difference of "
            f"₹{difference:,.2f}."
        )

    # --------------------------------------------------------
    # Invoice mismatch
    # --------------------------------------------------------

    if "INVOICE_MISMATCH" in issues:

        difference = abs(
            row["invoice_difference"]
        )

        summary_parts.append(
            f"Payment amount is "
            f"₹{amount:,.2f}, while "
            f"invoice amount is "
            f"₹{invoice_amount:,.2f}, "
            f"creating a difference of "
            f"₹{difference:,.2f}."
        )

    # --------------------------------------------------------
    # Duplicate
    # --------------------------------------------------------

    if "DUPLICATE_PAYMENT" in issues:

        summary_parts.append(
            f"Payment {payment_id} "
            f"matches another payment "
            f"on invoice, customer, amount "
            f"and payment date."
        )

    # --------------------------------------------------------
    # Delayed settlement
    # --------------------------------------------------------

    if "DELAYED_SETTLEMENT" in issues:

        delay = row[
            "settlement_delay_days"
        ]

        summary_parts.append(
            f"Settlement occurred "
            f"{delay} days after payment."
        )

    return " ".join(
        summary_parts
    )


# ============================================================
# Generate Recommended Investigation
# ============================================================

def generate_recommendation(row):

    issues = str(
        row["issues"]
    )

    if "MISSING_SETTLEMENT" in issues:

        return (
            "Verify settlement status with "
            "the payment processor and "
            "check whether the settlement "
            "batch is missing."
        )

    if "DUPLICATE_PAYMENT" in issues:

        return (
            "Check transaction identifiers "
            "and payment history to determine "
            "whether the payment was processed "
            "more than once."
        )

    if "AMOUNT_MISMATCH" in issues:

        return (
            "Compare settlement amount, "
            "processing fees, taxes and "
            "adjustments to determine the "
            "reason for the difference."
        )

    if "INVOICE_MISMATCH" in issues:

        return (
            "Compare the payment with the "
            "corresponding invoice and verify "
            "whether the invoice amount or "
            "payment amount is incorrect."
        )

    if "DELAYED_SETTLEMENT" in issues:

        return (
            "Review settlement timing and "
            "check whether the delay is "
            "within the expected processing window."
        )

    return (
        "Review the transaction manually."
    )


# ============================================================
# Build Exception Context
# ============================================================

def build_exception_context():

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("EXCEPTION CONTEXT GENERATOR")
    print("=" * 60)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = load_reconciliation()

    print(
        f"\nLoaded records: {len(df)}"
    )

    # --------------------------------------------------------
    # Keep exceptions only
    # --------------------------------------------------------

    exceptions = df[
        df["reconciliation_status"]
        == "EXCEPTION"
    ].copy()

    print(
        f"Exceptions found: "
        f"{len(exceptions)}"
    )

    # --------------------------------------------------------
    # Calculate differences
    # --------------------------------------------------------

    exceptions = calculate_differences(
        exceptions
    )

    # --------------------------------------------------------
    # Severity
    # --------------------------------------------------------

    exceptions["severity"] = (
        exceptions.apply(
            calculate_severity,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Investigation summary
    # --------------------------------------------------------

    exceptions["investigation_summary"] = (
        exceptions.apply(
            generate_summary,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Recommendation
    # --------------------------------------------------------

    exceptions["recommended_action"] = (
        exceptions.apply(
            generate_recommendation,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Exception ID
    # --------------------------------------------------------

    exceptions.insert(
        0,
        "exception_id",
        [
            f"EXC{i:05d}"
            for i in range(
                1,
                len(exceptions) + 1
            )
        ]
    )

    # --------------------------------------------------------
    # Select useful fields
    # --------------------------------------------------------

    output_columns = [

        "exception_id",

        "payment_id",

        "transaction_id",

        "invoice_id",

        "customer_id",

        "payment_date",

        "settlement_date",

        "amount",

        "settled_amount",

        "invoice_amount",

        "fees",

        "tax",

        "settlement_difference",

        "invoice_difference",

        "settlement_delay_days",

        "issues",

        "severity",

        "investigation_summary",

        "recommended_action",

        "payment_method",

        "currency",

    ]

    exceptions = exceptions[
        output_columns
    ]

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    exceptions.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("EXCEPTION SUMMARY")
    print("=" * 60)

    print(
        f"Total exceptions: "
        f"{len(exceptions)}"
    )

    print("\nSeverity distribution:")

    print(
        exceptions[
            "severity"
        ].value_counts()
    )

    print("\nIssue distribution:")

    print(
        exceptions[
            "issues"
        ]
        .str.split(";")
        .explode()
        .value_counts()
    )

    print(
        f"\nSaved to:\n{OUTPUT_FILE}"
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    build_exception_context()