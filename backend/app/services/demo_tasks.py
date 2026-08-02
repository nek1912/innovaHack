DEMO_TASKS = {
    "buy_cloud_credits": {
        "id": "buy_cloud_credits",
        "name": "Buy Cloud Credits",
        "description": "Purchase additional cloud compute credits for model training.",
        "vendor": "AWS",
        "amount_paise": 10000,  # ₹100
        "expected_result": "approved",
        "scenario": "normal_approval",
    },
    "pay_api_subscription": {
        "id": "pay_api_subscription",
        "name": "Pay API Subscription",
        "description": "Pay monthly subscription for AI API access.",
        "vendor": "Anthropic",
        "amount_paise": 12000,  # ₹120
        "expected_result": "approved",
        "scenario": "normal_approval",
    },
    "purchase_dataset": {
        "id": "purchase_dataset",
        "name": "Purchase Dataset",
        "description": "Acquire training dataset for new model development.",
        "vendor": "Kaggle",
        "amount_paise": 15000,  # ₹150
        "expected_result": "approval_required",
        "scenario": "approval_required",
    },
    "rent_test_compute": {
        "id": "rent_test_compute",
        "name": "Rent Test Compute",
        "description": "Rent GPU compute for testing new model architecture.",
        "vendor": "AWS",
        "amount_paise": 10000,  # ₹100
        "expected_result": "approved",
        "scenario": "normal_approval",
    },
    "emergency_extra_request": {
        "id": "emergency_extra_request",
        "name": "Emergency Extra Request",
        "description": "Urgent need for additional compute resources.",
        "vendor": "Unknown",
        "amount_paise": 25000,  # ₹250
        "expected_result": "rejected",
        "scenario": "unknown_vendor",
    },
}


def get_task(task_id: str) -> dict:
    return DEMO_TASKS.get(task_id)


def list_tasks() -> list[dict]:
    return list(DEMO_TASKS.values())
