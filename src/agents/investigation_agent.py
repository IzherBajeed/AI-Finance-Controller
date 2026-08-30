import json
import os
import time

import pandas as pd
from dotenv import load_dotenv
from google import genai


# ============================================================
# Configuration
# ============================================================

QUEUE_FILE = (
    "data/processed/controller/"
    "ai_investigation_queue.csv"
)

OUTPUT_DIR = (
    "data/processed/exceptions"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "ai_investigations.csv"
)

MODEL_NAME = "gemini-2.5-flash"

MAX_RETRIES = 2

RETRY_DELAY_SECONDS = 3


# ============================================================
# Environment
# ============================================================

load_dotenv()

API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

if not API_KEY:

    raise ValueError(
        "GEMINI_API_KEY was not found in .env"
    )


# ============================================================
# Gemini Client
# ============================================================

client = genai.Client(
    api_key=API_KEY
)


# ============================================================
# Load Queue
# ============================================================

def load_queue():

    return pd.read_csv(
        QUEUE_FILE
    )


# ============================================================
# Build Prompt
# ============================================================

def build_prompt(exception):

    return f"""
You are an AI Finance Controller investigating
a financial transaction exception.

Analyze ONLY the financial evidence provided below.

IMPORTANT RULES:

1. Do not invent facts.
2. Do not modify financial amounts.
3. Do not override the detected exception.
4. Clearly distinguish facts from possible causes.
5. If evidence is insufficient, say so.
6. Do not authorize a payment, refund, reversal,
   transfer, or other financial action.
7. Recommend investigation steps only.
8. A human must approve material financial actions.

Return ONLY valid JSON.

Required JSON:

{{
    "risk_level": "LOW | MEDIUM | HIGH | CRITICAL",
    "likely_cause": "string",
    "reasoning": "string",
    "recommended_action": "string",
    "requires_human_review": true
}}

------------------------------------------------------------
EXCEPTION
------------------------------------------------------------

Exception ID:
{exception["exception_id"]}

Payment ID:
{exception["payment_id"]}

Transaction ID:
{exception["transaction_id"]}

Invoice ID:
{exception["invoice_id"]}

Customer ID:
{exception["customer_id"]}

Detected Issue:
{exception["issues"]}

Controller Priority:
{exception["controller_priority"]}

------------------------------------------------------------
FINANCIAL DATA
------------------------------------------------------------

Payment Amount:
₹{exception["amount"]:,.2f}

Settlement Amount:
{exception["settled_amount"]}

Invoice Amount:
₹{exception["invoice_amount"]:,.2f}

Fees:
₹{exception["fees"]:,.2f}

Tax:
₹{exception["tax"]:,.2f}

Settlement Difference:
₹{exception["settlement_difference"]:,.2f}

Invoice Difference:
₹{exception["invoice_difference"]:,.2f}

------------------------------------------------------------
TIMING
------------------------------------------------------------

Payment Date:
{exception["payment_date"]}

Settlement Date:
{exception["settlement_date"]}

Settlement Delay:
{exception["settlement_delay_days"]}

------------------------------------------------------------
PAYMENT
------------------------------------------------------------

Payment Method:
{exception["payment_method"]}

Currency:
{exception["currency"]}

------------------------------------------------------------

Explain:

1. What the evidence shows.
2. The most plausible cause supported by
   the evidence.
3. What should be investigated next.
4. Whether human review is required.

Do not claim certainty when the evidence
does not establish the cause.
"""


# ============================================================
# Parse JSON
# ============================================================

def parse_json_response(text):

    text = text.strip()

    if text.startswith("```json"):

        text = text[len("```json"):]

    elif text.startswith("```"):

        text = text[len("```"):]

    if text.endswith("```"):

        text = text[:-3]

    text = text.strip()

    return json.loads(
        text
    )


# ============================================================
# Safe Fallback
# ============================================================

def fallback_response(exception):

    return {

        "risk_level":
            exception["controller_priority"],

        "likely_cause":
            "AI investigation unavailable.",

        "reasoning":
            (
                "The deterministic reconciliation "
                "engine detected this exception. "
                "AI investigation could not be "
                "completed because the AI service "
                "was unavailable or rate limited."
            ),

        "recommended_action":
            exception[
                "recommended_action"
            ],

        "requires_human_review":
            True,
    }


# ============================================================
# Detect Rate Limit
# ============================================================

def is_rate_limit_error(error):

    error_text = str(
        error
    ).lower()

    return (
        "429" in error_text
        or
        "resource_exhausted" in error_text
        or
        "quota" in error_text
        or
        "rate limit" in error_text
    )


# ============================================================
# Investigate One Exception
# ============================================================

