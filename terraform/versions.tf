terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.30"
    }
  }

  backend "gcs" {
    # bucket = "your-terraform-state-bucket"  # set via -backend-config or terraform init -backend-config
    prefix = "mlops-platform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
