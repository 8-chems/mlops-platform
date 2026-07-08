# MLOps Image Classification Platform

A production-style MLOps platform for training, tracking, registering, and
serving image classification models — built as a portfolio-grade reference
architecture for GCP.

##  Stack

- **Frontend**: React + TypeScript + MUI + React Query, Firebase Google Auth
- **Backend**: FastAPI + SQLAlchemy + Alembic, JWT sessions
- **ML**: TensorFlow/Keras (EfficientNet/ResNet/MobileNet transfer learning) + MLflow tracking
- **Infra**: Terraform (Cloud Run, Cloud SQL, GCS, Artifact Registry, Secret Manager, IAM)
- **CI/CD**: GitHub Actions → build/push Docker images → `terraform apply`

## Repository layout

```
backend/        FastAPI app (auth, dataset, training, prediction, admin, logs)
frontend/       React app (admin dashboard + client upload/predict UI)
terraform/      GCP infrastructure as code, modularized
.github/        CI/CD pipeline
docker-compose.yml   Local dev stack (Postgres + MLflow + backend + frontend)
```

## Local development

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
# Fill in Firebase project config in frontend/.env.local and add
# backend/firebase-service-account.json (Firebase Admin SDK service account key)

docker compose up --build
```

- Backend: http://localhost:8080/docs (Swagger UI)
- Frontend: http://localhost:5173
- MLflow UI: http://localhost:5000

The first user to log in with an email in `ADMIN_EMAIL_ALLOWLIST`
(`backend/app/auth/router.py`) becomes an admin; everyone else is a client.

## Typical workflow

1. **Admin**: create dataset classes and upload labeled images (`/admin/datasets`)
2. **Admin**: launch a training job with chosen architecture/hyperparameters (`/admin/training`)
3. Training runs in the background, logs params/metrics/artifacts to MLflow, and
   registers the resulting model in `model_registry` (staging by default)
4. **Admin**: promote the best model to `production` (`/admin/models`)
5. **Client**: upload an image and get a prediction from the current production model (`/client`)

## Deploying to GCP

Deployment is a **multi-step process**. Do not run `terraform apply` as the
first action — complete the prerequisites and GitHub secrets setup first.

**Full guide:** [`terraform/README.md`](terraform/README.md) (includes **PowerShell** commands for Windows)

### Deployment checklist (high level)

| Step | Action |
|------|--------|
| 1 | Install Terraform, gcloud, Docker |
| 2 | Create GCP project with `gcloud` + link billing (or use existing project) |
| 3 | Create GCS bucket for Terraform state |
| 4 | Edit `terraform/envs/staging.tfvars` (`project_id`) |
| 5 | Generate and save a JWT secret |
| 6 | First `terraform apply` (infra + placeholder images; APIs enabled automatically) |
| 7 | Set up Firebase (Google Sign-In, web app config, service account key) |
| 8 | Configure GitHub secrets + Workload Identity Federation (for CI/CD) |
| 9 | Build and push Docker images (manual or via push to `main`) |
| 10 | Second `terraform apply` with real `backend_image` / `frontend_image` |
| 11 | Run Alembic migrations against Cloud SQL |
| 12 | Verify app (login, admin flow, prediction) |

### GitHub secrets (CI/CD)

Add these in your repo: **Settings → Secrets and variables → Actions → New repository secret**.

Names must match exactly — the workflow reads them in `.github/workflows/ci-cd.yml`.

| Secret | Example / format | How to get it |
|--------|------------------|---------------|
| `GCP_PROJECT_ID` | `my-mlops-staging-123456` | GCP Console → project selector, or `gcloud config get-value project` |
| `TF_STATE_BUCKET` | `my-mlops-tf-state` | GCS bucket name you created in step 3 (no `gs://` prefix) |
| `JWT_SECRET` | `a1b2c3d4e5f6…` (64 hex chars) | Step 6: `$env:JWT_SECRET` in PowerShell, or `openssl rand -hex 32` in bash. **Must be the same value** used in manual `terraform apply` |
| `WIF_PROVIDER` | `projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider` | Created when setting up Workload Identity Federation (see terraform README step 9) |
| `WIF_SERVICE_ACCOUNT` | `github-actions@my-project.iam.gserviceaccount.com` | GCP service account email used by GitHub Actions for deploy |
| `VITE_FIREBASE_API_KEY` | `AIzaSy…` | Firebase Console → Project settings → Web app |
| `VITE_FIREBASE_AUTH_DOMAIN` | `PROJECT.firebaseapp.com` | Same |
| `VITE_FIREBASE_PROJECT_ID` | `my-mlops-staging-123456` | Same |
| `VITE_FIREBASE_APP_ID` | `1:946198550242:web:…` | Same |
| `BACKEND_CLOUD_RUN_URL` | `https://mlops-staging-backend-xxxxx-ew.a.run.app` | `terraform output -raw backend_url` after first apply — no trailing slash |

**When each secret is used**

- `GCP_PROJECT_ID` — Docker image paths and Terraform `project_id` context in CI
- `TF_STATE_BUCKET` — `terraform init -backend-config="bucket=…"`
- `JWT_SECRET` — passed to `terraform apply -var="jwt_secret=…"` (stored in Secret Manager)
- `WIF_PROVIDER` + `WIF_SERVICE_ACCOUNT` — keyless auth via `google-github-actions/auth` (push images + run Terraform)
- `VITE_FIREBASE_*` — baked into frontend static bundle at Docker build time
- `BACKEND_CLOUD_RUN_URL` — nginx proxies `/api/` to this URL in the frontend container

### Quick commands (after prerequisites)

**PowerShell (Windows):**

```powershell
cd terraform
terraform init -backend-config="bucket=my-mlops-tf-state"

terraform plan @(
  '-var-file=envs/staging.tfvars',
  "-var=jwt_secret=$($env:JWT_SECRET)"
)

terraform apply @(
  '-var-file=envs/staging.tfvars',
  "-var=jwt_secret=$($env:JWT_SECRET)"
)
```

## What's stubbed vs. production-ready

- **Production-ready**: FastAPI routing/auth/RBAC, SQLAlchemy models + Alembic
  migrations, Terraform modules, Docker images, CI/CD skeleton.
- **Simplified for portfolio use**: training runs synchronously in a FastAPI
  `BackgroundTasks` call rather than a real job queue (Celery is wired as a
  dependency and stubbed for use); training loads the full dataset into memory
  rather than a `tf.data` streaming pipeline; Vertex AI custom training jobs
  are stubbed in `app/training/vertex.py` as the recommended next step for
  real (large/GPU) workloads; MLflow is local-only (docker-compose) and not
  yet provisioned in Terraform for GCP; Grad-CAM, drift detection, A/B testing,
  and automatic retraining from the "nice advanced features" list are not
  implemented — the architecture (MLflow tracking, model registry with
  stage transitions) is designed to make adding them straightforward.