def investigate_exception(exception):

    prompt = build_prompt(
        exception
    )

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            response = (
                client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt
                )
            )

            result = parse_json_response(
                response.text
            )

            required_fields = [
                "risk_level",
                "likely_cause",
                "reasoning",
                "recommended_action",
                "requires_human_review"
            ]

            for field in required_fields:

                if field not in result:

                    raise ValueError(
                        f"Missing field: {field}"
                    )

            return (
                "COMPLETED",
                result,
                ""
            )

        except Exception as error:

            print(
                f"  Attempt {attempt} failed: "
                f"{error}"
            )

            # ------------------------------------------------
            # Do NOT retry quota errors.
            # ------------------------------------------------

            if is_rate_limit_error(error):

                return (
                    "RATE_LIMITED",
                    fallback_response(
                        exception
                    ),
                    str(error)
                )

            # ------------------------------------------------
            # Retry temporary errors.
            # ------------------------------------------------

            if attempt < MAX_RETRIES:

                time.sleep(
                    RETRY_DELAY_SECONDS
                )

    return (
        "FAILED",
        fallback_response(
            exception
        ),
        "AI investigation failed."
    )


# ============================================================
# Run Queue Worker
# ============================================================

def run_queue_worker():

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("AI INVESTIGATION QUEUE WORKER")
    print("=" * 60)

    # --------------------------------------------------------
    # Load queue
    # --------------------------------------------------------

    queue = load_queue()

    print(
        f"\nQueue records: "
        f"{len(queue)}"
    )

    # --------------------------------------------------------
    # Select pending cases only
    # --------------------------------------------------------

    pending = queue[
        queue["ai_status"]
        == "PENDING"
    ].copy()

    print(
        f"Pending cases: "
        f"{len(pending)}"
    )

    if pending.empty:

        print(
            "\nNo pending AI investigations."
        )

        return

    # --------------------------------------------------------
    # Existing results
    # --------------------------------------------------------

    if os.path.exists(
        OUTPUT_FILE
    ):

        existing_results = pd.read_csv(
            OUTPUT_FILE
        )

    else:

        existing_results = pd.DataFrame()

    # --------------------------------------------------------
    # Process cases
    # --------------------------------------------------------

    new_results = []

    for index, exception in pending.iterrows():

        exception_id = (
            exception["exception_id"]
        )

        payment_id = (
            exception["payment_id"]
        )

        print(
            f"\n[{index + 1}/{len(queue)}] "
            f"{exception_id} "
            f"({payment_id})"
        )

        status, ai_result, error = (
            investigate_exception(
                exception
            )
        )

        # ----------------------------------------------------
        # Result record
        # ----------------------------------------------------

        result = {

            "exception_id":
                exception_id,

            "payment_id":
                payment_id,

            "detected_issue":
                exception["issues"],

            "controller_priority":
                exception[
                    "controller_priority"
                ],

            "ai_status":
                status,

            "ai_risk_level":
                ai_result[
                    "risk_level"
                ],

            "likely_cause":
                ai_result[
                    "likely_cause"
                ],

            "ai_reasoning":
                ai_result[
                    "reasoning"
                ],

            "ai_recommended_action":
                ai_result[
                    "recommended_action"
                ],

            "requires_human_review":
                ai_result[
                    "requires_human_review"
                ],

            "ai_error":
                error,
        }

        new_results.append(
            result
        )

        # ----------------------------------------------------
        # Update queue state
        # ----------------------------------------------------

        queue.loc[
            queue["exception_id"]
            == exception_id,
            "ai_status"
        ] = status

        queue.loc[
            queue["exception_id"]
            == exception_id,
            "ai_attempts"
        ] += 1

        queue.loc[
            queue["exception_id"]
            == exception_id,
            "ai_result_available"
        ] = (
            status == "COMPLETED"
        )

        queue.loc[
            queue["exception_id"]
            == exception_id,
            "ai_error"
        ] = error

        # ----------------------------------------------------
        # Save queue immediately
        # ----------------------------------------------------

        queue.to_csv(
            QUEUE_FILE,
            index=False
        )

        # ----------------------------------------------------
        # Stop immediately on quota
        # ----------------------------------------------------

        if status == "RATE_LIMITED":

            print(
                "\nAI quota/rate limit reached."
            )

            print(
                "Stopping worker safely."
            )

            break

    # --------------------------------------------------------
    # Save AI results
    # --------------------------------------------------------

    if new_results:

        new_results_df = pd.DataFrame(
            new_results
        )

        if not existing_results.empty:

            combined = pd.concat(
                [
                    existing_results,
                    new_results_df
                ],
                ignore_index=True
            )

            # Keep latest result for each exception.
            combined = (
                combined
                .drop_duplicates(
                    subset=["exception_id"],
                    keep="last"
                )
            )

        else:

            combined = new_results_df

        os.makedirs(
            OUTPUT_DIR,
            exist_ok=True
        )

        combined.to_csv(
            OUTPUT_FILE,
            index=False
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("AI QUEUE WORKER SUMMARY")
    print("=" * 60)

    print("\nQueue status:")

    print(
        queue[
            "ai_status"
        ].value_counts()
    )

    print(
        f"\nQueue updated:\n"
        f"{QUEUE_FILE}"
    )

    print(
        f"\nAI results:\n"
        f"{OUTPUT_FILE}"
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    run_queue_worker()