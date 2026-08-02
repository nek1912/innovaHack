package agent.spend

# --- allow ---

test_allow_under_caps_active_payee_not_frozen if {
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

test_deny_per_tx_cap_exceeded if {
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

test_deny_reason_per_tx_cap_exceeded if {
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

test_deny_daily_cap_exceeded if {
    not allow with input as {
        "amount_paise": 50000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 480000,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_deny_reason_daily_cap_exceeded if {
    deny_reason == "daily_cap_exceeded" with input as {
        "amount_paise": 50000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 480000,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

# --- deny: agent_frozen ---

test_deny_agent_frozen if {
    not allow with input as {
        "amount_paise": 1000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "frozen",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_deny_reason_agent_frozen if {
    deny_reason == "agent_frozen" with input as {
        "amount_paise": 1000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "frozen",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_frozen_overrides_approval_threshold if {
    not requires_approval with input as {
        "amount_paise": 80000,
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

test_deny_payee_inactive if {
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

test_deny_reason_payee_inactive if {
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

test_requires_approval_over_threshold if {
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

test_requires_approval_not_over_threshold if {
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

# --- edge: exact cap boundary ---

test_allow_exact_per_tx_cap if {
    allow with input as {
        "amount_paise": 100000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 100000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_allow_exact_daily_cap if {
    allow with input as {
        "amount_paise": 100000,
        "per_tx_cap_paise": 200000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 400000,
        "approval_threshold_paise": 100000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

# --- Part B: boundary +1 / -1 rupee ---

test_deny_one_paise_over_per_tx_cap if {
    not allow with input as {
        "amount_paise": 100001,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 100000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_deny_reason_one_paise_over_per_tx_cap if {
    deny_reason == "per_tx_cap_exceeded" with input as {
        "amount_paise": 100001,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 100000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_deny_one_paise_over_daily_cap if {
    not allow with input as {
        "amount_paise": 100000,
        "per_tx_cap_paise": 200000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 400001,
        "approval_threshold_paise": 100000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_deny_reason_one_paise_over_daily_cap if {
    deny_reason == "daily_cap_exceeded" with input as {
        "amount_paise": 100000,
        "per_tx_cap_paise": 200000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 400001,
        "approval_threshold_paise": 100000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

# --- Part B: approval threshold is strictly greater-than ---

test_not_requires_approval_exactly_at_threshold if {
    not requires_approval with input as {
        "amount_paise": 75000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_allow_exactly_at_threshold if {
    allow with input as {
        "amount_paise": 75000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_requires_approval_one_paise_over_threshold if {
    requires_approval with input as {
        "amount_paise": 75001,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_over_threshold_is_not_auto_allowed if {
    not allow with input as {
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

# --- Part B: deny_reason precedence ---

test_frozen_beats_per_tx_and_daily if {
    deny_reason == "agent_frozen" with input as {
        "amount_paise": 150000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 1000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "frozen",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_frozen_never_approval_or_allow if {
    not allow with input as {
        "amount_paise": 80000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "frozen",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
    not requires_approval with input as {
        "amount_paise": 80000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "frozen",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_per_tx_beats_daily_cap_reason if {
    deny_reason == "per_tx_cap_exceeded" with input as {
        "amount_paise": 150000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 1000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_per_tx_beats_payee_inactive_reason if {
    deny_reason == "per_tx_cap_exceeded" with input as {
        "amount_paise": 150000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": false,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

# --- Part B: approval vs deny precedence ---

test_over_threshold_and_over_per_tx_denies if {
    not requires_approval with input as {
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

test_over_threshold_and_over_per_tx_deny_reason if {
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

test_over_threshold_and_inactive_payee_denies if {
    not allow with input as {
        "amount_paise": 80000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": false,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
    not requires_approval with input as {
        "amount_paise": 80000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 0,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": false,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

test_over_threshold_daily_cap_denies if {
    not requires_approval with input as {
        "amount_paise": 80000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 450000,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
    deny_reason == "daily_cap_exceeded" with input as {
        "amount_paise": 80000,
        "per_tx_cap_paise": 100000,
        "daily_cap_paise": 500000,
        "daily_spent_paise": 450000,
        "approval_threshold_paise": 75000,
        "agent_status": "active",
        "payee_active": true,
        "credit": {"has_credit": true, "available": 500000, "reserved": 0, "status": "active"}
    }
}

# --- deny: credit_not_issued ---

test_credit_not_issued if {
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

test_credit_inactive if {
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

test_credit_exhausted if {
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

test_credit_available_allows if {
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

test_frozen_agent_denied_before_credit if {
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
