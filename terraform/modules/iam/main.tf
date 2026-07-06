variable "project_id" { type = string }
variable "service_account_id" { type = string }
variable "gcs_bucket_name" { type = string }
variable "cloud_sql_instance_id" { type = string }
variable "secret_ids" {
  type = map(string)
}
variable "terraform_service_account_email" {
  description = "Email of the service account running Terraform (for Workload Identity Federation)"
  type        = string
}

resource "google_service_account" "run_sa" {
  project      = var.project_id
  account_id   = var.service_account_id
  display_name = "MLOps Platform Cloud Run runtime SA"
}

resource "google_project_iam_member" "cloud_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.run_sa.email}"
}

resource "google_storage_bucket_iam_member" "gcs_object_admin" {
  bucket = var.gcs_bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each  = var.secret_ids
  project   = var.project_id
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_sa.email}"
}

resource "google_project_iam_member" "aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.run_sa.email}"
}

resource "google_project_iam_member" "terraform_project_iam_admin" {
  project = var.project_id
  role    = "roles/resourcemanager.projectIamAdmin"
  member  = "serviceAccount:${var.terraform_service_account_email}"
}
