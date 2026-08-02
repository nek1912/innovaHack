package agent.spend

import future.keywords.in

default allow = false
default requires_approval = false

allow {
    not frozen
    credit_available
    input.amount_paise <= input.per_tx_cap_paise
    (input.daily_spent_paise + input.amount_paise) <= input.daily_cap_paise
    input.payee_active
    not requires_approval
}

requires_approval {
    not frozen
    credit_available
    input.amount_paise <= input.per_tx_cap_paise
    (input.daily_spent_paise + input.amount_paise) <= input.daily_cap_paise
    input.payee_active
    input.amount_paise > input.approval_threshold_paise
}

frozen {
    input.agent_status == "frozen"
}

credit_available {
    input.credit.has_credit
    input.credit.status == "active"
    input.credit.available >= input.amount_paise
}

# Deny reasons (deterministic precedence)
deny_reason = "agent_frozen" { frozen }
deny_reason = "credit_not_issued" { not input.credit.has_credit }
deny_reason = "credit_inactive" { input.credit.has_credit; input.credit.status != "active" }
deny_reason = "per_tx_cap_exceeded" { not frozen; input.amount_paise > input.per_tx_cap_paise }
deny_reason = "daily_cap_exceeded" { not frozen; input.amount_paise <= input.per_tx_cap_paise; (input.daily_spent_paise + input.amount_paise) > input.daily_cap_paise }
deny_reason = "payee_inactive" { not frozen; input.amount_paise <= input.per_tx_cap_paise; (input.daily_spent_paise + input.amount_paise) <= input.daily_cap_paise; input.payee_active == false }
deny_reason = "credit_exhausted" { input.credit.has_credit; input.credit.status == "active"; input.credit.available < input.amount_paise }
