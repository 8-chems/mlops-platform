locals {
  name_prefix = "mlops-${var.environment}"
}

module "apis" {
  source  = "./modules/apis"
  project_id = var.project_id
}

module "artifact_registry" {
  source     = "./modules/artifact_registry"
  project_id = var.project_id
  region     = var.region
  repo_id    = "${local.name_prefix}-repo"
  depends_on = [module.apis]
}

module "storage" {
  source      = "./modules/storage"
  project_id  = var.project_id
  region      = var.region
  bucket_name = "${local.name_prefix}-artifacts-${var.project_id}"
  depends_on  = [module.apis]
}

module "secret_manager" {
  source     = "./modules/secret_manager"
  project_id = var.project_id
  secret_ids = toset(["jwt-secret-key"])
  secret_values = {
    jwt-secret-key = var.jwt_secret
  }
  depends_on = [module.apis]
}

module "cloud_sql" {
  source       = "./modules/cloud_sql"
  project_id   = var.project_id
  region       = var.region
  instance_name = "${local.name_prefix}-db"
  db_name      = var.db_name
  db_user      = var.db_user
  tier         = var.db_tier
  depends_on   = [module.apis]
}

module "iam" {
  source                = "./modules/iam"
  project_id            = var.project_id
  service_account_id    = "${local.name_prefix}-run-sa"
  gcs_bucket_name       = module.storage.bucket_name
  cloud_sql_instance_id = module.cloud_sql.instance_id
  secret_ids            = module.secret_manager.secret_ids
}

module "cloud_run_backend" {
  source          = "./modules/cloud_run"
  project_id      = var.project_id
  region          = var.region
  service_name    = "${local.name_prefix}-backend"
  image           = var.backend_image != "" ? var.backend_image : "gcr.io/cloudrun/hello"
  service_account = module.iam.service_account_email
  allow_unauthenticated = true
  env_vars = {
    ENVIRONMENT         = var.environment
    GCS_BUCKET_NAME     = module.storage.bucket_name
    GCP_PROJECT_ID      = var.project_id
    DATABASE_URL        = "postgresql://${var.db_user}:$(DB_PASSWORD)@/${var.db_name}?host=/cloudsql/${module.cloud_sql.connection_name}"
    CORS_ORIGINS        = "*"
  }
  secret_env_vars = {
    JWT_SECRET_KEY = module.secret_manager.secret_ids["jwt-secret-key"]
  }
  cloudsql_connection = module.cloud_sql.connection_name
  depends_on = [module.apis]
}

module "cloud_run_frontend" {
  source          = "./modules/cloud_run"
  project_id      = var.project_id
  region          = var.region
  service_name    = "${local.name_prefix}-frontend"
  image           = var.frontend_image != "" ? var.frontend_image : "gcr.io/cloudrun/hello"
  service_account = module.iam.service_account_email
  allow_unauthenticated = true
  env_vars        = {}
  secret_env_vars = {}
  depends_on      = [module.apis, module.cloud_run_backend]
}
