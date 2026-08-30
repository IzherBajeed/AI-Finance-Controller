import os
import pandas as pd


# ============================================================
# Configuration
# ============================================================

GROUND_TRUTH_FILE = "data/raw/ground_truth.csv"

RECONCILIATION_FILE = (
    "data/processed/reconciliation/"
    "reconciliation_results.csv"
)

OUTPUT_DIR = "data/processed/reconciliation"


# ============================================================
# Load Data
# ============================================================

def load_data():

    ground_truth = pd.read_csv(
        GROUND_TRUTH_FILE
    )

    reconciliation = pd.read_csv(
        RECONCILIATION_FILE
    )

    return ground_truth, reconciliation


# ============================================================
# Build Expected Labels
# ============================================================

def prepare_ground_truth(ground_truth):

    ground_truth = ground_truth.copy()

    # A base transaction is an exception when its
    # generated exception type is not NONE.
    ground_truth["actual_exception"] = (
        ground_truth["exception_type"] != "NONE"
    )

    return ground_truth


# ============================================================
# Prepare Predictions
# ============================================================

def prepare_predictions(reconciliation):

    reconciliation = reconciliation.copy()

    # The reconciliation engine marks a record as an
    # exception when at least one issue was detected.
    reconciliation["predicted_exception"] = (
        reconciliation["reconciliation_status"]
        == "EXCEPTION"
    )

    # Keep only the original/base payment records.
    #
    # Duplicate records ending with "_DUP" are evaluated
    # separately.
    base_records = (
        ~reconciliation["payment_id"]
        .str.endswith("_DUP")
    )

    reconciliation = reconciliation[
        base_records
    ].copy()

    return reconciliation


# ============================================================
# Calculate Classification Metrics
# ============================================================

