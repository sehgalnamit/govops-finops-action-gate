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

module "cloud_sql_postgresql" {
  source  = "terraform-google-modules/sql-db/google//modules/postgresql"
  version = ">= 1.0.0"

  project_id       = "govops-finops-project"
  name             = "govops-demo-postgresql"
  database_version = "POSTGRES_15"
  region           = "us-east1"
}
