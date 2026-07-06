output "instance_id" {
  value = google_sql_database_instance.instance.id
}

output "connection_name" {
  value = google_sql_database_instance.instance.connection_name
}

output "db_password" {
  value     = random_password.db_password.result
  sensitive = true
}

output "db_password_secret_id" {
  value = google_secret_manager_secret.db_password.id
}

output "db_password_secret_name" {
  value = google_secret_manager_secret.db_password.secret_id
}
