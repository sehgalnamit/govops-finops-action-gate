terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = "govops-finops-project"
  region  = "us-east1"
}

module "vpc_network" {
  source  = "terraform-google-modules/network/google"
  version = ">= 1.0.0"

  project_id   = "govops-finops-project"
  network_name = "vpc-govops-demo"

  subnets = [
    {
      subnet_name   = "subnet-govops-demo"
      subnet_ip     = "10.20.0.0/24"
      subnet_region = "us-east1"
    }
  ]
}
