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
7. [Security Hardening](#7-security-hardening)
8. [Resuming a Lab Session](#8-resuming-a-lab-session)

---

## 1. System Architecture

The system is deployed on **AWS Learner Lab** using Docker Compose on a single EC2 instance. Services are isolated across two Docker networks:

```
Internet
   │
   ├── :80  (HTTP → HTTPS redirect)
   └── :443 (HTTPS)
         │
    ┌────▼──────────────────────────────── public network ──┐
    │  frontend (React + Nginx)                             │
    └────┬──────────────────────────────────────────────────┘
         │ /api/* proxy
    ┌────▼──────────────────────────────── internal network ─┐
    │  gateway (Nginx) ──► backend (FastAPI) ──► db (PG 16) │
    │                                                        │
    │  db-backup (cron pg_dump)                              │
    └────────────────────────────────────────────────────────┘
```

| Container | Technology | Network | Purpose |
|-----------|-----------|---------|---------|
| `frontend` | React + Nginx | public + internal | Serves the React SPA; terminates HTTPS; proxies `/api/` to the gateway |
| `gateway` | Nginx | internal only | Rate limiting, security headers, request validation |
| `backend` | FastAPI + Uvicorn | internal only | All backend API modules (port 8000, not exposed to host) |
| `db` | PostgreSQL 16 | internal only | Persistent relational database (not exposed to host) |
| `db-backup` | PostgreSQL client + cron | internal only | Automated daily database backups with retention policy |

**Key security properties:**
- Only the frontend container is reachable from the internet (ports 80/443)
- The gateway, backend, and database are on an **internal-only Docker network** with no external access
- All containers run with **resource limits** (CPU + memory) to prevent resource exhaustion
- The backend runs as a **non-root user** inside its container
- AWS KMS is used for encryption — the backend accesses KMS via the EC2 instance IAM role (LabRole) with no hardcoded credentials

---

## 2. Repository Structure

```
SecureBiometricEVotingSystem/
├── .github/
│   └── workflows/
│       ├── ci.yml              # Runs on every push/PR: lint, build, Docker build
│       └── deploy.yml          # Runs on push to main: SSH deploy to EC2
├── backend/
│   ├── app/                    # FastAPI application modules
│   ├── alembic/                # Database migrations
│   ├── Dockerfile              # Multi-stage build, non-root user
│   ├── .dockerignore
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/                    # React TypeScript source
│   ├── Dockerfile              # Multi-stage build (Node → Nginx + self-signed TLS)
│   ├── .dockerignore
│   └── nginx.conf              # HTTPS, SPA fallback, API proxy → gateway
├── gateway/
│   ├── Dockerfile              # Nginx-alpine reverse proxy
│   └── nginx.conf              # Rate limiting, security headers, upstream routing
├── scripts/
│   └── db-backup.sh            # Automated pg_dump with retention
├── docker-compose.yml          # Production: network-isolated services
├── docker-compose.dev.yml      # Dev overrides: exposes DB/gateway ports to host
└── .gitignore
```

---

## 3. Docker Configuration

### Backend Dockerfile (`backend/Dockerfile`)

Multi-stage build with security hardening:
- **Stage 1** (`deps`): Installs pip dependencies into a clean layer
- **Stage 2** (`production`): Copies only installed packages + application code, runs as non-root `appuser`

### Frontend Dockerfile (`frontend/Dockerfile`)

Multi-stage build:
- **Stage 1** (`node:20-alpine`): Runs `npm ci && npm run build` to produce the static `build/` folder
- **Stage 2** (`nginx:alpine`): Copies the build output, generates a self-signed TLS certificate, serves via Nginx

### Gateway (`gateway/`)

Nginx reverse proxy sitting between the frontend and backend:
- Per-IP rate limiting: 10 req/s general, 3 req/s auth, 2 req/s voting
- OWASP security headers on all proxied responses
- 5 MB request body size cap
- Hides upstream server identity

### Nginx Configuration (`frontend/nginx.conf`)

- HTTP → HTTPS redirect (port 80 → 443)
- Serves React static files with HSTS, CSP, and other security headers
- Proxies all requests to `/api/` through to the gateway (Docker internal DNS)
- SPA fallback: unknown routes serve `index.html` so React Router handles them

> **Important:** API calls in the React app must use relative paths (`/api/...`) not `http://localhost:8000`. Nginx handles the routing transparently.

### Docker Compose (`docker-compose.yml`)

Defines five services: `db`, `backend`, `gateway`, `frontend`, `db-backup`. All have `restart: unless-stopped` so they automatically restart when the EC2 instance boots.

**Network isolation:**
- `internal` network (bridge, `internal: true`): all services — no external access
- `public` network (bridge): frontend only — the sole entry point from the internet

**Resource limits:** Each service has CPU and memory limits to prevent resource exhaustion on the t3.medium instance.

**Health checks:** All services have Docker health checks. The backend checks its HTTP liveness endpoint; the gateway checks its health route; the frontend checks it can serve a page.

### Docker Compose Dev Override (`docker-compose.dev.yml`)

For local development, use both files to expose DB and gateway ports to the host:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

This exposes PostgreSQL on host port 5433 and the gateway on port 8080 for direct debugging.

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

| Type | Port | Source | Purpose |
|------|------|--------|---------|
| SSH | 22 | Your IP/32 | Admin access (restrict to your IP) |
| HTTP | 80 | 0.0.0.0/0 | Frontend (redirects to HTTPS) |
| HTTPS | 443 | 0.0.0.0/0 | Frontend (serves SPA + proxies API) |

> **Do NOT expose** ports 8000 (backend), 8080 (gateway), or 5432/5433 (database). These services are only accessible internally via Docker networks. Exposing them bypasses the gateway's rate limiting and security headers.

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
  ├── Docker: build all images (backend, frontend, gateway)
  └── Validate: docker compose config
        │
        ▼ (only on push to main)
  deploy.yml runs
  ├── SSH into EC2
  ├── git pull origin main
  ├── Write backend/.env from GitHub Secrets
  ├── docker compose build (incremental — uses layer cache)
  ├── docker compose up -d --remove-orphans (rolling restart)
  ├── alembic upgrade head (DB migrations)
  ├── Health check: frontend serving pages
  ├── Health check: backend readiness (DB connectivity)
  └── docker image prune (free disk space)
```

The deploy uses a **build-then-restart** strategy: new images are built while old containers still serve traffic. `docker compose up -d` then recreates only containers whose image changed, minimising downtime to seconds.

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

## 7. Security Hardening

This section documents the security measures applied to the deployment infrastructure.

### 7.1 Network Isolation

The Docker Compose configuration uses two networks:

- **`internal`** (`internal: true`): All services communicate here. The `internal: true` flag means Docker will not create any iptables rules allowing external traffic — even if a container binds a port, it is unreachable from outside.
- **`public`**: Only the frontend is attached. This is the sole ingress point from the internet.

This means an attacker who gains access to the host network cannot directly reach the database or backend — they must go through the frontend → gateway → backend proxy chain, where rate limiting and security headers are enforced.

### 7.2 Security Group (AWS)

The EC2 security group must only allow:

| Port | Protocol | Source | Service |
|------|----------|--------|---------|
| 22 | TCP | Your IP/32 | SSH (not 0.0.0.0/0) |
| 80 | TCP | 0.0.0.0/0 | Frontend HTTP → HTTPS redirect |
| 443 | TCP | 0.0.0.0/0 | Frontend HTTPS |

**Ports that must NOT be open:** 8000 (backend), 8080 (gateway), 5432/5433 (database). If these were previously open, remove them:

```bash
# Get security group ID
SG_ID=$(aws ec2 describe-instances \
  --instance-ids <INSTANCE_ID> \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text)

# Remove backend port
aws ec2 revoke-security-group-ingress \
  --group-id "$SG_ID" --protocol tcp --port 8000 --cidr 0.0.0.0/0

# Remove gateway port
aws ec2 revoke-security-group-ingress \
  --group-id "$SG_ID" --protocol tcp --port 8080 --cidr 0.0.0.0/0

# Restrict SSH to your IP
MY_IP=$(curl -s https://checkip.amazonaws.com)
aws ec2 revoke-security-group-ingress \
  --group-id "$SG_ID" --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" --protocol tcp --port 22 --cidr "${MY_IP}/32"
```

### 7.3 Container Hardening

- **Non-root execution:** The backend Dockerfile creates a dedicated `appuser` (UID 1000) and runs the application as that user. This limits the blast radius if the application is compromised.
- **Resource limits:** All containers have CPU and memory limits (`deploy.resources.limits`) to prevent a single service from exhausting the host.
- **Health checks:** Docker monitors every service. If a container becomes unhealthy, `restart: unless-stopped` triggers automatic recovery.
- **Read-only mounts:** The backup script is mounted read-only (`:ro`) into the backup container.

### 7.4 Rate Limiting (Gateway)

The Nginx gateway applies per-IP rate limits to prevent abuse:

| Endpoint | Rate | Burst | Purpose |
|----------|------|-------|---------|
| `/api/v1/auth/*` | 3 req/s | 5 | Brute-force protection on login |
| `/api/v1/voter/register` | 3 req/s | 5 | Registration abuse prevention |
| `/api/v1/voting/*` | 2 req/s | 3 | Vote submission rate control |
| `/api/*` (other) | 10 req/s | 20 | General API protection |

Excess requests receive HTTP 429 (Too Many Requests).

### 7.5 Database Backups

An automated backup service (`db-backup`) runs inside the Docker Compose stack:
- **Schedule:** Daily at 02:00 UTC via cron
- **Method:** `pg_dump` compressed with gzip
- **Retention:** 7 days (configurable via `BACKUP_RETENTION_DAYS`)
- **Storage:** Docker volume `db_backups`

To manually trigger a backup:

```bash
docker compose exec db-backup /usr/local/bin/db-backup.sh
```

To restore from a backup:

```bash
gunzip -c /path/to/evoting_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose exec -T db psql -U evoting_app -d evoting_db
```

### 7.6 Health Endpoints

| Endpoint | Purpose | Checks |
|----------|---------|--------|
| `GET /health` | Liveness | Process is running |
| `GET /api/v1/health` | Liveness (versioned) | Process + version info |
| `GET /api/v1/health/ready` | Readiness | Process + database connectivity |
| `GET /gateway/health` | Gateway liveness | Nginx is serving |

The deploy workflow verifies both frontend availability and backend readiness (DB connectivity) after every deployment. If the readiness check fails, the deploy is marked as failed in GitHub Actions.

---

## 8. Resuming a Lab Session

When returning to the Learner Lab after a session has expired:

1. Click **Start Lab** and wait for it to turn green — do **not** click "End Lab" or "Reset"
2. Go to **EC2 → Instances → Start instance** (`evoting-server`)
3. The Elastic IP remains the same — no secret updates needed
4. If your home IP changed, update the SSH inbound rule: **Security Groups → Edit inbound rules → SSH → My IP**
5. Docker containers restart automatically (`restart: unless-stopped`)
6. Push a commit or manually trigger the deploy workflow to redeploy if needed
