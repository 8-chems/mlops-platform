variable "project_id" { type = string }
variable "region" { type = string }
variable "instance_name" { type = string }
variable "db_name" { type = string }
variable "db_user" { type = string }
variable "tier" { type = string }

resource "random_password" "db_password" {
  length  = 20
  special = false
}

resource "google_sql_database_instance" "instance" {
  project          = var.project_id
  name             = var.instance_name
  region           = var.region
  database_version = "POSTGRES_15"

  settings {
    tier = var.tier
    backup_configuration {
      enabled    = true
      start_time = "02:00"
    }
    ip_configuration {
      ipv4_enabled = true
    }
  }

  deletion_protection = true
}

resource "google_sql_database" "database" {
  project  = var.project_id
  name     = var.db_name
  instance = google_sql_database_instance.instance.name
}

resource "google_sql_user" "user" {
  project  = var.project_id
  name     = var.db_user
  instance = google_sql_database_instance.instance.name
  password = random_password.db_password.result
}

resource "google_secret_manager_secret" "db_password" {
  project   = var.project_id
  secret_id = "${var.instance_name}-db-password"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result

  lifecycle {
    ignore_changes = [secret_data]
  }
}
