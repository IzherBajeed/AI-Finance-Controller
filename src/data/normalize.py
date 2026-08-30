import os
import pandas as pd


# --------------------------------------------------
# Configuration
# --------------------------------------------------

INPUT_DIR = "data/processed"
OUTPUT_DIR = "data/processed/normalized"


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def normalize_id(series):
    """Standardize IDs."""

    return (
        series
        .astype(str)
        .str.strip()
        .str.upper()
    )


def normalize_amount(series):
    """Convert financial values into numeric format."""

    return (
        series
        .astype(str)
        .str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
        .astype(float)
        .round(2)
    )


def normalize_date(series):
    """Convert dates into YYYY-MM-DD format."""

    return pd.to_datetime(
        series,
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")


def normalize_text(series):
    """Standardize text values."""

    return (
        series
        .astype(str)
        .str.strip()
        .str.upper()
    )


# --------------------------------------------------
# Normalize Payments
# --------------------------------------------------

def normalize_payments(df):

    df = df.copy()

    df["payment_id"] = normalize_id(
        df["payment_id"]
    )

    df["transaction_id"] = normalize_id(
        df["transaction_id"]
    )

    df["customer_id"] = normalize_id(
        df["customer_id"]
    )

    df["payment_date"] = normalize_date(
        df["payment_date"]
    )

    df["amount"] = normalize_amount(
        df["amount"]
    )

    df["currency"] = normalize_text(
        df["currency"]
    )

    df["payment_method"] = normalize_text(
        df["payment_method"]
    )

    df["status"] = normalize_text(
        df["status"]
    )

    return df


# --------------------------------------------------
# Normalize Settlements
# --------------------------------------------------

def normalize_settlements(df):

    df = df.copy()

    df["settlement_id"] = normalize_id(
        df["settlement_id"]
    )

    df["payment_id"] = normalize_id(
        df["payment_id"]
    )

    df["settlement_date"] = normalize_date(
        df["settlement_date"]
    )

    df["settled_amount"] = normalize_amount(
        df["settled_amount"]
    )

    df["fees"] = normalize_amount(
        df["fees"]
    )

    df["tax"] = normalize_amount(
        df["tax"]
    )

    df["status"] = normalize_text(
        df["status"]
    )

    return df


# --------------------------------------------------
# Normalize Invoices
# --------------------------------------------------

def normalize_invoices(df):

    df = df.copy()

    df["invoice_id"] = normalize_id(
        df["invoice_id"]
    )

    df["customer_id"] = normalize_id(
        df["customer_id"]
    )

    df["invoice_date"] = normalize_date(
        df["invoice_date"]
    )

    df["due_date"] = normalize_date(
        df["due_date"]
    )

    df["invoice_amount"] = normalize_amount(
        df["invoice_amount"]
    )

    df["paid_amount"] = normalize_amount(
        df["paid_amount"]
    )

    df["status"] = normalize_text(
        df["status"]
    )

    return df


# --------------------------------------------------
# Main normalization pipeline
# --------------------------------------------------

def run_normalization():

    print("=" * 55)
    print("AI FINANCE CONTROLLER")
    print("DATA NORMALIZATION PIPELINE")
    print("=" * 55)

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    # Load processed datasets

    payments = pd.read_csv(
        os.path.join(
            INPUT_DIR,
            "payments.csv"
        )
    )

    settlements = pd.read_csv(
        os.path.join(
            INPUT_DIR,
            "settlements.csv"
        )
    )

    invoices = pd.read_csv(
        os.path.join(
            INPUT_DIR,
            "invoices.csv"
        )
    )

    print("\nNormalizing Payments...")
    payments = normalize_payments(
        payments
    )

    print("Normalizing Settlements...")
    settlements = normalize_settlements(
        settlements
    )

    print("Normalizing Invoices...")
    invoices = normalize_invoices(
        invoices
    )

    # Save normalized datasets

    payments.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "payments.csv"
        ),
        index=False
    )

    settlements.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "settlements.csv"
        ),
        index=False
    )

    invoices.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "invoices.csv"
        ),
        index=False
    )

    print("\nNormalization completed.")

    print("\nOutput:")
    print(
        f"Payments:       {len(payments)} records"
    )
    print(
        f"Settlements:    {len(settlements)} records"
    )
    print(
        f"Invoices:       {len(invoices)} records"
    )


# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":
    run_normalization()