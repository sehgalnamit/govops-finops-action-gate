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

# Each catalog module directory is a self-contained Terraform root (its own
# parent resource group) so it can be `init`/`plan`-ed independently of the
# other catalog entries.
module "resource_group" {
  source  = "Azure/avm-res-resources-resourcegroup/azurerm"
  version = ">= 0.1.0"

  name     = "rg-govops-demo-vnet"
  location = "eastus"
  tags = {
    Environment = "GovOps-FinOps-Demo"
    ManagedBy   = "AgenticActionGate"
  }
}

module "avm_res_network_virtualnetwork" {
  source  = "Azure/avm-res-network-virtualnetwork/azurerm"
  version = ">= 0.1.0"

  name          = "vnet-govops-demo"
  location      = module.resource_group.location
  parent_id     = module.resource_group.resource_id
  address_space = ["10.10.0.0/16"]
}
