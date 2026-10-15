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

module "resource_group" {
  source  = "Azure/avm-res-resources-resourcegroup/azurerm"
  version = ">= 0.1.0"

  name     = "rg-govops-demo-storage"
  location = "eastus"
  tags = {
    Environment = "GovOps-FinOps-Demo"
    ManagedBy   = "AgenticActionGate"
  }
}

module "avm_res_storage_storageaccount" {
  source  = "Azure/avm-res-storage-storageaccount/azurerm"
  version = ">= 0.1.0"

  # Must match ^[a-z0-9]{3,24}$ - storage account names are globally unique.
  name      = "govopsdemosa001"
  location  = module.resource_group.location
  parent_id = module.resource_group.resource_id
}
