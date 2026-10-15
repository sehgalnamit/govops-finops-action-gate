"""Catalog of real Azure Verified Modules (AVM) and GCP Cloud Foundation
Toolkit (CFT) modules the GovOps gate can plan against.

Adding a new gated resource type is a config change here plus a new
Terraform root directory under `terraform/<provider>/<dir_name>/` - no
changes to the FastAPI app, crypto-binding, or policy engine are needed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class ModuleCatalogEntry:
    dir_name: str
    source: str
    version: str
    description: str


MODULE_CATALOG: Dict[str, Dict[str, ModuleCatalogEntry]] = {
    "azure_avm": {
        "resource_group": ModuleCatalogEntry(
            dir_name="resource_group",
            source="Azure/avm-res-resources-resourcegroup/azurerm",
            version="0.1.1",
            description="Azure Verified Module: Resource Group.",
        ),
        "virtual_network": ModuleCatalogEntry(
            dir_name="virtual_network",
            source="Azure/avm-res-network-virtualnetwork/azurerm",
            version=">= 0.1.0",
            description="Azure Verified Module: Virtual Network, subnets and peerings.",
        ),
        "storage_account": ModuleCatalogEntry(
            dir_name="storage_account",
            source="Azure/avm-res-storage-storageaccount/azurerm",
            version=">= 0.1.0",
            description="Azure Verified Module: Storage Account.",
        ),
        "key_vault": ModuleCatalogEntry(
            dir_name="key_vault",
            source="Azure/avm-res-keyvault-vault/azurerm",
            version=">= 0.1.0",
            description="Azure Verified Module: Key Vault.",
        ),
    },
    "gcp_modules": {
        "cloud_storage": ModuleCatalogEntry(
            dir_name="cloud_storage",
            source="terraform-google-modules/cloud-storage/google",
            version="~> 6.0",
            description="GCP Cloud Foundation Toolkit module: Cloud Storage bucket.",
        ),
        "vpc_network": ModuleCatalogEntry(
            dir_name="vpc_network",
            source="terraform-google-modules/network/google",
            version=">= 1.0.0",
            description="GCP Cloud Foundation Toolkit module: VPC network and subnets.",
        ),
        "cloud_sql_postgresql": ModuleCatalogEntry(
            dir_name="cloud_sql_postgresql",
            source="terraform-google-modules/sql-db/google//modules/postgresql",
            version=">= 1.0.0",
            description="GCP Cloud Foundation Toolkit module: Cloud SQL for PostgreSQL.",
        ),
    },
}

# The module used when an intent/execution request doesn't specify a
# module_key explicitly - keeps the simplest single-resource demo flow
# backward compatible.
DEFAULT_MODULE_KEY: Dict[str, str] = {
    "azure_avm": "resource_group",
    "gcp_modules": "cloud_storage",
}


def resolve_module_key(provider: str, module_key: Optional[str]) -> str:
    """Resolve a requested module_key, falling back to the provider's default."""
    return module_key or DEFAULT_MODULE_KEY[provider]


def get_catalog_entry(provider: str, module_key: str) -> ModuleCatalogEntry:
    """Look up a catalog entry, raising KeyError with a helpful message if unknown."""
    try:
        return MODULE_CATALOG[provider][module_key]
    except KeyError as exc:
        available = list(MODULE_CATALOG.get(provider, {}))
        raise KeyError(
            f"Unknown module_key '{module_key}' for provider '{provider}'. Available: {available}"
        ) from exc
