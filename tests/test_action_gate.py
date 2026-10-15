"""Pytest suite for the GovOps FinOps Action Gate."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _future_expiry(hours: int = 1) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _create_intent(
    provider: str,
    target_action: str,
    target_resource: str,
    max_budget_usd: float,
    allowed_region: str = "us-east-1",
) -> Dict[str, Any]:
    response = client.post(
        "/api/v1/intent/create",
        json={
            "user_id": "agent-007",
            "provider": provider,
            "target_action": target_action,
            "target_resource": target_resource,
            "max_budget_usd": max_budget_usd,
            "allowed_region": allowed_region,
            "expires_at": _future_expiry(),
        },
    )
    assert response.status_code == 200
    return response.json()


def test_successful_azure_avm_execution():
    """A deploy request within budget, in-region, and matching its bound intent executes."""
    intent = _create_intent(
        provider="azure_avm",
        target_action="deploy_resource",
        target_resource="rg-govops-demo-avm",
        max_budget_usd=500.0,
    )

    response = client.post(
        "/api/v1/action/execute",
        json={
            "intent_id": intent["intent_id"],
            "proof_of_intent_token": intent["proof_of_intent_token"],
            "provider": "azure_avm",
            "action": "deploy_resource",
            "resource": "rg-govops-demo-avm",
            "tf_variables": {"location": "eastus"},
            "requested_budget": 400.0,
            "region": "us-east-1",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "EXECUTED"
    assert body["policy_decision"] == "APPROVED"
    assert "terraform_execution" in body
    assert body["terraform_execution"]["status"] == "SUCCESS"


def test_budget_exceeded_veto():
    """An execution request exceeding the intent's bound budget ceiling is vetoed."""
    intent = _create_intent(
        provider="gcp_modules",
        target_action="deploy_resource",
        target_resource="govops-finops-demo-bucket",
        max_budget_usd=500.0,
    )

    response = client.post(
        "/api/v1/action/execute",
        json={
            "intent_id": intent["intent_id"],
            "proof_of_intent_token": intent["proof_of_intent_token"],
            "provider": "gcp_modules",
            "action": "deploy_resource",
            "resource": "govops-finops-demo-bucket",
            "tf_variables": {},
            "requested_budget": 5000.0,
            "region": "us-east-1",
        },
    )

    assert response.status_code == 403
    assert "budget" in response.json()["detail"].lower()


def test_cryptographic_mismatch_injection():
    """Swapping a deploy intent for a destroy action at execution time trips HA != HB."""
    intent = _create_intent(
        provider="azure_avm",
        target_action="deploy_resource",
        target_resource="rg-govops-demo-avm",
        max_budget_usd=500.0,
    )

    response = client.post(
        "/api/v1/action/execute",
        json={
            "intent_id": intent["intent_id"],
            "proof_of_intent_token": intent["proof_of_intent_token"],
            "provider": "azure_avm",
            "action": "destroy_resource",
            "resource": "rg-govops-demo-avm",
            "tf_variables": {},
            "requested_budget": 100.0,
            "region": "us-east-1",
        },
    )

    assert response.status_code == 403
    assert "HA != HB" in response.json()["detail"]


def test_catalog_lists_both_providers_and_real_modules():
    """GET /api/v1/catalog exposes the real AVM/CFT module sources, not just one each."""
    response = client.get("/api/v1/catalog")

    assert response.status_code == 200
    catalog = response.json()
    assert set(catalog["azure_avm"]) == {
        "resource_group",
        "virtual_network",
        "storage_account",
        "key_vault",
    }
    assert set(catalog["gcp_modules"]) == {
        "cloud_storage",
        "vpc_network",
        "cloud_sql_postgresql",
    }
    assert catalog["azure_avm"]["virtual_network"]["source"] == "Azure/avm-res-network-virtualnetwork/azurerm"
    assert catalog["gcp_modules"]["vpc_network"]["source"] == "terraform-google-modules/network/google"


def test_execute_with_explicit_module_key_targets_that_module():
    """An intent/execution pair can target a non-default catalog module (e.g. virtual_network)."""
    intent = _create_intent(
        provider="azure_avm",
        target_action="deploy_resource",
        target_resource="vnet-govops-demo",
        max_budget_usd=500.0,
    )
    # _create_intent doesn't expose module_key, so bind it directly here instead.
    intent_response = client.post(
        "/api/v1/intent/create",
        json={
            "user_id": "agent-007",
            "provider": "azure_avm",
            "target_action": "deploy_resource",
            "target_resource": "vnet-govops-demo",
            "max_budget_usd": 500.0,
            "allowed_region": "us-east-1",
            "expires_at": _future_expiry(),
            "module_key": "virtual_network",
        },
    )
    assert intent_response.status_code == 200
    intent = intent_response.json()

    response = client.post(
        "/api/v1/action/execute",
        json={
            "intent_id": intent["intent_id"],
            "proof_of_intent_token": intent["proof_of_intent_token"],
            "provider": "azure_avm",
            "action": "deploy_resource",
            "resource": "vnet-govops-demo",
            "tf_variables": {},
            "requested_budget": 400.0,
            "region": "us-east-1",
            "module_key": "virtual_network",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["terraform_execution"]["module_dir"].endswith("virtual_network")


def test_module_key_drift_is_vetoed():
    """An intent bound to one module cannot be used to execute against a different module."""
    intent = _create_intent(
        provider="azure_avm",
        target_action="deploy_resource",
        target_resource="rg-govops-demo-avm",
        max_budget_usd=500.0,
    )

    response = client.post(
        "/api/v1/action/execute",
        json={
            "intent_id": intent["intent_id"],
            "proof_of_intent_token": intent["proof_of_intent_token"],
            "provider": "azure_avm",
            "action": "deploy_resource",
            "resource": "rg-govops-demo-avm",
            "tf_variables": {},
            "requested_budget": 400.0,
            "region": "us-east-1",
            "module_key": "key_vault",
        },
    )

    assert response.status_code == 403
    assert "HA != HB" in response.json()["detail"]
