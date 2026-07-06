output "backend_url" {
  value = module.cloud_run_backend.service_url
}

output "frontend_url" {
  value = module.cloud_run_frontend.service_url
}

output "gcs_bucket" {
  value = module.storage.bucket_name
}

output "database_connection_name" {
  value = module.cloud_sql.connection_name
}

output "artifact_registry_repo" {
  value = module.artifact_registry.repository_id
}
