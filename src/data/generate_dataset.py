import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker


# ============================================================
# Reproducibility
# ============================================================

random.seed(42)
np.random.seed(42)
Faker.seed(42)

fake = Faker()


# ============================================================
# Configuration
# ============================================================

NUM_RECORDS = 1000

OUTPUT_DIR = "data/raw"

PAYMENT_FILE = os.path.join(
    OUTPUT_DIR,
    "payments.csv"
)

SETTLEMENT_FILE = os.path.join(
    OUTPUT_DIR,
    "settlements.csv"
)

INVOICE_FILE = os.path.join(
    OUTPUT_DIR,
    "invoices.csv"
)

GROUND_TRUTH_FILE = os.path.join(
    OUTPUT_DIR,
    "ground_truth.csv"
)


PAYMENT_METHODS = [
    "UPI",
    "CARD",
    "NETBANKING",
    "WALLET",
]

CURRENCY = "INR"


# ============================================================
# Exception Configuration
# ============================================================

EXCEPTION_TYPES = [
    "NONE",
    "AMOUNT_MISMATCH",
    "MISSING_SETTLEMENT",
    "DUPLICATE_PAYMENT",
    "INVOICE_MISMATCH",
    "DELAYED_SETTLEMENT",
]

EXCEPTION_WEIGHTS = [
    85,  # NONE
    5,   # AMOUNT_MISMATCH
    3,   # MISSING_SETTLEMENT
    2,   # DUPLICATE_PAYMENT
    3,   # INVOICE_MISMATCH
    2,   # DELAYED_SETTLEMENT
]


# ============================================================
# Helper Functions
# ============================================================

def random_date(start_date, end_date):
    """Generate a random date between two dates."""

    days = (end_date - start_date).days

    return start_date + timedelta(
        days=random.randint(0, days)
    )


def generate_amount():
    """Generate a realistic transaction amount."""

    return round(
        random.uniform(500, 100000),
        2
    )


def generate_customer_id():
    """Generate a customer ID."""

    return f"CUST{random.randint(1, 300):04d}"


# ============================================================
# Dataset Generator
# ============================================================

