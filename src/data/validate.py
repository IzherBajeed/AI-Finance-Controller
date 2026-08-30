import os
import pandas as pd


# --------------------------------------------------
# Configuration
# --------------------------------------------------

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"


FILES = {
    "payments": "payments.csv",
    "settlements": "settlements.csv",
    "invoices": "invoices.csv",
}


# --------------------------------------------------
# Validation helpers
# --------------------------------------------------

def validate_required_columns(df, required_columns, dataset_name):
    """Check whether all required columns exist."""

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        print(
            f"[ERROR] {dataset_name}: "
            f"Missing columns: {missing_columns}"
        )
        return False

    return True


def validate_missing_values(df, dataset_name):
    """Check for missing values."""

    missing = df.isnull().sum()

    missing = missing[missing > 0]

    if not missing.empty:
        print(f"[WARNING] {dataset_name}: Missing values found:")
        print(missing)
        return False

    return True


def validate_duplicates(df, column, dataset_name):
    """Check duplicate values in a column."""

    duplicates = df[column].duplicated().sum()

    if duplicates > 0:
        print(
            f"[WARNING] {dataset_name}: "
            f"{duplicates} duplicate {column} values found."
        )
        return False

    return True


def validate_positive_amounts(df, amount_column, dataset_name):
    """Check that financial amounts are positive."""

    invalid = (df[amount_column] <= 0).sum()

    if invalid > 0:
        print(
            f"[WARNING] {dataset_name}: "
            f"{invalid} invalid amount values found."
        )
        return False

    return True


def validate_dates(df, date_column, dataset_name):
    """Check whether dates can be parsed."""

    parsed_dates = pd.to_datetime(
        df[date_column],
        errors="coerce"
    )

    invalid = parsed_dates.isnull().sum()

    if invalid > 0:
        print(
            f"[WARNING] {dataset_name}: "
            f"{invalid} invalid dates found."
        )
        return False

    return True


# --------------------------------------------------
# Payments validation
# --------------------------------------------------

def validate_payments(df):
    print("\nValidating Payments...")

    required_columns = [
        "payment_id",
        "transaction_id",
        "payment_date",
        "customer_id",
        "amount",
        "currency",
        "payment_method",
        "status",
    ]

    valid = True

    valid &= validate_required_columns(
        df,
        required_columns,
        "Payments"
    )

    if not valid:
        return False

    valid &= validate_missing_values(
        df,
        "Payments"
    )

    valid &= validate_duplicates(
        df,
        "payment_id",
        "Payments"
    )

    valid &= validate_positive_amounts(
        df,
        "amount",
        "Payments"
    )

    valid &= validate_dates(
        df,
        "payment_date",
        "Payments"
    )

    return bool(valid)


# --------------------------------------------------
# Settlements validation
# --------------------------------------------------

def validate_settlements(df):
    print("\nValidating Settlements...")

    required_columns = [
        "settlement_id",
        "payment_id",
        "settlement_date",
        "settled_amount",
        "fees",
        "tax",
        "status",
    ]

    valid = True

    valid &= validate_required_columns(
        df,
        required_columns,
        "Settlements"
    )

    if not valid:
        return False

    valid &= validate_missing_values(
        df,
        "Settlements"
    )

    valid &= validate_duplicates(
        df,
        "settlement_id",
        "Settlements"
    )

    valid &= validate_positive_amounts(
        df,
        "settled_amount",
        "Settlements"
    )

    valid &= validate_dates(
        df,
        "settlement_date",
        "Settlements"
    )

    return bool(valid)


# --------------------------------------------------
# Invoices validation
# --------------------------------------------------

def validate_invoices(df):
    print("\nValidating Invoices...")

    required_columns = [
        "invoice_id",
        "customer_id",
        "invoice_date",
        "due_date",
        "invoice_amount",
        "paid_amount",
        "status",
    ]

    valid = True

    valid &= validate_required_columns(
        df,
        required_columns,
        "Invoices"
    )

    if not valid:
        return False

    valid &= validate_missing_values(
        df,
        "Invoices"
    )

    valid &= validate_duplicates(
        df,
        "invoice_id",
        "Invoices"
    )

    valid &= validate_positive_amounts(
        df,
        "invoice_amount",
        "Invoices"
    )

    valid &= validate_dates(
        df,
        "invoice_date",
        "Invoices"
    )

    valid &= validate_dates(
        df,
        "due_date",
        "Invoices"
    )

    return bool(valid)


# --------------------------------------------------
# Main validation pipeline
# --------------------------------------------------

def run_validation():

    print("=" * 50)
    print("AI FINANCE CONTROLLER")
    print("DATA VALIDATION PIPELINE")
    print("=" * 50)

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # Load datasets

    payments = pd.read_csv(
        os.path.join(RAW_DIR, FILES["payments"])
    )

    settlements = pd.read_csv(
        os.path.join(RAW_DIR, FILES["settlements"])
    )

    invoices = pd.read_csv(
        os.path.join(RAW_DIR, FILES["invoices"])
    )

    # Validate

    payments_valid = validate_payments(payments)

    settlements_valid = validate_settlements(
        settlements
    )

    invoices_valid = validate_invoices(
        invoices
    )

    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)

    print(
        f"Payments:    "
        f"{'VALID' if payments_valid else 'INVALID'}"
    )

    print(
        f"Settlements: "
        f"{'VALID' if settlements_valid else 'INVALID'}"
    )

    print(
        f"Invoices:    "
        f"{'VALID' if invoices_valid else 'INVALID'}"
    )

    # Save clean datasets

    if payments_valid:
        payments.to_csv(
            os.path.join(
                PROCESSED_DIR,
                "payments.csv"
            ),
            index=False
        )

    if settlements_valid:
        settlements.to_csv(
            os.path.join(
                PROCESSED_DIR,
                "settlements.csv"
            ),
            index=False
        )

    if invoices_valid:
        invoices.to_csv(
            os.path.join(
                PROCESSED_DIR,
                "invoices.csv"
            ),
            index=False
        )

    print("\nValidation completed.")


# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":
    run_validation()