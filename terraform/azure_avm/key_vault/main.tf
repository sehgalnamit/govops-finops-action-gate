terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_client_config" "current" {}

module "resource_group" {
  source  = "Azure/avm-res-resources-resourcegroup/azurerm"
  version = ">= 0.1.0"

  name     = "rg-govops-demo-kv"
  location = "eastus"
  tags = {
    Environment = "GovOps-FinOps-Demo"
    ManagedBy   = "AgenticActionGate"
  }
}

module "avm_res_keyvault_vault" {
  source  = "Azure/avm-res-keyvault-vault/azurerm"
  version = ">= 0.1.0"

  name      = "kv-govops-demo"
  location  = module.resource_group.location
  parent_id = module.resource_group.resource_id
  tenant_id = data.azurerm_client_config.current.tenant_id
}