def generate_dataset():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    start_date = datetime(
        2026,
        7,
        1
    )

    end_date = datetime(
        2026,
        8,
        20
    )

    payments = []
    settlements = []
    invoices = []
    ground_truth = []

    # --------------------------------------------------------
    # Main records
    # --------------------------------------------------------

    for i in range(
        1,
        NUM_RECORDS + 1
    ):

        # ----------------------------------------------------
        # IDs
        # ----------------------------------------------------

        payment_id = f"PAY{i:05d}"

        transaction_id = f"TXN{i:05d}"

        invoice_id = f"INV{i:05d}"

        customer_id = generate_customer_id()

        # ----------------------------------------------------
        # Basic payment information
        # ----------------------------------------------------

        payment_date = random_date(
            start_date,
            end_date
        )

        amount = generate_amount()

        payment_method = random.choice(
            PAYMENT_METHODS
        )

        # ----------------------------------------------------
        # Select exception
        # ----------------------------------------------------

        exception_type = random.choices(
            EXCEPTION_TYPES,
            weights=EXCEPTION_WEIGHTS,
            k=1
        )[0]

        # ----------------------------------------------------
        # Payment record
        # ----------------------------------------------------

        payments.append({

            "payment_id": payment_id,

            "transaction_id": transaction_id,

            # IMPORTANT:
            # Explicit relationship between payment
            # and invoice.
            "invoice_id": invoice_id,

            "payment_date": payment_date.strftime(
                "%Y-%m-%d"
            ),

            "customer_id": customer_id,

            "amount": amount,

            "currency": CURRENCY,

            "payment_method": payment_method,

            "status": "SUCCESS",
        })

        # ----------------------------------------------------
        # Invoice
        # ----------------------------------------------------

        invoice_amount = amount

        # Create invoice mismatch
        if exception_type == "INVOICE_MISMATCH":

            invoice_amount = round(
                amount + random.uniform(
                    500,
                    5000
                ),
                2
            )

        invoice_date = (
            payment_date
            - timedelta(
                days=random.randint(
                    0,
                    5
                )
            )
        )

        due_date = (
            invoice_date
            + timedelta(
                days=15
            )
        )

        # For now the paid amount represents the payment
        # received against the invoice.
        paid_amount = amount

        invoices.append({

            "invoice_id": invoice_id,

            "customer_id": customer_id,

            "invoice_date": invoice_date.strftime(
                "%Y-%m-%d"
            ),

            "due_date": due_date.strftime(
                "%Y-%m-%d"
            ),

            "invoice_amount": invoice_amount,

            "paid_amount": paid_amount,

            "status": "PAID",
        })

        # ----------------------------------------------------
        # Settlement
        # ----------------------------------------------------

        settlement_created = True

        settlement_amount = amount

        settlement_delay = random.randint(
            1,
            3
        )

        # -----------------------------------------------
        # Missing settlement
        # -----------------------------------------------

        if exception_type == "MISSING_SETTLEMENT":

            settlement_created = False

        # -----------------------------------------------
        # Amount mismatch
        # -----------------------------------------------

        elif exception_type == "AMOUNT_MISMATCH":

            settlement_amount = round(
                amount
                - random.uniform(
                    100,
                    2000
                ),
                2
            )

        # -----------------------------------------------
        # Delayed settlement
        # -----------------------------------------------

        elif exception_type == "DELAYED_SETTLEMENT":

            settlement_delay = random.randint(
                7,
                15
            )

        # ------------------------------------------------
        # Create settlement
        # ------------------------------------------------

        if settlement_created:

            settlement_date = (
                payment_date
                + timedelta(
                    days=settlement_delay
                )
            )

            # Simulated processing fee
            fees = round(
                amount * 0.015,
                2
            )

            # Simulated tax on fee
            tax = round(
                fees * 0.18,
                2
            )

            settlements.append({

                "settlement_id":
                    f"SET{i:05d}",

                "payment_id":
                    payment_id,

                "settlement_date":
                    settlement_date.strftime(
                        "%Y-%m-%d"
                    ),

                "settled_amount":
                    settlement_amount,

                "fees":
                    fees,

                "tax":
                    tax,

                "status":
                    "SETTLED",
            })

        # ----------------------------------------------------
        # Ground truth
        # ----------------------------------------------------

        ground_truth.append({

            "payment_id":
                payment_id,

            "invoice_id":
                invoice_id,

            "exception_type":
                exception_type,

            "is_exception":
                exception_type != "NONE",

        })

        # ----------------------------------------------------
        # Duplicate payment
        # ----------------------------------------------------

        if exception_type == "DUPLICATE_PAYMENT":

            payments.append({

                # Different payment ID because this is
                # a duplicate transaction record.
                "payment_id":
                    payment_id + "_DUP",

                "transaction_id":
                    transaction_id + "_DUP",

                # Same invoice relationship
                # intentionally creates a duplicate
                # payment against the same invoice.
                "invoice_id":
                    invoice_id,

                "payment_date":
                    payment_date.strftime(
                        "%Y-%m-%d"
                    ),

                "customer_id":
                    customer_id,

                "amount":
                    amount,

                "currency":
                    CURRENCY,

                "payment_method":
                    payment_method,

                "status":
                    "SUCCESS",
            })


    # ========================================================
    # Convert to DataFrames
    # ========================================================

    payments_df = pd.DataFrame(
        payments
    )

    settlements_df = pd.DataFrame(
        settlements
    )

    invoices_df = pd.DataFrame(
        invoices
    )

    ground_truth_df = pd.DataFrame(
        ground_truth
    )


    # ========================================================
    # Save datasets
    # ========================================================

    payments_df.to_csv(
        PAYMENT_FILE,
        index=False
    )

    settlements_df.to_csv(
        SETTLEMENT_FILE,
        index=False
    )

    invoices_df.to_csv(
        INVOICE_FILE,
        index=False
    )

    ground_truth_df.to_csv(
        GROUND_TRUTH_FILE,
        index=False
    )


    # ========================================================
    # Dataset Summary
    # ========================================================

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("DATASET GENERATION")
    print("=" * 60)

    print()

    print(
        f"Payments:       {len(payments_df)}"
    )

    print(
        f"Settlements:    {len(settlements_df)}"
    )

    print(
        f"Invoices:       {len(invoices_df)}"
    )

    print(
        f"Ground Truth:   {len(ground_truth_df)}"
    )

    print()

    print(
        "Exception Distribution:"
    )

    print(
        ground_truth_df[
            "exception_type"
        ].value_counts()
    )

    print()

    print(
        "Files saved to:"
    )

    print(
        f"  {PAYMENT_FILE}"
    )

    print(
        f"  {SETTLEMENT_FILE}"
    )

    print(
        f"  {INVOICE_FILE}"
    )

    print(
        f"  {GROUND_TRUTH_FILE}"
    )

    print()

    print(
        "Dataset generation completed."
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    generate_dataset()