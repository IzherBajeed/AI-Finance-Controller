import os
import requests


# ============================================================
# Configuration
# ============================================================

SANDBOX_BASE_URL = os.getenv(
    "SANDBOX_BASE_URL",
    "http://127.0.0.1:5001"
).rstrip("/")

REQUEST_TIMEOUT = 10


# ============================================================
# Generic Request Helper
# ============================================================

def post_action(
    endpoint,
    payload
):

    url = (
        SANDBOX_BASE_URL
        + endpoint
    )

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        # Raise an exception for HTTP errors.
        response.raise_for_status()

        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json(),
            "error": ""
        }

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "status_code": None,
            "data": {},
            "error": (
                "Sandbox API request timed out."
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "success": False,
            "status_code": None,
            "data": {},
            "error": (
                "Could not connect to "
                "Finance Sandbox API."
            )
        }

    except requests.exceptions.HTTPError as error:

        try:
            data = response.json()
        except Exception:
            data = {}

        return {
            "success": False,
            "status_code": response.status_code,
            "data": data,
            "error": str(error)
        }

    except Exception as error:

        return {
            "success": False,
            "status_code": None,
            "data": {},
            "error": str(error)
        }


# ============================================================
# Verify Settlement
# ============================================================

def verify_settlement(
    exception_id
):

    return post_action(
        "/api/actions/verify-settlement",
        {
            "exception_id": exception_id
        }
    )


# ============================================================
# Investigate Duplicate
# ============================================================

def investigate_duplicate(
    exception_id
):

    return post_action(
        "/api/actions/investigate-duplicate",
        {
            "exception_id": exception_id
        }
    )


# ============================================================
# Determine Sandbox Action
# ============================================================

def execute_sandbox_action(
    action,
    exception_id
):

    action = str(
        action
    ).upper()

    # --------------------------------------------------------
    # Settlement verification
    # --------------------------------------------------------

    if action == "VERIFY_SETTLEMENT":

        return verify_settlement(
            exception_id
        )

    # --------------------------------------------------------
    # Duplicate investigation
    # --------------------------------------------------------

    if action == "INVESTIGATE_DUPLICATE":

        return investigate_duplicate(
            exception_id
        )

    # --------------------------------------------------------
    # Review-only actions
    # --------------------------------------------------------

    review_only_actions = {

        "REVIEW_SETTLEMENT_DIFFERENCE",

        "REVIEW_INVOICE_DIFFERENCE",

        "REVIEW_SETTLEMENT_DELAY",

        "MANUAL_FINANCIAL_REVIEW",

        "GENERAL_REVIEW",
    }

    if action in review_only_actions:

        return {
            "success": True,
            "status_code": 200,
            "data": {
                "environment": "sandbox",
                "action": action,
                "status": "REVIEW_ONLY",
                "message": (
                    "This action requires "
                    "financial review and does "
                    "not perform an automated "
                    "financial operation."
                )
            },
            "error": ""
        }

    # --------------------------------------------------------
    # Unknown action
    # --------------------------------------------------------

    return {
        "success": False,
        "status_code": 400,
        "data": {},
        "error": (
            f"Unsupported sandbox action: "
            f"{action}"
        )
    }


# ============================================================
# Health Check
# ============================================================

def check_sandbox_health():

    url = (
        SANDBOX_BASE_URL
        + "/api/health"
    )

    try:

        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json(),
            "error": ""
        }

    except Exception as error:

        return {
            "success": False,
            "status_code": None,
            "data": {},
            "error": str(error)
        }


# ============================================================
# Demo
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("SANDBOX CLIENT TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Health check
    # --------------------------------------------------------

    print("\nChecking sandbox health...")

    health = check_sandbox_health()

    print(
        f"Success: {health['success']}"
    )

    print(
        f"Status: {health['status_code']}"
    )

    print(
        f"Response: {health['data']}"
    )

    if not health["success"]:

        print(
            "\nSandbox is unavailable."
        )

        print(
            health["error"]
        )

        raise SystemExit(1)

    # --------------------------------------------------------
    # Test settlement verification
    # --------------------------------------------------------

    test_exception_id = (
        "EXC00001"
    )

    print(
        f"\nTesting settlement verification "
        f"for {test_exception_id}..."
    )

    result = verify_settlement(
        test_exception_id
    )

    print(
        f"Success: {result['success']}"
    )

    print(
        f"Status: {result['status_code']}"
    )

    print(
        f"Response: {result['data']}"
    )

    if result["error"]:

        print(
            f"Error: {result['error']}"
        )

    # --------------------------------------------------------
    # Test review-only action
    # --------------------------------------------------------

    print(
        "\nTesting review-only action..."
    )

    result = execute_sandbox_action(
        "REVIEW_INVOICE_DIFFERENCE",
        test_exception_id
    )

    print(
        f"Success: {result['success']}"
    )

    print(
        f"Response: {result['data']}"
    )

    # --------------------------------------------------------
    # Test duplicate investigation
    # --------------------------------------------------------

    print(
        "\nTesting duplicate investigation..."
    )

    result = execute_sandbox_action(
        "INVESTIGATE_DUPLICATE",
        "EXC00003"
    )

    print(
        f"Success: {result['success']}"
    )

    print(
        f"Status: {result['status_code']}"
    )

    print(
        f"Response: {result['data']}"
    )

    print("\n" + "=" * 60)
    print("SANDBOX CLIENT TEST COMPLETED")
    print("=" * 60)