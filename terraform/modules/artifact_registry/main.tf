variable "project_id" { type = string }
variable "region" { type = string }
variable "repo_id" { type = string }

resource "google_artifact_registry_repository" "repo" {
  project       = var.project_id
  location      = var.region
  repository_id = var.repo_id
  format        = "DOCKER"
  description   = "Docker images for the MLOps image classification platform"
}
