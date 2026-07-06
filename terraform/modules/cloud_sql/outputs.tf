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
