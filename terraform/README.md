# Terraform — MLOps Platform Infrastructure

Provisions the GCP footprint: Cloud Run (backend + frontend), Cloud SQL
(Postgres), GCS (dataset/model artifacts), Artifact Registry, Secret Manager,
and IAM bindings for a dedicated runtime service account.

## What Terraform does *not* provision

- **Firebase** — Google Sign-In, frontend config, backend service account key
- **Docker images** — built and pushed after Artifact Registry exists
- **Database schema** — Alembic migrations against Cloud SQL
- **MLflow** — runs locally via docker-compose; no GCP service yet

---

## Step-by-step deployment

> **Shell:** On Windows, use **PowerShell** (default terminal). `export` is bash-only —
> use `$env:NAME = "value"` instead. Linux/macOS/Git Bash commands are shown as
> **bash** where they differ.

### Step 1 — Install local tools

Install on your machine:

| Tool | Version | Purpose |
|------|---------|---------|
| [Terraform](https://developer.hashicorp.com/terraform/install) | ≥ 1.6 | Apply infrastructure |
| [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) | latest | `gcloud`, `gsutil` |
| [Docker](https://docs.docker.com/get-docker/) | latest | Build images (manual path) |

> **Cursor terminal can't find `terraform` or `gcloud`?** Windows CMD may see them
> but Cursor inherits PATH from when it was launched. After installing via WinGet:
> **fully quit and reopen Cursor**, or open a **new terminal** if
> `terminal.integrated.env.windows` was updated. Quick session fix (PowerShell):
> ```powershell
> $env:PATH = "C:\Users\bchems\AppData\Local\Microsoft\WinGet\Packages\Hashicorp.Terraform_Microsoft.Winget.Source_8wekyb3d8bbwe;C:\Users\bchems\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin;" + $env:PATH
> ```

You need a GCP **billing account** before step 3. List yours with
`gcloud billing accounts list` (requires an existing Google Cloud org or
personal billing setup).

### Step 2 — (Optional) Use an existing GCP project

Skip to step 4 if you already have a project with billing enabled. Note its
**project ID** for tfvars and GitHub secrets.

Or create a new project with `gcloud` in step 3.

### Step 3 — Authenticate gcloud and create the project

Pick a globally unique **project ID** (6–30 chars, lowercase letters, digits,
hyphens; e.g. `my-mlops-staging-123456`). This becomes `GCP_PROJECT_ID` in
GitHub secrets and `project_id` in tfvars.

**PowerShell (Windows):**

```powershell
# 1. Authenticate
gcloud auth login
gcloud auth application-default login

# 2. Set variables (customize PROJECT_ID)
$env:PROJECT_ID = "my-mlops-staging-123456"

# 3. Create the project
gcloud projects create $env:PROJECT_ID --name="MLOps Staging"

# 4. Link billing (required before Terraform can enable APIs / create resources)
$env:BILLING_ACCOUNT_ID = gcloud billing accounts list --format="value(name)" --limit=1
gcloud billing projects link $env:PROJECT_ID --billing-account=$env:BILLING_ACCOUNT_ID

# 5. Set as active project for subsequent commands
gcloud config set project $env:PROJECT_ID

# 6. Verify
gcloud config get-value project
```

**bash (Linux / macOS / Git Bash):**

```bash
# 1. Authenticate
gcloud auth login
gcloud auth application-default login

# 2. Set variables (customize PROJECT_ID)
export PROJECT_ID=my-mlops-staging-123456

# 3. Create the project
gcloud projects create $PROJECT_ID --name="MLOps Staging"

# 4. Link billing (required before Terraform can enable APIs / create resources)
export BILLING_ACCOUNT_ID=$(gcloud billing accounts list --format="value(name)" --limit=1)
gcloud billing projects link $PROJECT_ID --billing-account=$BILLING_ACCOUNT_ID

# 5. Set as active project for subsequent commands
gcloud config set project $PROJECT_ID

# 6. Verify
gcloud config get-value project
```

> **No variables?** You can skip `$env:PROJECT_ID` / `export` and paste the ID
> directly: `gcloud projects create my-mlops-staging-123456 --name="MLOps Staging"`

> **Console alternative:** [Google Cloud Console](https://console.cloud.google.com/)
> → New project → enable billing → use that project ID in tfvars and secrets.

### Step 4 — Create Terraform state bucket

One-time. Pick a globally unique bucket name (e.g. `my-mlops-tf-state`).

```bash
gsutil mb -l europe-west1 gs://YOUR-TF-STATE-BUCKET
gsutil versioning set on gs://YOUR-TF-STATE-BUCKET
```

Save the bucket name — it becomes the GitHub secret `TF_STATE_BUCKET`.

### Step 5 — Configure tfvars

Edit `envs/staging.tfvars`:

```hcl
project_id  = "YOUR_PROJECT_ID"   # replace placeholder
region      = "europe-west1"
environment = "staging"
db_tier     = "db-f1-micro"
```

For production, use `envs/production.tfvars` and set `environment = "production"`.

### Step 6 — Generate JWT secret

Generate **once**, store in a password manager, and reuse on every `terraform apply`.
The secret must be **64 hexadecimal characters** (32 random bytes).

**PowerShell (Windows):**

```powershell
# Cryptographically secure 32-byte hex string
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$env:JWT_SECRET = -join ($bytes | ForEach-Object { '{0:x2}' -f $_ })

# Save it — copy this output somewhere safe before closing the terminal
$env:JWT_SECRET
```

Reuse in later steps via `$env:JWT_SECRET` (same PowerShell session), or paste
the value into GitHub secret `JWT_SECRET` and terraform `-var="jwt_secret=..."`.

**bash (Linux / macOS / Git Bash):**

```bash
export JWT_SECRET=$(openssl rand -hex 32)
echo $JWT_SECRET
```

This value becomes:

- CLI: `-var="jwt_secret=$env:JWT_SECRET"` (PowerShell) or `-var="jwt_secret=$JWT_SECRET"` (bash)
- GitHub secret: `JWT_SECRET` (same value)

### Step 7 — First Terraform apply (bootstrap infra)

GCP APIs are enabled automatically by `modules/apis` — no manual
`gcloud services enable` needed.

APIs enabled in [`modules/apis/main.tf`](modules/apis/main.tf):

| API | Used by |
|-----|---------|
| `run.googleapis.com` | Cloud Run |
| `sqladmin.googleapis.com` | Cloud SQL |
| `storage.googleapis.com` | GCS |
| `artifactregistry.googleapis.com` | Docker registry |
| `secretmanager.googleapis.com` | JWT secret |
| `cloudbuild.googleapis.com` | Optional CI builds |
| `aiplatform.googleapis.com` | Vertex AI (stub) |
| `iam.googleapis.com` | Service accounts |
| `logging.googleapis.com` | Logging |
| `monitoring.googleapis.com` | Monitoring |

**PowerShell (Windows):**

```powershell
cd terraform
terraform init -backend-config="bucket=YOUR-TF-STATE-BUCKET"

terraform workspace new staging   # optional

# Re-set JWT if you opened a new terminal (step 6)
# $env:JWT_SECRET = "paste-your-64-char-hex-here"

# Recommended: array form — PowerShell won't mangle -var-file
terraform plan @(
  '-var-file=envs/staging.tfvars',
  "-var=jwt_secret=$($env:JWT_SECRET)"
)

terraform apply @(
  '-var-file=envs/staging.tfvars',
  "-var=jwt_secret=$($env:JWT_SECRET)"
)
```

> **Common mistakes on Windows**
> - Use `$env:JWT_SECRET`, **not** `$JWT_SECRET` (bash syntax)
> - Do **not** use `terraform -init` — use `terraform init`
> - If you still get *"Too many command line arguments"*, use the stop-parsing token:
>   ```powershell
>   terraform --% plan -var-file=envs/staging.tfvars -var=jwt_secret=PASTE_SECRET_HERE
>   ```

**bash:**

```bash
cd terraform
terraform init -backend-config="bucket=YOUR-TF-STATE-BUCKET"

terraform workspace new staging   # optional
terraform plan  -var-file=envs/staging.tfvars -var="jwt_secret=$JWT_SECRET"
terraform apply -var-file=envs/staging.tfvars -var="jwt_secret=$JWT_SECRET"
```

> Use the secret from step 6 (`$env:JWT_SECRET` or `$JWT_SECRET`), or paste the
> literal value if the variable is not set in your current shell.

**Troubleshooting `terraform init`**

| Error | Fix |
|-------|-----|
| Prints usage / help instead of initializing | Use `terraform init` (subcommand), **not** `terraform -init` |
| `Too many command line arguments` on `plan` | PowerShell parses `-var-file` as its own flag. Use the **array form**: `terraform plan @('-var-file=envs/staging.tfvars', "-var=jwt_secret=$($env:JWT_SECRET)")` |
| `bucket doesn't exist` / `project was not found` | ADC may point at a deleted project. Run: `gcloud auth application-default set-quota-project YOUR_PROJECT_ID` |
| Bucket not found | Create it in step 4 first: `gsutil mb -l europe-west1 gs://YOUR-TF-STATE-BUCKET` |

Cloud Run starts with placeholder images (`gcr.io/cloudrun/hello`) until step 10.

**How long does the first apply take?** This is normal — do not cancel.

| Resource | Typical duration |
|----------|------------------|
| GCP APIs (`modules/apis`) | ~30 seconds each |
| GCS, Secret Manager, Artifact Registry | ~1–3 minutes |
| **Cloud SQL Postgres** | **5–20 minutes** (longest step) |
| Cloud Run services | ~2–5 minutes |
| **Total first apply** | **~15–30 minutes** |

While running you will see `Still creating... [XXmXXs elapsed]` — that means
Terraform is waiting on Google Cloud, not stuck.

**If frontend fails with `Cloud Run Admin API ... disabled` (403):** the backend
often succeeds first while the API is still propagating. Re-run `terraform apply`
— only the frontend service will be created.

**After apply, save these outputs:**

```bash
terraform output backend_url
terraform output frontend_url
terraform output gcs_bucket
terraform output artifact_registry_repo
terraform output database_connection_name
```

### Step 8 — Link Firebase to your GCP project

Firebase powers **Google Sign-In** on the frontend and **token verification** on the backend.

#### 8a. Link Firebase to GCP

1. Open [Firebase Console](https://console.firebase.google.com/)
2. Click **Add project** (or **Add project** from the home screen)
3. Choose **Use an existing Google Cloud project**
4. Select `my-mlops-staging-123456` (your GCP project from step 3)
5. Finish the wizard (Google Analytics optional — you can disable it)

#### 8b. Enable Google Sign-In

1. Firebase Console → your project → **Build** → **Authentication**
2. Click **Get started** (if first time)
3. **Sign-in method** tab → **Google** → **Enable** → Save
4. Note the **Project support email** (your Google account)

#### 8c. Register the web app (frontend config)

1. Firebase Console → **Project settings** (gear icon) → **General**
2. Under **Your apps**, click **</> Web**
3. App nickname: `mlops-frontend` → **Register app**
4. Copy these values — you will add them as GitHub secrets:

| Firebase console field | GitHub secret name |
|------------------------|-------------------|
| apiKey | `VITE_FIREBASE_API_KEY` |
| authDomain | `VITE_FIREBASE_AUTH_DOMAIN` |
| projectId | `VITE_FIREBASE_PROJECT_ID` |
| appId | `VITE_FIREBASE_APP_ID` |

Example `authDomain`: `my-mlops-staging-123456.firebaseapp.com`

#### 8d. Backend service account key (local dev)

1. Firebase Console → **Project settings** → **Service accounts**
2. Click **Generate new private key** → download JSON
3. Save as `backend/firebase-service-account.json` (local dev only — file is gitignored)

> Cloud Run backend still needs this key wired via Secret Manager (not yet in Terraform).

#### 8e. Admin allowlist

Add your email in `backend/app/auth/router.py`:

```python
ADMIN_EMAIL_ALLOWLIST: set[str] = {"chemseddineberbague@gmail.com"}
```

#### 8f. Authorized domains (after first deploy)

Once Cloud Run URLs exist, add them in Firebase:

1. **Authentication** → **Settings** → **Authorized domains**
2. Add your frontend Cloud Run host, e.g. `mlops-staging-frontend-xxxxx-ew.a.run.app`

Get URLs after terraform apply:

```powershell
terraform output backend_url
terraform output frontend_url
```

### Step 9 — Configure GitHub secrets and Workload Identity Federation

CI/CD runs on push to `main` (`.github/workflows/ci-cd.yml`): tests → build/push
images → `terraform apply`.

#### 9a. Create a GCP service account for GitHub Actions

**PowerShell (Windows):**

```powershell
$env:PROJECT_ID = "YOUR_PROJECT_ID"
$env:GITHUB_ORG = "8-chems"
$env:GITHUB_REPO = "mlops-platform"

gcloud iam service-accounts create github-actions `
  --project=$env:PROJECT_ID `
  --display-name="GitHub Actions deploy"

$env:SA_EMAIL = "github-actions@$($env:PROJECT_ID).iam.gserviceaccount.com"
```

**bash:**

```bash
export PROJECT_ID=YOUR_PROJECT_ID
export GITHUB_ORG=your-github-username-or-org
export GITHUB_REPO=mlops-platform

gcloud iam service-accounts create github-actions \
  --project=$PROJECT_ID \
  --display-name="GitHub Actions deploy"

export SA_EMAIL=github-actions@${PROJECT_ID}.iam.gserviceaccount.com
```

Grant roles needed to push images, run Terraform, and manage Cloud Run:

**PowerShell (Windows):**

```powershell
$roles = @(
  "roles/run.admin",
  "roles/artifactregistry.admin",
  "roles/storage.admin",
  "roles/cloudsql.admin",
  "roles/secretmanager.admin",
  "roles/iam.serviceAccountAdmin",
  "roles/iam.serviceAccountUser",
  "roles/serviceusage.serviceUsageAdmin"
)
foreach ($ROLE in $roles) {
  gcloud projects add-iam-policy-binding $env:PROJECT_ID `
    --member="serviceAccount:$($env:SA_EMAIL)" `
    --role="$ROLE"
}
```

**bash:**

```bash
for ROLE in \
  roles/run.admin \
  roles/artifactregistry.admin \
  roles/storage.admin \
  roles/cloudsql.admin \
  roles/secretmanager.admin \
  roles/iam.serviceAccountAdmin \
  roles/iam.serviceAccountUser \
  roles/serviceusage.serviceUsageAdmin; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$ROLE"
done
```

> Tighten roles in production; the above is sufficient for staging bootstrap.

#### 9b. Create Workload Identity Pool + Provider

Set your GitHub owner and repo name first:

```powershell
$env:PROJECT_ID = "my-mlops-staging-123456"
$env:GITHUB_ORG = "8-chems"   # e.g. chemseddineberbague
$env:GITHUB_REPO = "mlops-platform"
$env:SA_EMAIL = "github-actions@$($env:PROJECT_ID).iam.gserviceaccount.com"
```

**PowerShell (Windows)** — use **single-line** commands (multiline paste often breaks `providers create-oidc`):

```powershell
# Skip if github-pool already exists ("already exists" error is OK)
gcloud iam workload-identity-pools create github-pool --project=$env:PROJECT_ID --location=global --display-name="GitHub Actions pool"

# Provider — attribute-condition is required by Google Cloud
gcloud iam workload-identity-pools providers create-oidc github-provider --project=$env:PROJECT_ID --location=global --workload-identity-pool=github-pool --display-name="GitHub provider" --issuer-uri="https://token.actions.githubusercontent.com" --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" --attribute-condition="assertion.repository_owner=='$($env:GITHUB_ORG)' && assertion.repository=='$($env:GITHUB_ORG)/$($env:GITHUB_REPO)'"

$PROJECT_NUMBER = gcloud projects describe $env:PROJECT_ID --format="value(projectNumber)"
gcloud iam service-accounts add-iam-policy-binding $env:SA_EMAIL --project=$env:PROJECT_ID --role="roles/iam.workloadIdentityUser" --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/$($env:GITHUB_ORG)/$($env:GITHUB_REPO)"
```

**bash:**

```bash
gcloud iam workload-identity-pools create github-pool \
  --project=$PROJECT_ID \
  --location=global \
  --display-name="GitHub Actions pool"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --project=$PROJECT_ID \
  --location=global \
  --workload-identity-pool=github-pool \
  --display-name="GitHub provider" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository_owner=='${GITHUB_ORG}' && assertion.repository=='${GITHUB_ORG}/${GITHUB_REPO}'"

gcloud iam service-accounts add-iam-policy-binding $SA_EMAIL \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}"
```

> **If you see `INVALID_ARGUMENT: attribute condition must reference provider's claims`:**
> the provider command was missing `--attribute-condition` and `repository_owner`
> in `--attribute-mapping`. Use the single-line command above.
>
> **If multiline paste breaks the command** (terminal shows `provider>>` instead of
> `providers create-oidc github-provider`), re-run as a **single line**.

Get the provider resource name for GitHub:

```powershell
# PowerShell or bash — same syntax
gcloud iam workload-identity-pools providers describe github-provider `
  --project=$env:PROJECT_ID `
  --location=global `
  --workload-identity-pool=github-pool `
  --format="value(name)"
```

Example output (this is `WIF_PROVIDER`):

```text
projects/123456789012/locations/global/workloadIdentityPools/github-pool/providers/github-provider
```

#### 9c. Add secrets to GitHub

In your repo: **Settings → Secrets and variables → Actions → New repository secret**.

**Infrastructure secrets (required for CI/CD auth + Terraform):**

| # | Secret name | Value | Notes |
|---|-------------|-------|-------|
| 1 | `GCP_PROJECT_ID` | `my-mlops-staging-123456` | Your GCP project ID (step 3) |
| 2 | `TF_STATE_BUCKET` | `my-mlops-tf-state` | Bucket from step 4 — **no** `gs://` prefix |
| 3 | `JWT_SECRET` | `a1b2c3…` (64 hex chars) | Same value from step 6 |
| 4 | `WIF_PROVIDER` | `projects/…/providers/github-provider` | Full resource name from 9b |
| 5 | `WIF_SERVICE_ACCOUNT` | `github-actions@PROJECT.iam.gserviceaccount.com` | Service account email from 9a |

**Frontend build secrets (required before step 10 Option A):**

| # | Secret name | Value | How to get it |
|---|-------------|-------|---------------|
| 6 | `VITE_FIREBASE_API_KEY` | `AIzaSy…` | Firebase Console → Project settings → Your apps → Web app config |
| 7 | `VITE_FIREBASE_AUTH_DOMAIN` | `PROJECT.firebaseapp.com` | Same screen |
| 8 | `VITE_FIREBASE_PROJECT_ID` | `my-mlops-staging-123456` | Same screen (usually = GCP project ID) |
| 9 | `VITE_FIREBASE_APP_ID` | `1:946198550242:web:…` | Same screen |
| 10 | `BACKEND_CLOUD_RUN_URL` | `https://mlops-staging-backend-xxxxx-ew.a.run.app` | After step 7 apply — **no trailing slash** |

Get the backend URL (PowerShell):

```powershell
cd terraform
terraform output -raw backend_url
```

Copy the full URL including `https://` into GitHub secret `BACKEND_CLOUD_RUN_URL`.

**Validation checklist**

- [ ] All 10 secret names match the table exactly (case-sensitive)
- [ ] `JWT_SECRET` is identical to what you passed in step 7
- [ ] `WIF_PROVIDER` is the full path, not just the provider ID
- [ ] `WIF_SERVICE_ACCOUNT` is an email ending in `.iam.gserviceaccount.com`
- [ ] WIF binding uses the correct `GITHUB_ORG/GITHUB_REPO` (repo owner + name)
- [ ] `BACKEND_CLOUD_RUN_URL` starts with `https://` and has **no** trailing `/`
- [ ] All 4 `VITE_FIREBASE_*` secrets are set before pushing to `main`

### Step 10 — Build and push Docker images

Artifact Registry repo `mlops-staging-repo` is created in step 7.

#### Option A — GitHub Actions (recommended)

**Prerequisites:** steps 7–9 complete, including all **10 GitHub secrets** (especially
`VITE_FIREBASE_*` and `BACKEND_CLOUD_RUN_URL`).

**Order of operations:**

```
Step 7  → first terraform apply (creates backend Cloud Run URL)
Step 8  → link Firebase, get VITE_* values
Step 9  → WIF + add all GitHub secrets (including BACKEND_CLOUD_RUN_URL)
Step 10 → push to main → CI builds images + terraform apply with real tags
```

1. Verify secrets in GitHub: **Settings → Secrets and variables → Actions**
   (you should see 10 repository secrets).
2. Commit and push to `main`:

   ```powershell
   git add .
   git commit -m "feat: wire Firebase and backend URL in CI"
   git push origin main
   ```

3. Watch the workflow: GitHub → **Actions** → **CI/CD**
   - `test-backend` + `test-frontend` run on every push/PR
   - `build-and-push` runs only on `main`: builds Docker images with Firebase
     config + backend URL, pushes to Artifact Registry, runs `terraform apply`

4. After success, verify:

   ```powershell
   terraform output frontend_url
   terraform output backend_url
   ```

5. Add the frontend Cloud Run domain to Firebase **Authorized domains** (step 8f).

**If CI fails with `409 already exists` + `403 Permission denied`:**

| Error | Cause | Fix |
|-------|-------|-----|
| `instanceAlreadyExists`, `already exists` | CI used **default** workspace; your local state is in **`staging`** | CI now runs `terraform workspace select staging` — push latest workflow |
| `artifactregistry.repositories.create` denied | `github-actions` has `writer` not `admin` | Grant `roles/artifactregistry.admin` (see below) |
| `iam.serviceAccounts.create` denied | missing `serviceAccountAdmin` | Grant `roles/iam.serviceAccountAdmin` (see below) |

Grant missing roles (PowerShell):

```powershell
$env:PROJECT_ID = "my-mlops-staging-123456"
$env:SA_EMAIL = "github-actions@$($env:PROJECT_ID).iam.gserviceaccount.com"
foreach ($ROLE in @("roles/artifactregistry.admin", "roles/iam.serviceAccountAdmin")) {
  gcloud projects add-iam-policy-binding $env:PROJECT_ID `
    --member="serviceAccount:$($env:SA_EMAIL)" `
    --role="$ROLE"
}
```

**What CI injects into the frontend image:**

| Build arg / env | GitHub secret |
|-----------------|---------------|
| `VITE_FIREBASE_API_KEY` | `VITE_FIREBASE_API_KEY` |
| `VITE_FIREBASE_AUTH_DOMAIN` | `VITE_FIREBASE_AUTH_DOMAIN` |
| `VITE_FIREBASE_PROJECT_ID` | `VITE_FIREBASE_PROJECT_ID` |
| `VITE_FIREBASE_APP_ID` | `VITE_FIREBASE_APP_ID` |
| `BACKEND_CLOUD_RUN_URL` (nginx `/api/` proxy) | `BACKEND_CLOUD_RUN_URL` |

#### Option B — Manual build

**PowerShell (Windows):**

```powershell
gcloud auth configure-docker europe-west1-docker.pkg.dev --quiet

# Backend
$IMAGE = "europe-west1-docker.pkg.dev/YOUR_PROJECT/mlops-staging-repo/backend:v1"
docker build -t $IMAGE ..\backend
docker push $IMAGE

# Frontend — pass Firebase + backend URL as build args
docker build -t europe-west1-docker.pkg.dev/YOUR_PROJECT/mlops-staging-repo/frontend:v1 `
  --build-arg VITE_FIREBASE_API_KEY="YOUR_KEY" `
  --build-arg VITE_FIREBASE_AUTH_DOMAIN="YOUR_PROJECT.firebaseapp.com" `
  --build-arg VITE_FIREBASE_PROJECT_ID="YOUR_PROJECT" `
  --build-arg VITE_FIREBASE_APP_ID="YOUR_APP_ID" `
  --build-arg BACKEND_CLOUD_RUN_URL="https://mlops-staging-backend-xxxxx-ew.a.run.app" `
  ..\frontend
docker push europe-west1-docker.pkg.dev/YOUR_PROJECT/mlops-staging-repo/frontend:v1
```

**bash:**

```bash
gcloud auth configure-docker europe-west1-docker.pkg.dev --quiet

# Backend
IMAGE=europe-west1-docker.pkg.dev/YOUR_PROJECT/mlops-staging-repo/backend:v1
docker build -t $IMAGE ../backend
docker push $IMAGE

# Frontend
docker build -t europe-west1-docker.pkg.dev/YOUR_PROJECT/mlops-staging-repo/frontend:v1 \
  --build-arg VITE_FIREBASE_API_KEY="YOUR_KEY" \
  --build-arg VITE_FIREBASE_AUTH_DOMAIN="YOUR_PROJECT.firebaseapp.com" \
  --build-arg VITE_FIREBASE_PROJECT_ID="YOUR_PROJECT" \
  --build-arg VITE_FIREBASE_APP_ID="YOUR_APP_ID" \
  --build-arg BACKEND_CLOUD_RUN_URL="https://mlops-staging-backend-xxxxx-ew.a.run.app" \
  ../frontend
docker push europe-west1-docker.pkg.dev/YOUR_PROJECT/mlops-staging-repo/frontend:v1
```

### Step 11 — Second Terraform apply (real images)

Use the **same** `jwt_secret` as step 7. Image tags from step 10 (or CI output).

```bash
terraform apply -var-file=envs/staging.tfvars \
  -var="jwt_secret=YOUR_JWT_SECRET" \
  -var="backend_image=europe-west1-docker.pkg.dev/YOUR_PROJECT/mlops-staging-repo/backend:v1" \
  -var="frontend_image=europe-west1-docker.pkg.dev/YOUR_PROJECT/mlops-staging-repo/frontend:v1"
```

**PowerShell (Windows):**

```powershell
terraform apply @(
  '-var-file=envs/staging.tfvars',
  "-var=jwt_secret=$($env:JWT_SECRET)",
  '-var=backend_image=europe-west1-docker.pkg.dev/YOUR_PROJECT/mlops-staging-repo/backend:v1',
  '-var=frontend_image=europe-west1-docker.pkg.dev/YOUR_PROJECT/mlops-staging-repo/frontend:v1'
)
```

If CI ran step 10, it already applied — skip unless you deploy manually.

### Step 12 — Run database migrations

Production does not auto-create tables (`environment != local`).

**PowerShell (Windows):**

```powershell
cd backend

# Connect via Cloud SQL Auth Proxy, then:
$env:DATABASE_URL = "postgresql://mlops:PASSWORD@127.0.0.1:5432/mlops"

alembic revision --autogenerate -m "initial"
alembic upgrade head
```

**bash:**

```bash
cd backend

# Connect via Cloud SQL Auth Proxy, then:
export DATABASE_URL="postgresql://mlops:PASSWORD@127.0.0.1:5432/mlops"

alembic revision --autogenerate -m "initial"
alembic upgrade head
```

> No files exist yet under `backend/alembic/versions/` — generate the initial
> revision first. DB password: retrieve from Terraform state / Cloud SQL console
> until Secret Manager wiring is complete.

### Step 13 — Verify deployment

1. Open `terraform output frontend_url` in a browser.
2. Sign in with Google (Firebase).
3. Confirm admin access if your email is in `ADMIN_EMAIL_ALLOWLIST`.
4. Backend health (PowerShell): `curl (terraform output -raw backend_url)/health`
5. Test admin dataset upload and client prediction flows.

---

## Module layout

| Module | Purpose |
|--------|---------|
| `modules/apis` | Enables GCP APIs via `google_project_service` |
| `modules/artifact_registry` | Docker image repository |
| `modules/storage` | GCS bucket (versioned, Nearline lifecycle) |
| `modules/cloud_sql` | Postgres instance, DB, user, password |
| `modules/secret_manager` | JWT signing secret |
| `modules/iam` | Cloud Run runtime SA + IAM bindings |
| `modules/cloud_run` | Cloud Run v2 (backend + frontend) |

---

## Known gaps / follow-ups

- **`DATABASE_URL` password** — `main.tf` uses `$(DB_PASSWORD)` placeholder; wire
  Cloud SQL password from Secret Manager before production.
- **Firebase on Cloud Run** — backend expects `firebase-service-account.json`;
  mount via Secret Manager or use ADC.
- **MLflow on GCP** — not provisioned; training metrics won't persist until added.
- **CORS** — set to `*` in Terraform; tighten to frontend URL in production.
- **Cloud SQL** — `deletion_protection = true`; disable before `terraform destroy`.
- **Cold starts** — set `min_instances = 1` on backend in production.
