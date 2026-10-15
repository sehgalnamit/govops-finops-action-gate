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

module "gcp_storage_bucket" {
  source  = "terraform-google-modules/cloud-storage/google"
  version = "~> 6.0"

  name       = "govops-finops-demo-bucket"
  project_id = "govops-finops-project"
  location   = "us-east1"
}
