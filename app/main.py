"""FastAPI service implementing the GovOps FinOps Action Gate.

American Express Intent Intelligence Framework + Cryptographic
Action-Binding (HA == HB) for gating agentic Terraform deployments
against Azure Verified Modules (AVM) and GCP Cloud Modules.
"""
from __future__ import annotations

import uuid
from datetime import timezone
from typing import Any, Dict

import jwt
from fastapi import FastAPI, HTTPException

from app.crypto_gate import CryptographicActionBinder
from app.models import ActionExecutionPayload, IntentCaptureRequest
from app.policy_engine import GovOpsPolicyEngine
from app.terraform_runner import TerraformExecutor

# Demo-only secret. In production this must come from a secrets manager
# (Azure Key Vault / GCP Secret Manager), never from source control.
JWT_SECRET = "enterprise-secure-intent-key-2026"
JWT_ALGORITHM = "HS256"

app = FastAPI(
    title="GovOps FinOps Action Gate",
    description=(
        "Agentic Infrastructure Governance microservice implementing the American "
        "Express Intent Intelligence Framework with Cryptographic Action-Binding "
        "(HA == HB) to govern Terraform deployments across Azure AVM and GCP modules."
    ),
    version="1.0.0",
)

# In-memory intent store for demo purposes. A production deployment would
# persist this in a durable store (e.g. Redis/Postgres) keyed by intent_id.
_INTENT_STORE: Dict[str, Dict[str, Any]] = {}


@app.post("/api/v1/intent/create")
def create_intent(request: IntentCaptureRequest) -> Dict[str, Any]:
    """Capture an agent's declared intent and issue a signed proof-of-intent token."""
    intent_id = f"intent_{uuid.uuid4().hex[:16]}"

    intent_constraints = {
        "intent_id": intent_id,
        "user_id": request.user_id,
        "provider": request.provider.value,
        "target_action": request.target_action,
        "target_resource": request.target_resource,
        "max_budget_usd": request.max_budget_usd,
        "allowed_region": request.allowed_region,
    }

    token_exp = request.expires_at
    if token_exp.tzinfo is None:
        token_exp = token_exp.replace(tzinfo=timezone.utc)

    token_payload = {**intent_constraints, "exp": token_exp}
    proof_of_intent_token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    _INTENT_STORE[intent_id] = intent_constraints

    return {
        "intent_id": intent_id,
        "proof_of_intent_token": proof_of_intent_token,
        "status": "CONFIRMED_AND_BOUND",
    }


@app.post("/api/v1/action/execute")
def execute_action(payload: ActionExecutionPayload) -> Dict[str, Any]:
    """Re-verify a proposed execution against its bound intent, then gate the Terraform run."""
    try:
        token_payload = jwt.decode(payload.proof_of_intent_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Proof-of-intent token has expired.")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=403, detail=f"Invalid proof-of-intent token: {exc}")

    if token_payload.get("intent_id") != payload.intent_id:
        raise HTTPException(
            status_code=403,
            detail="intent_id does not match the intent bound in the proof token.",
        )

    intent_constraints = _INTENT_STORE.get(payload.intent_id)
    if intent_constraints is None:
        raise HTTPException(status_code=404, detail=f"Unknown intent_id '{payload.intent_id}'.")

    # HA: footprint authorized at intent-capture time (from the signed token).
    h_a_payload = {
        "intent_id": token_payload["intent_id"],
        "provider": token_payload["provider"],
        "target_action": token_payload["target_action"],
        "target_resource": token_payload["target_resource"],
    }
    # HB: footprint of what is actually being requested for execution.
    h_b_payload = {
        "intent_id": payload.intent_id,
        "provider": payload.provider.value,
        "target_action": payload.action,
        "target_resource": payload.resource,
    }

    if not CryptographicActionBinder.verify_action_binding(h_a_payload, h_b_payload):
        raise HTTPException(
            status_code=403,
            detail=(
                "Cryptographic Action-Binding failure: HA != HB. The execution payload "
                "diverges from the authorized intent and has been vetoed."
            ),
        )

    execution_payload = {
        "requested_budget": payload.requested_budget,
        "region": payload.region,
        "action": payload.action,
    }
    approved, reason = GovOpsPolicyEngine.evaluate_constraints(intent_constraints, execution_payload)
    if not approved:
        raise HTTPException(status_code=403, detail=reason)

    terraform_result = TerraformExecutor.run_terraform_plan(payload.provider.value, payload.tf_variables)

    return {
        "status": "EXECUTED",
        "intent_id": payload.intent_id,
        "policy_decision": reason,
        "terraform_execution": terraform_result,
        "audit_log": {
            "intent_id": payload.intent_id,
            "user_id": intent_constraints["user_id"],
            "provider": payload.provider.value,
            "action": payload.action,
            "resource": payload.resource,
            "requested_budget": payload.requested_budget,
            "region": payload.region,
            "ha_eq_hb": True,
            "policy_decision": reason,
        },
    }
