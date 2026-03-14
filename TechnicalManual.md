# Technical Manual

## Secure Biometric E-Voting System

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Repository Structure](#2-repository-structure)
3. [Docker Configuration](#3-docker-configuration)
4. [AWS EC2 Setup](#4-aws-ec2-setup)
5. [CI/CD Pipeline](#5-cicd-pipeline)
6. [Environment Variables & Secrets](#6-environment-variables--secrets)
7. [Resuming a Lab Session](#7-resuming-a-lab-session)

---

## 1. System Architecture

The system is deployed on **AWS Learner Lab** using the following containers, orchestrated with Docker Compose on a single EC2 instance:

| Container | Technology | Purpose |
|-----------|-----------|---------|
| `frontend` | React + Nginx | Serves the React SPA as static files; proxies `/api/` requests to the backend |
| `backend` | FastAPI + Uvicorn | Runs all backend API modules on port 8000 |
| `db` | PostgreSQL 16 | Persistent relational database |

AWS KMS is used for encryption/decryption operations. The backend container accesses KMS via the EC2 instance IAM role (LabRole) — no credentials are hardcoded.

---

## 2. Repository Structure

```
SecureBiometricEVotingSystem/
├── .github/
│   └── workflows/
│       ├── ci.yml           # Runs on every push/PR: lint, build, Docker build
│       └── deploy.yml       # Runs on push to main: SSH deploy to EC2
├── backend/
│   ├── app/                 # FastAPI application modules
│   ├── alembic/             # Database migrations
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/                 # React TypeScript source
│   ├── Dockerfile
│   ├── .dockerignore
│   └── nginx.conf           # Nginx config: static serving + API proxy
├── docker-compose.yml
└── .gitignore
```

---

## 3. Docker Configuration

### Backend Dockerfile (`backend/Dockerfile`)

Uses `python:3.12-slim`. Installs pip dependencies then copies application code. Runs Uvicorn on port 8000.

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile (`frontend/Dockerfile`)

Multi-stage build:
- **Stage 1** (`node:20-alpine`): Runs `npm ci && npm run build` to produce the static `build/` folder
- **Stage 2** (`nginx:alpine`): Copies the build output and serves it via Nginx

### Nginx Configuration (`frontend/nginx.conf`)

- Serves React static files
- Proxies all requests to `/api/` through to `http://backend:8000/` (Docker Compose internal DNS)
- SPA fallback: unknown routes serve `index.html` so React Router handles them

> **Important:** API calls in the React app must use relative paths (`/api/...`) not `http://localhost:8000`. Nginx handles the routing transparently.

### Docker Compose (`docker-compose.yml`)

Defines three services: `db`, `backend`, `frontend`. All have `restart: unless-stopped` so they automatically restart when the EC2 instance boots.

The `backend` service overrides `DATABASE_URL` to point to the `db` container hostname rather than `localhost`.

---

## 4. AWS EC2 Setup

This is a one-time manual setup. After this, all subsequent deploys are fully automated via GitHub Actions.

### 4.1 Launch EC2 Instance

1. In the AWS Learner Lab console, go to **EC2 → Launch Instance**
2. Configure as follows:

| Setting | Value |
|---------|-------|
| Name | `evoting-server` |
| AMI | Ubuntu Server 24.04 LTS |
| Instance type | `t3.medium` |
| Key pair | Create new → `evoting-key` → RSA → `.pem` → download and save |
| Auto-assign public IP | **Enable** |
| Storage | 20 GB gp3 |

3. **Security Group inbound rules:**

| Type | Port | Source |
|------|------|--------|
| SSH | 22 | Anywhere (0.0.0.0/0) |
| HTTP | 80 | Anywhere (0.0.0.0/0) |
| Custom TCP | 8000 | Anywhere (0.0.0.0/0) |

4. Launch the instance.

### 4.2 Allocate an Elastic IP (prevents IP changing between sessions)

1. EC2 → **Elastic IPs** → **Allocate Elastic IP address** → Allocate
2. Select the new IP → **Actions → Associate Elastic IP address**
3. Choose the `evoting-server` instance → **Associate**
4. Note the Elastic IP — this is your permanent server address

### 4.3 SSH into the Instance

```bash
chmod 600 evoting-key.pem
ssh -i evoting-key.pem ubuntu@YOUR_ELASTIC_IP
```

### 4.4 Install Docker

Run these commands on the EC2 instance:

```bash
# Add Docker's official repository
sudo apt-get update && sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list

# Install Docker and Git
sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin git

# Allow running Docker without sudo
sudo usermod -aG docker ubuntu && newgrp docker

# Verify
docker run hello-world
```

### 4.5 Clone the Repository

```bash
git config --global credential.helper store
git clone https://github.com/ldamps/SecureBiometricEVotingSystem.git
cd SecureBiometricEVotingSystem
```

> GitHub no longer accepts passwords. When prompted, enter your GitHub username and a **Personal Access Token** (not your password) as the password. Create one at: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → tick `repo` scope.

### 4.6 Fix IMDS Hop Limit for AWS KMS Access

By default, AWS only allows 1 network hop to the EC2 metadata service. Docker containers are 2 hops away, so without this fix the backend cannot access KMS via the IAM role. Run once:

```bash
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
aws ec2 modify-instance-metadata-options \
  --instance-id $INSTANCE_ID \
  --http-put-response-hop-limit 2 \
  --http-endpoint enabled \
  --region us-east-1
```

Verify KMS access works from inside a container:

```bash
docker run --rm amazon/aws-cli sts get-caller-identity
```

Expected output: a JSON object containing the `LabRole` ARN. If this succeeds, the backend will be able to call KMS without any hardcoded credentials.

---

## 5. CI/CD Pipeline

### How it works

```
Developer pushes code
        │
        ▼
  ci.yml runs (all branches)
  ├── Backend: pip install + import check
  ├── Frontend: npm ci + npm run build
  └── Docker: build both images
        │
        ▼ (only on push to main)
  deploy.yml runs
  ├── SSH into EC2
  ├── git pull origin main
  ├── Write backend/.env from GitHub Secrets
  ├── docker compose build --no-cache
  ├── docker compose up -d
  └── alembic upgrade head (run DB migrations)
```

### GitHub Actions Secrets Required

Go to: **GitHub repo → Settings → Secrets and variables → Actions**

| Secret | Description |
|--------|-------------|
| `EC2_HOST` | Elastic IP of the EC2 instance |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Full contents of `evoting-key.pem` (including `-----BEGIN/END-----` lines) |
| `DATABASE_URL` | `postgresql://evoting_app:PASSWORD@db:5432/evoting_db` |
| `POSTGRES_PASSWORD` | PostgreSQL password |

> AWS credentials are **not** stored in GitHub Secrets. The backend running on EC2 uses the instance IAM role (LabRole) automatically via the metadata service.

### Triggering a Deploy

- **Automatic:** push or merge to `main`
- **Manual:** GitHub → Actions → Deploy to EC2 → Run workflow (useful for testing from a feature branch)

---

## 6. Environment Variables & Secrets

### `backend/.env` (local development only — never commit)

On EC2, this file is written automatically by the deploy workflow from GitHub Secrets. AWS credentials are not included — the EC2 IAM role provides them.

### `.gitignore`

The `.gitignore` at the root excludes `.env`, `node_modules/`, `venv/`, and build artefacts. Verify the `.env` file is not tracked:

```bash
git check-ignore -v backend/.env
```

---

## 7. Resuming a Lab Session

When returning to the Learner Lab after a session has expired:

1. Click **Start Lab** and wait for it to turn green — do **not** click "End Lab" or "Reset"
2. Go to **EC2 → Instances → Start instance** (`evoting-server`)
3. The Elastic IP remains the same — no secret updates needed
4. If your home IP changed, update the SSH inbound rule: **Security Groups → Edit inbound rules → SSH → My IP**
5. Docker containers restart automatically (`restart: unless-stopped`)
6. Push a commit or manually trigger the deploy workflow to redeploy if needed
