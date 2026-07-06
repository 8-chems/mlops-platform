variable "project_id" { type = string }

variable "secret_ids" {
  description = "Set of secret IDs to create (non-sensitive; used as for_each keys)"
  type        = set(string)
}

variable "secret_values" {
  description = "Map of secret_id => initial value"
  type        = map(string)
  sensitive   = true
}

resource "google_secret_manager_secret" "secret" {
  for_each  = var.secret_ids
  project   = var.project_id
  secret_id = each.key

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "version" {
  for_each    = var.secret_ids
  secret      = google_secret_manager_secret.secret[each.key].id
  secret_data = var.secret_values[each.key]

  lifecycle {
    ignore_changes = [secret_data]
  }
}
