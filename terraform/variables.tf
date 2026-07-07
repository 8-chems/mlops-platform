variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-west1"
}

variable "environment" {
  description = "Deployment environment (staging/production)"
  type        = string
  default     = "staging"
}

variable "db_tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_name" {
  type    = string
  default = "mlops"
}

variable "db_user" {
  type    = string
  default = "mlops"
}

variable "backend_image" {
  description = "Full Artifact Registry image path for backend, e.g. europe-west1-docker.pkg.dev/PROJECT/mlops/backend:tag"
  type        = string
  default     = ""
}

variable "frontend_image" {
  description = "Full Artifact Registry image path for frontend"
  type        = string
  default     = ""
}

variable "jwt_secret" {
  description = "Secret used to sign platform JWTs"
  type        = string
  sensitive   = true
}

variable "terraform_service_account_email" {
  description = "Email of the service account running Terraform (for Workload Identity Federation)"
  type        = string
}

variable "firebase_credentials" {
  description = "Firebase service account credentials JSON"
  type        = string
  sensitive   = true
  default     = ""
}

variable "firebase_credentials_base64" {
  description = "Firebase service account credentials JSON (base64 encoded)"
  type        = string
  sensitive   = true
  default     = ""
}
