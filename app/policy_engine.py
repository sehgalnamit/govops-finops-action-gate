"""Deterministic FinOps/GovOps policy guardrails evaluated at execution time."""
from __future__ import annotations

from typing import Any, Dict, Tuple

# Keywords that mark an action as destructive/irreversible and therefore
# requiring explicit prior authorization at intent-capture time.
DESTRUCTIVE_KEYWORDS = ("destroy", "delete")


class GovOpsPolicyEngine:
    """Evaluates an execution request against the constraints bound at intent time."""

    @staticmethod
    def evaluate_constraints(
        intent_constraints: Dict[str, Any],
        execution_payload: Dict[str, Any],
    ) -> Tuple[bool, str]:
        requested_budget = execution_payload.get("requested_budget", 0.0)
        max_budget = intent_constraints.get("max_budget_usd", 0.0)
        if requested_budget > max_budget:
            return False, (
                f"VETO: requested_budget ${requested_budget:,.2f} exceeds "
                f"authorized max_budget_usd ${max_budget:,.2f}."
            )

        execution_region = execution_payload.get("region")
        allowed_region = intent_constraints.get("allowed_region")
        if execution_region != allowed_region:
            return False, (
                f"VETO: execution region '{execution_region}' does not match "
                f"authorized region '{allowed_region}'."
            )

        action = str(execution_payload.get("action", "")).lower()
        intent_action = str(intent_constraints.get("target_action", "")).lower()
        is_destructive = any(keyword in action for keyword in DESTRUCTIVE_KEYWORDS)
        intent_authorized_destructive = any(keyword in intent_action for keyword in DESTRUCTIVE_KEYWORDS)
        if is_destructive and not intent_authorized_destructive:
            return False, (
                f"VETO: action '{execution_payload.get('action')}' is destructive and was not "
                "explicitly authorized at intent capture time."
            )

        return True, "APPROVED"
