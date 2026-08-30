import os
import pandas as pd


# ============================================================
# Configuration
# ============================================================

DATA_DIR = "data/processed/normalized"
OUTPUT_DIR = "data/processed/reconciliation"

SETTLEMENT_DELAY_LIMIT = 3


# ============================================================
# Load Data
# ============================================================

def load_data():

    payments = pd.read_csv(
        os.path.join(
            DATA_DIR,
            "payments.csv"
        )
    )

    settlements = pd.read_csv(
        os.path.join(
            DATA_DIR,
            "settlements.csv"
        )
    )

    invoices = pd.read_csv(
        os.path.join(
            DATA_DIR,
            "invoices.csv"
        )
    )

    return payments, settlements, invoices


# ============================================================
# Validate Relationships
# ============================================================

def validate_relationships(
    payments,
    settlements,
    invoices
):

    print("\nChecking financial relationships...")

    duplicate_payment_ids = (
        payments["payment_id"]
        .duplicated()
        .sum()
    )

    duplicate_invoice_ids = (
        invoices["invoice_id"]
        .duplicated()
        .sum()
    )

    duplicate_settlement_ids = (
        settlements["settlement_id"]
        .duplicated()
        .sum()
    )

    print(
        f"Duplicate payment IDs:    {duplicate_payment_ids}"
    )

    print(
        f"Duplicate invoice IDs:    {duplicate_invoice_ids}"
    )

    print(
        f"Duplicate settlement IDs: {duplicate_settlement_ids}"
    )

    if duplicate_invoice_ids > 0:
        raise ValueError(
            "Invoice IDs must be unique."
        )

    if duplicate_settlement_ids > 0:
        raise ValueError(
            "Settlement IDs must be unique."
        )


# ============================================================
# Detect Duplicate Payments
# ============================================================

def detect_duplicate_payments(payments):

    duplicate_columns = [
        "invoice_id",
        "customer_id",
        "amount",
        "payment_date"
    ]

    duplicate_mask = (
        payments
        .duplicated(
            subset=duplicate_columns,
            keep=False
        )
    )

    duplicate_payment_ids = set(
        payments.loc[
            duplicate_mask,
            "payment_id"
        ]
    )

    return duplicate_payment_ids


# ============================================================
# Reconciliation Engine
# ============================================================

