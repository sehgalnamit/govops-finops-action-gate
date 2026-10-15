"""Pydantic v2 schemas for the GovOps FinOps Action Gate."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel, Field


class InfrastructureProvider(str, Enum):
    """Supported Terraform module targets for gated deployments."""

    AZURE_AVM = "azure_avm"
    GCP_MODULES = "gcp_modules"


class IntentCaptureRequest(BaseModel):
    """What an agent declares it intends to do, and under what constraints."""

    user_id: str
    provider: InfrastructureProvider
    target_action: str
    target_resource: str
    max_budget_usd: float = Field(gt=0)
    allowed_region: str = "us-east-1"
    expires_at: datetime


class ActionExecutionPayload(BaseModel):
    """What the agent actually requests at execution time, re-verified against intent."""

    intent_id: str
    proof_of_intent_token: str
    provider: InfrastructureProvider
    action: str
    resource: str
    tf_variables: Dict[str, Any] = Field(default_factory=dict)
    requested_budget: float
    region: str
