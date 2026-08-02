package agent.spend

# --- allow ---

test_allow_under_caps_active_payee_not_frozen {
    allow with input as {
        "amount_paise": 50000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 100000,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

# --- deny: per_tx_cap_exceeded ---

test_deny_per_tx_cap_exceeded {
    not allow with input as {
        "amount_paise": 150000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_deny_reason_per_tx_cap_exceeded {
    deny_reason == "per_tx_cap_exceeded" with input as {
        "amount_paise": 150000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

# --- deny: daily_cap_exceeded ---

test_deny_daily_cap_exceeded {
    not allow with input as {
        "amount_paise": 50000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 460000,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_deny_reason_daily_cap_exceeded {
    deny_reason == "daily_cap_exceeded" with input as {
        "amount_paise": 50000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 460000,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

# --- deny: agent_frozen ---

test_deny_agent_frozen {
    not allow with input as {
        "amount_paise": 50000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "frozen",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_deny_reason_agent_frozen {
    deny_reason == "agent_frozen" with input as {
        "amount_paise": 50000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "frozen",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

# --- deny: payee_inactive ---

test_deny_payee_inactive {
    not allow with input as {
        "amount_paise": 50000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": false,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_deny_reason_payee_inactive {
    deny_reason == "payee_inactive" with input as {
        "amount_paise": 50000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": false,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

# --- requires_approval ---

test_requires_approval_when_above_threshold {
    requires_approval with input as {
        "amount_paise": 80000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_not_requires_approval_when_below_threshold {
    not requires_approval with input as {
        "amount_paise": 50000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

# --- deny: credit_not_issued ---

test_deny_credit_not_issued {
    not allow with input as {
        "agent_status": "active",
        "per_tx_cap_paise": 10000,
        "daily_cap_paise": 50000,
        "daily_spent_paise": 0,
        "payee_active": true,
        "approval_threshold_paise": 5000,
        "amount_paise": 1000,
        "credit": {"has_credit": false, "available": 0, "reserved": 0, "status": "none"}
    }
}

test_deny_reason_credit_not_issued {
    deny_reason == "credit_not_issued" with input as {
        "agent_status": "active",
        "per_tx_cap_paise": 10000,
        "daily_cap_paise": 50000,
        "daily_spent_paise": 0,
        "payee_active": true,
        "approval_threshold_paise": 5000,
        "amount_paise": 1000,
        "credit": {"has_credit": false, "available": 0, "reserved": 0, "status": "none"}
    }
}

# --- deny: credit_inactive ---

test_deny_credit_inactive {
    not allow with input as {
        "agent_status": "active",
        "per_tx_cap_paise": 10000,
        "daily_cap_paise": 50000,
        "daily_spent_paise": 0,
        "payee_active": true,
        "approval_threshold_paise": 5000,
        "amount_paise": 1000,
        "credit": {"has_credit": true, "available": 5000, "reserved": 0, "status": "frozen"}
    }
}

test_deny_reason_credit_inactive {
    deny_reason == "credit_inactive" with input as {
        "agent_status": "active",
        "per_tx_cap_paise": 10000,
        "daily_cap_paise": 50000,
        "daily_spent_paise": 0,
        "payee_active": true,
        "approval_threshold_paise": 5000,
        "amount_paise": 1000,
        "credit": {"has_credit": true, "available": 5000, "reserved": 0, "status": "frozen"}
    }
}

# --- deny: credit_exhausted ---

test_deny_credit_exhausted {
    not allow with input as {
        "agent_status": "active",
        "per_tx_cap_paise": 10000,
        "daily_cap_paise": 50000,
        "daily_spent_paise": 0,
        "payee_active": true,
        "approval_threshold_paise": 5000,
        "amount_paise": 1000,
        "credit": {"has_credit": true, "available": 500, "reserved": 0, "status": "active"}
    }
}

test_deny_reason_credit_exhausted {
    deny_reason == "credit_exhausted" with input as {
        "agent_status": "active",
        "per_tx_cap_paise": 10000,
        "daily_cap_paise": 50000,
        "daily_spent_paise": 0,
        "payee_active": true,
        "approval_threshold_paise": 5000,
        "amount_paise": 1000,
        "credit": {"has_credit": true, "available": 500, "reserved": 0, "status": "active"}
    }
}

# --- allow: credit available ---

test_credit_available_allows {
    allow with input as {
        "agent_status": "active",
        "per_tx_cap_paise": 10000,
        "daily_cap_paise": 50000,
        "daily_spent_paise": 0,
        "payee_active": true,
        "approval_threshold_paise": 5000,
        "amount_paise": 1000,
        "credit": {"has_credit": true, "available": 5000, "reserved": 0, "status": "active"}
    }
}

# --- precedence: frozen beats credit ---

test_frozen_agent_denied_before_credit {
    not allow with input as {
        "agent_status": "frozen",
        "per_tx_cap_paise": 10000,
        "daily_cap_paise": 50000,
        "daily_spent_paise": 0,
        "payee_active": true,
        "approval_threshold_paise": 5000,
        "amount_paise": 1000,
        "credit": {"has_credit": true, "available": 5000, "reserved": 0, "status": "active"}
    }
}

test_frozen_agent_deny_reason {
    deny_reason == "agent_frozen" with input as {
        "agent_status": "frozen",
        "per_tx_cap_paise": 10000,
        "daily_cap_paise": 50000,
        "daily_spent_paise": 0,
        "payee_active": true,
        "approval_threshold_paise": 5000,
        "amount_paise": 1000,
        "credit": {"has_credit": true, "available": 5000, "reserved": 0, "status": "active"}
    }
}