def reconcile():

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("RECONCILIATION ENGINE")
    print("=" * 60)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    payments, settlements, invoices = load_data()

    print("\nInput records:")

    print(
        f"Payments:       {len(payments)}"
    )

    print(
        f"Settlements:    {len(settlements)}"
    )

    print(
        f"Invoices:       {len(invoices)}"
    )

    # --------------------------------------------------------
    # Validate relationships
    # --------------------------------------------------------

    validate_relationships(
        payments,
        settlements,
        invoices
    )

    # --------------------------------------------------------
    # Convert dates
    # --------------------------------------------------------

    payments["payment_date"] = pd.to_datetime(
        payments["payment_date"]
    )

    settlements["settlement_date"] = pd.to_datetime(
        settlements["settlement_date"]
    )

    invoices["invoice_date"] = pd.to_datetime(
        invoices["invoice_date"]
    )

    invoices["due_date"] = pd.to_datetime(
        invoices["due_date"]
    )

    # --------------------------------------------------------
    # Detect duplicates BEFORE merging
    # --------------------------------------------------------

    duplicate_payment_ids = (
        detect_duplicate_payments(
            payments
        )
    )

    print(
        f"\nPotential duplicate payments: "
        f"{len(duplicate_payment_ids)}"
    )

    # --------------------------------------------------------
    # STEP 1
    # Payment → Settlement
    # --------------------------------------------------------

    reconciliation = payments.merge(
        settlements[
            [
                "settlement_id",
                "payment_id",
                "settlement_date",
                "settled_amount",
                "fees",
                "tax",
                "status"
            ]
        ],
        on="payment_id",
        how="left",
        suffixes=(
            "_payment",
            "_settlement"
        )
    )

    print(
        f"After Payment → Settlement merge: "
        f"{len(reconciliation)} rows"
    )

    # --------------------------------------------------------
    # STEP 2
    # Payment → Invoice
    #
    # IMPORTANT:
    # Match using invoice_id, NOT customer_id.
    # --------------------------------------------------------

    reconciliation = reconciliation.merge(
        invoices[
            [
                "invoice_id",
                "customer_id",
                "invoice_amount",
                "paid_amount",
                "status"
            ]
        ],
        on="invoice_id",
        how="left",
        suffixes=(
            "",
            "_invoice"
        )
    )

    print(
        f"After Payment → Invoice merge: "
        f"{len(reconciliation)} rows"
    )

    # --------------------------------------------------------
    # Initialize reconciliation fields
    # --------------------------------------------------------

    reconciliation["issues"] = ""

    reconciliation["is_reconciled"] = True

    # --------------------------------------------------------
    # Rule 1
    # Missing Settlement
    # --------------------------------------------------------

    missing_settlement = (
        reconciliation["settlement_id"]
        .isna()
    )

    reconciliation.loc[
        missing_settlement,
        "issues"
    ] += "MISSING_SETTLEMENT;"

    reconciliation.loc[
        missing_settlement,
        "is_reconciled"
    ] = False

    # --------------------------------------------------------
    # Rule 2
    # Settlement Amount Mismatch
    # --------------------------------------------------------

    settlement_exists = (
        ~reconciliation["settlement_id"]
        .isna()
    )

    amount_mismatch = (
        settlement_exists
        &
        (
            reconciliation["amount"]
            != reconciliation["settled_amount"]
        )
    )

    reconciliation.loc[
        amount_mismatch,
        "issues"
    ] += "AMOUNT_MISMATCH;"

    reconciliation.loc[
        amount_mismatch,
        "is_reconciled"
    ] = False

    # --------------------------------------------------------
    # Rule 3
    # Invoice Amount Mismatch
    # --------------------------------------------------------

    invoice_exists = (
        ~reconciliation["invoice_id"]
        .isna()
    )

    invoice_mismatch = (
        invoice_exists
        &
        (
            reconciliation["amount"]
            != reconciliation["invoice_amount"]
        )
    )

    reconciliation.loc[
        invoice_mismatch,
        "issues"
    ] += "INVOICE_MISMATCH;"

    reconciliation.loc[
        invoice_mismatch,
        "is_reconciled"
    ] = False

    # --------------------------------------------------------
    # Rule 4
    # Duplicate Payment
    # --------------------------------------------------------

    duplicate_payment = (
        reconciliation["payment_id"]
        .isin(duplicate_payment_ids)
    )

    reconciliation.loc[
        duplicate_payment,
        "issues"
    ] += "DUPLICATE_PAYMENT;"

    reconciliation.loc[
        duplicate_payment,
        "is_reconciled"
    ] = False

    # --------------------------------------------------------
    # Rule 5
    # Delayed Settlement
    # --------------------------------------------------------

    settlement_delay = (
        reconciliation["settlement_date"]
        - reconciliation["payment_date"]
    ).dt.days

    delayed_settlement = (
        settlement_exists
        &
        (
            settlement_delay
            > SETTLEMENT_DELAY_LIMIT
        )
    )

    reconciliation.loc[
        delayed_settlement,
        "issues"
    ] += "DELAYED_SETTLEMENT;"

    reconciliation.loc[
        delayed_settlement,
        "is_reconciled"
    ] = False

    # --------------------------------------------------------
    # Clean issue field
    # --------------------------------------------------------

    reconciliation["issues"] = (
        reconciliation["issues"]
        .str.rstrip(";")
    )

    reconciliation.loc[
        reconciliation["issues"] == "",
        "issues"
    ] = "NONE"

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    reconciliation["reconciliation_status"] = (
        reconciliation["is_reconciled"]
        .map(
            {
                True: "MATCHED",
                False: "EXCEPTION"
            }
        )
    )

    # --------------------------------------------------------
    # Save result
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    output_file = os.path.join(
        OUTPUT_DIR,
        "reconciliation_results.csv"
    )

    reconciliation.to_csv(
        output_file,
        index=False
    )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    total = len(
        reconciliation
    )

    matched = int(
        reconciliation[
            "is_reconciled"
        ].sum()
    )

    exceptions = (
        total - matched
    )

    match_rate = (
        matched / total * 100
        if total > 0
        else 0
    )

    # --------------------------------------------------------
    # Exception distribution
    # --------------------------------------------------------

    exception_counts = (
        reconciliation[
            reconciliation["issues"] != "NONE"
        ]["issues"]
        .str.split(";")
        .explode()
        .value_counts()
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("RECONCILIATION SUMMARY")
    print("=" * 60)

    print(
        f"Total records:      {total}"
    )

    print(
        f"Matched records:    {matched}"
    )

    print(
        f"Exceptions:         {exceptions}"
    )

    print(
        f"Match rate:         {match_rate:.2f}%"
    )

    print("\nException types:")

    if len(exception_counts) > 0:

        print(
            exception_counts
        )

    else:

        print(
            "No exceptions detected."
        )

    print(
        f"\nResults saved to:\n"
        f"{output_file}"
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    reconcile()