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

module "avm_res_resources_resourcegroup" {
  source  = "Azure/avm-res-resources-resourcegroup/azurerm"
  version = "0.1.1"

  name     = "rg-govops-demo-avm"
  location = "eastus"
  tags = {
    Environment = "GovOps-FinOps-Demo"
    ManagedBy   = "AgenticActionGate"
  }
}