def calculate_metrics(
    ground_truth,
    predictions
):

    comparison = ground_truth.merge(
        predictions[
            [
                "payment_id",
                "predicted_exception",
                "issues",
            ]
        ],
        on="payment_id",
        how="left"
    )

    # If a prediction is missing, treat it as normal.
    comparison["predicted_exception"] = (
        comparison["predicted_exception"]
        .fillna(False)
    )

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    actual = comparison[
        "actual_exception"
    ]

    predicted = comparison[
        "predicted_exception"
    ]

    true_positive = int(
        (actual & predicted).sum()
    )

    true_negative = int(
        (~actual & ~predicted).sum()
    )

    false_positive = int(
        (~actual & predicted).sum()
    )

    false_negative = int(
        (actual & ~predicted).sum()
    )

    # --------------------------------------------------------
    # Precision
    # --------------------------------------------------------

    precision = (
        true_positive
        /
        (true_positive + false_positive)
        if (true_positive + false_positive) > 0
        else 0
    )

    # --------------------------------------------------------
    # Recall
    # --------------------------------------------------------

    recall = (
        true_positive
        /
        (true_positive + false_negative)
        if (true_positive + false_negative) > 0
        else 0
    )

    # --------------------------------------------------------
    # F1 Score
    # --------------------------------------------------------

    f1 = (
        2 * precision * recall
        /
        (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    # --------------------------------------------------------
    # Accuracy
    # --------------------------------------------------------

    total = len(comparison)

    accuracy = (
        (true_positive + true_negative)
        / total
        if total > 0
        else 0
    )

    metrics = {
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "accuracy": accuracy,
        "evaluated_records": total,
    }

    return comparison, metrics


# ============================================================
# Evaluate Exception Types
# ============================================================

def evaluate_exception_types(comparison):

    results = []

    exception_types = [
        exception_type
        for exception_type in
        comparison["exception_type"].unique()
        if exception_type != "NONE"
    ]

    for exception_type in exception_types:

        actual = (
            comparison["exception_type"]
            == exception_type
        )

        predicted = (
            comparison["issues"]
            .fillna("")
            .str.contains(
                exception_type,
                regex=False
            )
        )

        true_positive = int(
            (actual & predicted).sum()
        )

        false_positive = int(
            (~actual & predicted).sum()
        )

        false_negative = int(
            (actual & ~predicted).sum()
        )

        precision = (
            true_positive
            /
            (true_positive + false_positive)
            if (true_positive + false_positive) > 0
            else 0
        )

        recall = (
            true_positive
            /
            (true_positive + false_negative)
            if (true_positive + false_negative) > 0
            else 0
        )

        f1 = (
            2 * precision * recall
            /
            (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        results.append({
            "exception_type": exception_type,
            "actual_count": int(actual.sum()),
            "detected_count": int(predicted.sum()),
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
        })

    return pd.DataFrame(results)


# ============================================================
# Evaluate Duplicate Detection
# ============================================================

def evaluate_duplicates(reconciliation):

    # A duplicate scenario creates two payment records:
    #
    # PAYxxxxx
    # PAYxxxxx_DUP
    #
    # The generator creates 12 such scenarios.
    duplicate_records = reconciliation[
        reconciliation["payment_id"]
        .str.endswith("_DUP")
    ].copy()

    detected_duplicates = (
        duplicate_records["issues"]
        .fillna("")
        .str.contains(
            "DUPLICATE_PAYMENT",
            regex=False
        )
    )

    total_duplicates = len(
        duplicate_records
    )

    detected = int(
        detected_duplicates.sum()
    )

    detection_rate = (
        detected / total_duplicates
        if total_duplicates > 0
        else 0
    )

    return {
        "duplicate_records": total_duplicates,
        "detected_duplicates": detected,
        "duplicate_detection_rate": detection_rate,
    }


# ============================================================
# Save Evaluation Report
# ============================================================

def save_report(
    comparison,
    exception_results,
    metrics,
    duplicate_metrics
):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Detailed comparison
    # --------------------------------------------------------

    comparison_file = os.path.join(
        OUTPUT_DIR,
        "evaluation_comparison.csv"
    )

    comparison.to_csv(
        comparison_file,
        index=False
    )

    # --------------------------------------------------------
    # Exception metrics
    # --------------------------------------------------------

    exception_file = os.path.join(
        OUTPUT_DIR,
        "exception_metrics.csv"
    )

    exception_results.to_csv(
        exception_file,
        index=False
    )

    # --------------------------------------------------------
    # Overall metrics
    # --------------------------------------------------------

    metrics_file = os.path.join(
        OUTPUT_DIR,
        "evaluation_metrics.csv"
    )

    metrics_df = pd.DataFrame(
        [metrics]
    )

    metrics_df.to_csv(
        metrics_file,
        index=False
    )

    # --------------------------------------------------------
    # Duplicate metrics
    # --------------------------------------------------------

    duplicate_file = os.path.join(
        OUTPUT_DIR,
        "duplicate_metrics.csv"
    )

    duplicate_df = pd.DataFrame(
        [duplicate_metrics]
    )

    duplicate_df.to_csv(
        duplicate_file,
        index=False
    )

    return (
        comparison_file,
        exception_file,
        metrics_file,
        duplicate_file
    )


# ============================================================
# Main Evaluation Pipeline
# ============================================================

def evaluate():

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("RECONCILIATION EVALUATION")
    print("=" * 60)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    ground_truth, reconciliation = load_data()

    print("\nInput:")
    print(
        f"Ground truth records: "
        f"{len(ground_truth)}"
    )

    print(
        f"Reconciliation records: "
        f"{len(reconciliation)}"
    )

    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    ground_truth = prepare_ground_truth(
        ground_truth
    )

    predictions = prepare_predictions(
        reconciliation
    )

    # --------------------------------------------------------
    # Calculate overall metrics
    # --------------------------------------------------------

    comparison, metrics = calculate_metrics(
        ground_truth,
        predictions
    )

    # --------------------------------------------------------
    # Exception-level metrics
    # --------------------------------------------------------

    exception_results = (
        evaluate_exception_types(
            comparison
        )
    )

    # --------------------------------------------------------
    # Duplicate metrics
    # --------------------------------------------------------

    duplicate_metrics = (
        evaluate_duplicates(
            reconciliation
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    files = save_report(
        comparison,
        exception_results,
        metrics,
        duplicate_metrics
    )

    # --------------------------------------------------------
    # Print overall metrics
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("OVERALL PERFORMANCE")
    print("=" * 60)

    print(
        f"Evaluated records: "
        f"{metrics['evaluated_records']}"
    )

    print(
        f"True positives:    "
        f"{metrics['true_positive']}"
    )

    print(
        f"True negatives:    "
        f"{metrics['true_negative']}"
    )

    print(
        f"False positives:   "
        f"{metrics['false_positive']}"
    )

    print(
        f"False negatives:   "
        f"{metrics['false_negative']}"
    )

    print(
        f"Accuracy:          "
        f"{metrics['accuracy']:.2%}"
    )

    print(
        f"Precision:         "
        f"{metrics['precision']:.2%}"
    )

    print(
        f"Recall:            "
        f"{metrics['recall']:.2%}"
    )

    print(
        f"F1 Score:          "
        f"{metrics['f1_score']:.2%}"
    )

    # --------------------------------------------------------
    # Exception-level report
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("EXCEPTION-LEVEL PERFORMANCE")
    print("=" * 60)

    if len(exception_results) > 0:

        display_columns = [
            "exception_type",
            "actual_count",
            "detected_count",
            "precision",
            "recall",
            "f1_score",
        ]

        report = exception_results[
            display_columns
        ].copy()

        report["precision"] = (
            report["precision"]
            .map(
                lambda x: f"{x:.2%}"
            )
        )

        report["recall"] = (
            report["recall"]
            .map(
                lambda x: f"{x:.2%}"
            )
        )

        report["f1_score"] = (
            report["f1_score"]
            .map(
                lambda x: f"{x:.2%}"
            )
        )

        print(
            report.to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # Duplicate report
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("DUPLICATE PAYMENT PERFORMANCE")
    print("=" * 60)

    print(
        f"Duplicate records: "
        f"{duplicate_metrics['duplicate_records']}"
    )

    print(
        f"Detected duplicates: "
        f"{duplicate_metrics['detected_duplicates']}"
    )

    print(
        f"Detection rate: "
        f"{duplicate_metrics['duplicate_detection_rate']:.2%}"
    )

    # --------------------------------------------------------
    # Output files
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("EVALUATION FILES")
    print("=" * 60)

    for file in files:
        print(file)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    evaluate()