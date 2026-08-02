DEMO_TASKS = {
    "buy_gpu_compute": {
        "id": "buy_gpu_compute",
        "name": "Buy GPU Compute",
        "description": "Purchase additional cloud compute for AI model training. GPU inventory is low.",
        "vendor": "AWS",
        "amount_paise": 120000,
        "expected_result": "approved",
        "scenario": "normal_approval",
    },
    "purchase_dataset": {
        "id": "purchase_dataset",
        "name": "Purchase Dataset",
        "description": "Acquire training dataset from Kaggle for new model development.",
        "vendor": "Kaggle",
        "amount_paise": 350000,
        "expected_result": "approval_required",
        "scenario": "approval_required",
    },
    "purchase_hardware": {
        "id": "purchase_hardware",
        "name": "Purchase Hardware",
        "description": "Order specialized GPU hardware from an unapproved vendor.",
        "vendor": "Unknown",
        "amount_paise": 500000,
        "expected_result": "rejected",
        "scenario": "unknown_vendor",
    },
    "api_subscription": {
        "id": "api_subscription",
        "name": "API Subscription",
        "description": "Subscribe to Anthropic API for advanced AI capabilities.",
        "vendor": "Anthropic",
        "amount_paise": 60000,
        "expected_result": "approved",
        "scenario": "normal_approval",
    },
    "emergency_compute": {
        "id": "emergency_compute",
        "name": "Emergency Compute",
        "description": "Urgent need for additional compute resources for time-sensitive training.",
        "vendor": "AWS",
        "amount_paise": 1500000,
        "expected_result": "credit_exhausted",
        "scenario": "credit_exhausted",
    },
}


def get_task(task_id: str) -> dict:
    return DEMO_TASKS.get(task_id)


def list_tasks() -> list[dict]:
    return list(DEMO_TASKS.values())
