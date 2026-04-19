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
8. [Application Architecture](#8-application-architecture)
9. [Encryption Architecture](#9-encryption-architecture)
10. [Biometric Authentication](#10-biometric-authentication)
11. [External Integrations](#11-external-integrations)
12. [Testing](#12-testing)
13. [Database Seeding & Diagnostics](#13-database-seeding--diagnostics)
14. [Resuming a Lab Session](#14-resuming-a-lab-session)

---

## 1. System Architecture

The system is deployed on **AWS Learner Lab** using Docker Compose on a single EC2 instance. Services are isolated across two Docker networks:

```
Internet
   │
   ├── :80  (HTTP → HTTPS redirect + ACME challenge)
   └── :443 (HTTPS)
         │
    ┌────▼──────────────────────────── public network ──────┐
    │  frontend (React + Nginx)                             │
    │  backend  (FastAPI) ← outbound only (Stripe, email…) │
    │  certbot  (Let's Encrypt renewal)                     │
    └────┬──────────────────────────────────────────────────┘
         │ /api/* proxy
    ┌────▼──────────────────────────── internal network ────┐
    │  frontend ──► gateway (Nginx) ──► backend ──► db      │
    │                                                       │
    │  db-backup (cron pg_dump)                             │
    └───────────────────────────────────────────────────────┘
```

| Container | Technology | Network | Purpose |
|-----------|-----------|---------|---------|
| `frontend` | React + Nginx | public + internal | Serves the React SPA; terminates HTTPS (Let's Encrypt with self-signed fallback); proxies `/api/` to the gateway |
| `gateway` | Nginx | internal only | Rate limiting, security headers, request validation |
| `backend` | FastAPI + Uvicorn | internal + public | All backend API modules (port 8000, not exposed to host). On the public network for outbound calls (postcodes.io, Stripe, email) |
| `db` | PostgreSQL 16 | internal only | Persistent relational database (not exposed to host) |
| `db-backup` | PostgreSQL client + cron | internal only | Automated daily database backups with retention policy |
| `certbot` | certbot/certbot | public only | Automated Let's Encrypt certificate renewal (runs every 12 h) |

**Key security properties:**
- Only the frontend container accepts inbound traffic from the internet (ports 80/443)
- The backend is on the public network solely for **outbound** calls (Stripe, email, postcodes.io) — it does not expose any ports to the host
- The gateway and database are on an **internal-only Docker network** with no external access
- All containers run with **resource limits** (CPU + memory) to prevent resource exhaustion
- The backend runs as a **non-root user** inside its container
- Encryption uses a local key (via `ENCRYPTION_KEY` and `ENCRYPTION_HMAC_SECRET`), with optional AWS KMS support configured through `ENCRYPTION_PROVIDER`

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
│   ├── alembic.ini             # Alembic configuration
│   ├── Dockerfile              # Multi-stage build, non-root user
│   ├── .dockerignore
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/                    # React TypeScript source
│   ├── Dockerfile              # Multi-stage build (Node → Nginx)
│   ├── entrypoint.sh           # TLS entrypoint: uses Let's Encrypt certs or generates self-signed fallback
│   ├── .dockerignore
│   └── nginx.conf              # HTTPS, ACME challenge, SPA fallback, API proxy → gateway
├── gateway/
│   ├── Dockerfile              # Nginx-alpine reverse proxy
│   └── nginx.conf              # Rate limiting, security headers, upstream routing
├── scripts/
│   ├── db-backup.sh            # Automated pg_dump with retention
│   └── init-letsencrypt.sh     # Initial Let's Encrypt certificate provisioning
├── docker-compose.yml          # Production: network-isolated services
├── docker-compose.dev.yml      # Dev overrides: exposes DB/gateway ports to host
└── .gitignore
```

---

## 3. Docker Configuration

### Backend Dockerfile (`backend/Dockerfile`)

Multi-stage build with security hardening:
- **Stage 1** (`deps`): Installs pip dependencies into a clean layer
- **Stage 2** (`production`): Installs system dependencies (Tesseract OCR for document verification, poppler for PDF processing), copies only installed packages + application code, runs as non-root `appuser`

### Frontend Dockerfile (`frontend/Dockerfile`)

Multi-stage build:
- **Stage 1** (`node:20-alpine`): Runs `npm ci && npm run build` to produce the static `build/` folder
- **Stage 2** (`nginx:alpine`): Copies the build output, installs OpenSSL for fallback certificate generation, and uses `entrypoint.sh` to handle TLS

### Frontend TLS Entrypoint (`frontend/entrypoint.sh`)

At container startup, the entrypoint script:
1. Checks if Let's Encrypt certificates exist (from the shared `certbot_conf` volume)
2. If found, symlinks them into the Nginx SSL directory
3. If not found, generates a **self-signed fallback** certificate and starts a background watcher that switches to Let's Encrypt certs once certbot obtains them (reloading Nginx automatically)

### Gateway (`gateway/`)

Nginx reverse proxy sitting between the frontend and backend:
- Per-IP rate limiting: 10 req/s general, 3 req/s auth, 2 req/s voting
- OWASP security headers on all proxied responses
- 5 MB request body size cap
- Hides upstream server identity

### Nginx Configuration (`frontend/nginx.conf`)

- HTTP → HTTPS redirect (port 80 → 443)
- Serves the Let's Encrypt ACME HTTP-01 challenge at `/.well-known/acme-challenge/` (required for certificate issuance/renewal)
- Serves React static files with HSTS, CSP, and other security headers
- Proxies all requests to `/api/` through to the gateway (Docker internal DNS)
- SPA fallback: unknown routes serve `index.html` so React Router handles them

> **Important:** API calls in the React app must use relative paths (`/api/...`) not `http://localhost:8000`. Nginx handles the routing transparently.

### Certbot (`certbot`)

A `certbot/certbot` container that handles automated Let's Encrypt certificate renewal:
- Runs a renewal loop every 12 hours (`certbot renew --webroot`)
- Shares the `certbot_conf` volume (certificates) and `certbot_www` volume (ACME webroot) with the frontend
- On first deploy, the deploy workflow requests the initial certificate; certbot then handles renewals automatically

### Docker Compose (`docker-compose.yml`)

Defines six services: `db`, `backend`, `gateway`, `frontend`, `certbot`, `db-backup`. All have `restart: unless-stopped` so they automatically restart when the EC2 instance boots.

**Network isolation:**
- `internal` network (bridge, `internal: true`): db, backend, gateway, frontend, db-backup — no external access
- `public` network (bridge): frontend (inbound internet traffic), backend (outbound calls to external APIs), and certbot (Let's Encrypt ACME)

**Volumes:** `postgres_data` (database), `db_backups` (backup files), `certbot_conf` (Let's Encrypt certificates), `certbot_www` (ACME webroot)

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
  ├── Append AWS credentials from backend/aws.env (if present)
  ├── Export POSTGRES_PASSWORD, DOMAIN, CORS_ALLOWED_ORIGINS
  ├── docker compose down --rmi local (stop + remove old images)
  ├── docker compose build --no-cache (clean rebuild)
  ├── docker compose up -d --remove-orphans
  ├── alembic upgrade head (DB migrations)
  ├── Health check: frontend serving pages
  ├── Health check: backend readiness (DB connectivity)
  ├── docker image prune (free disk space)
  ├── Let's Encrypt: provision certificate if not already present
  └── Code version verification
```

The deploy uses a **full-rebuild** strategy: old containers are stopped and images removed (`docker compose down --rmi local`), then new images are built from scratch (`--no-cache`). This ensures a clean state on every deploy but causes brief downtime during the build.

### GitHub Actions Secrets Required

Go to: **GitHub repo → Settings → Secrets and variables → Actions**

| Secret | Description |
|--------|-------------|
| `EC2_HOST` | Elastic IP of the EC2 instance |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Full contents of `evoting-key.pem` (including `-----BEGIN/END-----` lines) |
| `DATABASE_URL` | `postgresql://evoting_app:PASSWORD@db:5432/evoting_db` |
| `POSTGRES_PASSWORD` | PostgreSQL password (also used by Docker Compose for the db service) |
| `ENCRYPTION_KEY` | Local encryption key for field-level encryption |
| `ENCRYPTION_HMAC_SECRET` | HMAC secret for integrity verification |
| `AWS_REGION` | AWS region (e.g. `us-east-1`) |
| `KMS_KEY_ID` | AWS KMS key identifier (used when `ENCRYPTION_PROVIDER=kms`) |
| `JWT_SECRET` | Secret key for signing JWT tokens |
| `JWT_ALGORITHM` | JWT signing algorithm (e.g. `HS256`) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry in minutes |
| `JWT_REFRESH_TOKEN_EXPIRE_MINUTES` | Refresh token expiry in minutes |
| `MAX_LOGIN_ATTEMPTS` | Maximum failed login attempts before lockout |
| `LOCKOUT_DURATION_MINUTES` | Account lockout duration in minutes |
| `RESEND_API_KEY` | API key for the Resend email service |
| `EMAIL_FROM` | Sender email address for transactional emails |
| `STRIPE_SECRET_KEY` | Stripe API secret key for payment processing |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `CERTBOT_EMAIL` | Email address for Let's Encrypt certificate registration |

> AWS credentials for KMS are **not** stored in GitHub Secrets. They are managed separately in `backend/aws.env` on the EC2 instance (rotated per lab session) and appended to the `.env` file during deploy.

### Triggering a Deploy

- **Automatic:** push or merge to `main`
- **Manual:** GitHub → Actions → Deploy to EC2 → Run workflow (useful for testing from a feature branch)

---

## 6. Environment Variables & Secrets

### `backend/.env` (never commit)

On EC2, this file is written automatically by the deploy workflow from GitHub Secrets. It contains all backend configuration: database URL, encryption keys, JWT settings, email/Stripe API keys, and login security settings (see the full list in the [GitHub Secrets table](#github-actions-secrets-required)).

AWS credentials are managed separately in `backend/aws.env` on the EC2 instance. This file is rotated per lab session and appended to `.env` during deploy. If `backend/aws.env` is missing, the deploy warns that KMS encryption will be unavailable.

### Docker Compose environment variables

The following variables can be set in a root `.env` file or exported before running `docker compose up`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `POSTGRES_USER` | `evoting_app` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `evoting_local_dev` | PostgreSQL password |
| `POSTGRES_DB` | `evoting_db` | PostgreSQL database name |
| `DOMAIN` | `localhost` | Domain for TLS certificates and CORS |
| `CORS_ALLOWED_ORIGINS` | (see docker-compose.yml) | Allowed CORS origins for the backend |

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

- **`internal`** (`internal: true`): All services except certbot communicate here. The `internal: true` flag means Docker will not create any iptables rules allowing external traffic — even if a container binds a port, it is unreachable from outside.
- **`public`**: The frontend (inbound traffic), backend (outbound API calls to Stripe, email, postcodes.io), and certbot (Let's Encrypt ACME). The backend does **not** expose any ports to the host — it is on the public network solely for outbound connectivity.

This means an attacker who gains access to the host network cannot directly reach the database or backend API — they must go through the frontend → gateway → backend proxy chain, where rate limiting and security headers are enforced. The gateway and database are strictly internal-only.

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
- **Read-only mounts:** The backup script and Let's Encrypt certificate volumes are mounted read-only (`:ro`) into their respective containers.
- **Gateway-required mode:** The backend enforces `REQUIRE_GATEWAY=true`, rejecting requests that don't arrive through the gateway proxy chain.

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

## 8. Application Architecture

### 8.1 Backend (FastAPI)

The backend follows a **layered architecture** with dependency injection:

```
Routes (app/application/api/v1/)
  │  Pydantic request/response schemas
  ▼
Services (app/service/)
  │  Business logic, validation, orchestration
  ▼
Repositories (app/repository/)
  │  SQLAlchemy ORM queries
  ▼
Database (PostgreSQL 16)
```

**API routers** (all mounted under `/api/v1/`):

| Router | Prefix | Purpose |
|--------|--------|---------|
| `health` | `/health` | Liveness and readiness probes |
| `auth_route` | `/auth` | Login, token refresh, password management |
| `voter_route` | `/voter` | Voter registration, identity verification, passport/address CRUD |
| `biometric_route` | `/biometric` | Device enrollment, challenge-response verification |
| `election_route` | `/election` | Election CRUD, results, seat allocations |
| `voting_route` | `/voting` | Cast votes and referendums |
| `party_route` | `/party` | Political party CRUD (admin-only) |
| `referendum_route` | `/referendum` | Referendum CRUD and results |
| `constituency_route` | `/constituency` | Read-only UK constituency lookup |
| `official_route` | `/official` | Election official management (admin-only) |
| `audit_route` | `/audit` | Audit log retrieval and privacy-safe reports |
| `investigation_route` | `/errors` | Error reporting and investigation tracking |
| `email_verification_route` | `/email-verification` | 6-digit code sending and verification |
| `kyc_route` | `/kyc` | Stripe Identity KYC verification sessions |

**Middleware stack** (outermost to innermost, defined in `main.py`):

1. **CORSMiddleware** — Preflight handling, allowed origins from config
2. **RequestContextMiddleware** — Assigns a unique `X-Request-ID` to every request
3. **RequestSecurityMiddleware** — Validates gateway origin (when `REQUIRE_GATEWAY=true`), enforces 5 MB body size limit
4. **SecurityHeadersMiddleware** — Defence-in-depth response headers
5. **RequestLoggerMiddleware** — Structured JSON logging of every request via structlog (method, path, status, duration)

**Global error handlers** map domain exceptions to HTTP status codes: `AuthenticationError` → 401, `AuthorizationError` → 403, `NotFoundError` → 404, `ValidationError` → 422, `BusinessLogicError` → 400.

**Electoral system support:** The backend supports multiple allocation methods — First Past the Post (FPTP), Additional Member System (AMS), Single Transferable Vote (STV), and Alternative Vote. Votes can carry ranked preferences (STV/AV) and party list votes (AMS regional top-up).

### 8.2 Frontend (React)

The frontend is a React TypeScript SPA with three user flows:

**Voter flow** (`/voter/*`):
- Registration with multi-step form and Stripe Identity KYC verification
- Biometric enrollment (face + ear recognition with liveness detection)
- Vote casting: election selection → identity verification → biometric check → ballot → confirmation
- Registration management (update address, name, nationality)
- 10-minute voting window after biometric verification

**Official flow** (`/official/*`, protected routes):
- Dashboard with election/referendum results and charts (Recharts)
- Election and referendum management (create, edit, open, close)
- Officials onboarding and management
- Audit log viewer and PDF audit report generation (jsPDF)
- Investigation tracking for reported errors

**Authenticator PWA** (`/auth/*`):
- Progressive Web App installable on mobile devices
- QR code scanner to link to the voting website
- Face recognition via face-api.js with TensorFlow
- Ear recognition for additional biometric modality
- Liveness detection (blink detection + head turn tracking)

**Key libraries:** React 19, React Router 7, Recharts (charts), face-api.js (biometrics), @stripe/stripe-js (KYC), jsPDF (PDF reports), qrcode.react (QR codes), jsqr (QR scanning).

---

## 9. Encryption Architecture

The system uses **field-level encryption** for all personally-identifiable information (names, national insurance numbers, passport details, addresses). No PII is stored in plaintext in the database.

### 9.1 Key Hierarchy

```
KEK (Key Encryption Key)
 │  AWS KMS key or local Fernet key
 │
 └──wraps──► DEK (Data Encryption Key)
              │  AES-256-GCM, stored encrypted in encryption_key table
              │
              └──encrypts──► Field data (stored as JSONB in PostgreSQL)
```

- **KEK** is never stored in the database. In production it is an AWS KMS key; in development it is a Fernet key from `ENCRYPTION_KEY`.
- **DEKs** are 256-bit keys generated per purpose. Only the KMS-wrapped (encrypted) form is stored in the database. Plain DEKs are decrypted on demand and cached in memory.
- **Three DEK purposes:** `DATABASE` (field encryption), `SEARCH` (HMAC blind indices), `STORAGE` (file/blob encryption).

### 9.2 Encryption Providers

Configured via `ENCRYPTION_PROVIDER` environment variable:

| Provider | Class | When to use | How it works |
|----------|-------|-------------|--------------|
| `local` | `LocalEncryption` | Development, testing | Fernet symmetric encryption using `ENCRYPTION_KEY` |
| `aws_kms` | `AWSKMSEncryption` | Production | Envelope encryption: KMS generates a unique AES-256-GCM data key per value. Wire format: `[4-byte key_len][encrypted_data_key][12-byte nonce][ciphertext]` |

Both providers generate **HMAC-SHA256 search tokens** for encrypted fields, enabling database queries (e.g. lookup voter by national insurance number) without decrypting every row.

### 9.3 DEK Rotation

DEK rotation is supported without re-encrypting existing data:
1. A new 256-bit key is generated and wrapped by the KEK
2. The previous DEK row is deactivated (`is_active=false`)
3. New writes use the current active DEK
4. Existing records store their `dek_version`, so the correct older DEK is fetched for decryption
5. This limits the blast radius of a compromised key to only data encrypted under that version

### 9.4 Encrypted Storage Format

Encrypted fields are stored as PostgreSQL JSONB columns (`EncryptedDBField`) containing:
- `ciphertext` — The encrypted value
- `search_token` — Deterministic HMAC-SHA256 blind index for queries
- `dek_version` — Which DEK version encrypted this value

---

## 10. Biometric Authentication

The system uses a **match-on-device** model — biometric templates (face and ear descriptors) never leave the user's mobile device. The server only stores a public key and verifies cryptographic signatures.

### 10.1 Flow

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  Mobile App  │         │   Backend    │         │  Database   │
│  (PWA)       │         │   (FastAPI)  │         │  (PG 16)    │
└──────┬───────┘         └──────┬───────┘         └──────┬──────┘
       │                        │                        │
  ENROLLMENT                    │                        │
       │  1. Generate ECDSA     │                        │
       │     P-256 key pair     │                        │
       │  2. Capture face+ear   │                        │
       │     descriptors        │                        │
       │  3. Store private key  │                        │
       │     + descriptors      │                        │
       │     on device          │                        │
       │                        │                        │
       │──POST /enroll─────────►│  4. Validate PEM key   │
       │  (public_key_pem,      │     is ECDSA P-256     │
       │   device_id,           │──store credential─────►│
       │   modalities)          │                        │
       │◄──credential_id────────│                        │
       │                        │                        │
  VERIFICATION                  │                        │
       │──POST /challenge──────►│  5. Generate 32-byte   │
       │  (voter_id)            │     random nonce       │
       │◄──challenge_hex────────│──store challenge──────►│
       │                        │     (5-min TTL)        │
       │  6. On-device biometric│                        │
       │     match (face+ear)   │                        │
       │  7. Sign challenge     │                        │
       │     with private key   │                        │
       │                        │                        │
       │──POST /verify─────────►│  8. Retrieve challenge │
       │  (challenge_id,        │     (not used, not     │
       │   signature,           │      expired)          │
       │   device_id)           │  9. Load voter's       │
       │                        │     public key         │
       │                        │ 10. Verify ECDSA       │
       │                        │     signature          │
       │                        │ 11. Mark challenge     │
       │◄──verified: true───────│     as used            │
```

### 10.2 Security Properties

- **No server-side biometric storage:** Face and ear descriptors are computed and stored only on the device. The server never sees raw biometric data.
- **ECDSA P-256 signatures:** The server stores only the public key. Verification proves the device holds the private key and the on-device biometric match succeeded.
- **Single-use challenges:** Each challenge nonce is marked as used after verification, preventing replay attacks. Challenges expire after 5 minutes.
- **Re-enrollment:** If a voter re-enrolls (e.g. new device), all previous credentials are deactivated first.
- **Liveness detection:** The mobile PWA performs blink detection and head turn tracking to prevent photo/video spoofing before signing the challenge.
- **Audit trail:** Enrollment and verification events are logged in the audit log.

---

## 11. External Integrations

### 11.1 Stripe Identity (KYC)

Used for voter identity verification during registration.

| Detail | Value |
|--------|-------|
| **Purpose** | Document upload (passport/driving licence), selfie, extraction of name, DOB, address |
| **Integration** | Backend creates a Stripe Identity verification session; frontend loads Stripe.js to present the UI |
| **Endpoints** | `POST /api/v1/kyc/session` (create), `GET /api/v1/kyc/session/{id}/verified-data` (retrieve results), `GET /api/v1/kyc/status` |
| **Secrets** | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` |
| **Frontend library** | `@stripe/stripe-js` |

### 11.2 Resend (Email)

Used for transactional emails throughout the voter and official lifecycle.

| Detail | Value |
|--------|-------|
| **Purpose** | Registration confirmations, email verification codes, vote confirmations, official welcome emails |
| **Integration** | `ResendEmailClient` in `app/infra/email/client.py` sends via Resend API with Jinja2 HTML templates |
| **Secrets** | `RESEND_API_KEY`, `EMAIL_FROM` |
| **Email types** | Registration confirmation, 6-digit verification code, vote receipt, official onboarding |

### 11.3 Postcodes.io (Address Lookup)

Used for UK postcode validation and constituency resolution.

| Detail | Value |
|--------|-------|
| **Purpose** | Look up a UK postcode to determine the voter's constituency (2025 parliamentary boundaries) and country |
| **Integration** | Async HTTP client in `app/infra/postcode/postcodes_io.py` — free API, no authentication required |
| **Used by** | `AddressService` during voter address creation/update |
| **Returns** | Constituency name, country (England/Scotland/Wales/Northern Ireland), county, region |

### 11.4 AWS KMS (Optional)

Used for production envelope encryption when `ENCRYPTION_PROVIDER=aws_kms`.

| Detail | Value |
|--------|-------|
| **Purpose** | Generate and manage data encryption keys (DEKs) via KMS key wrapping |
| **Integration** | `AWSKMSEncryption` in `app/infra/encryption/aws_kms.py` uses `boto3` KMS client |
| **Authentication** | IAM role via EC2 instance metadata (no hardcoded credentials). Requires IMDS hop limit of 2 for Docker containers (see [Section 4.6](#46-fix-imds-hop-limit-for-aws-kms-access)) |
| **Secrets** | `KMS_KEY_ID`, `AWS_REGION` (plus IAM credentials in `backend/aws.env` on EC2) |

---

## 12. Testing

### 12.1 Backend Test Suites (pytest)

Tests are in `backend/tests/` and use `pytest` with `asyncio_mode = auto` (configured in `pytest.ini`).

```bash
# Run all tests from the backend directory
cd backend
pip install -r requirements.txt   # includes pytest, pytest-asyncio
pytest

# Run a specific suite
pytest tests/unit/
pytest tests/integration/
pytest tests/security/
```

| Suite | Directory | What it covers |
|-------|-----------|---------------|
| **Unit** | `tests/unit/` | `test_auth_service.py` — login, lockout, token lifecycle; `test_encryption_service.py` — encrypt/decrypt round-trips; `test_biometric_service.py` — enrollment, challenge, verification; `test_election_and_voting_window.py` — election timing logic; `test_voting_service.py` — vote casting rules |
| **Integration** | `tests/integration/` | `test_auth_api.py` — FastAPI TestClient endpoint tests with database dependency mocks |
| **Security** | `tests/security/` | `test_security.py` — Security invariant tests: vote anonymity (no voter ID on vote records), one-voter-one-vote enforcement, ballot token single-use, JWT tamper detection, account lockout after failed attempts, encryption verification, biometric challenge replay prevention |

Test fixtures are defined in `tests/conftest.py` with factories for mock objects (`make_official`, `make_election`, `make_ballot_token`, `make_voter`, `mock_session`).

### 12.2 Load Testing (Locust)

Load tests simulate realistic traffic during a polling window using [Locust](https://locust.io/).

```bash
# Install locust
pip install locust

# Web UI (dashboard at http://localhost:8089)
locust -f tests/load/locustfile.py --host https://localhost

# Headless (no browser, exports CSV results)
locust -f tests/load/locustfile.py --host https://localhost \
       --headless -u 50 -r 5 -t 60s --csv tests/load/results/load_test
```

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `-u 50` | 50 concurrent users | Total simulated users |
| `-r 5` | 5 users/second | Spawn rate |
| `-t 60s` | 60 seconds | Test duration |

**User profiles:**
- **VoterUser** (70% weight): Health checks, browse elections/referendums/parties, view constituency info
- **OfficialUser** (30% weight): Login attempts, view elections, audit logs, deliberate failed logins

**Rate limit handling:** HTTP 429 responses from the gateway are counted as **successes**, not failures — they validate that Nginx rate limiting is working. Only 5xx errors and connection failures count as real failures.

---

## 13. Database Seeding & Diagnostics

### 13.1 Seed Scripts

Seed scripts in `backend/seeds/` populate the database with reference data and test data. Run them inside the backend container:

```bash
docker compose exec -T backend python -m seeds.<script_name>
```

| Script | Purpose |
|--------|---------|
| `seed_constituencies.py` | Load all 650 UK parliamentary constituencies from `uk_constituencies_2024.json` |
| `seed_production_elections.py` | Create election records for a working demo |
| `seed_electoral_systems_test.py` | Create elections of each type (FPTP, AMS, STV, AV) for testing |
| `seed_votes_test.py` | Generate test vote data |
| `seed_full_results_test.py` | Seed elections with votes and results for end-to-end result testing |
| `close_past_elections.py` | Administrative: close elections whose voting window has passed |

### 13.2 Diagnostic Script

`backend/diagnose.py` is a one-shot troubleshooting tool that validates the full registration flow inside the backend container:

```bash
docker compose exec -T backend python diagnose.py
```

It checks:
1. **Environment variables** — Verifies all required env vars are set (DATABASE_URL, encryption keys, JWT, Stripe, etc.)
2. **Database connectivity** — Confirms the backend can connect to PostgreSQL and the expected tables exist
3. **Encryption** — Tests that the configured provider (local Fernet or AWS KMS) can encrypt and decrypt a value
4. **Schema validation** — Verifies Pydantic schemas accept valid registration data
5. **Registration flow** — Attempts a full voter registration round-trip

This is useful for debugging deployment issues when the backend container starts but requests fail.

---

## 14. Resuming a Lab Session

When returning to the Learner Lab after a session has expired:

1. Click **Start Lab** and wait for it to turn green — do **not** click "End Lab" or "Reset"
2. Go to **EC2 → Instances → Start instance** (`evoting-server`)
3. The Elastic IP remains the same — no secret updates needed
4. If your home IP changed, update the SSH inbound rule: **Security Groups → Edit inbound rules → SSH → My IP**
5. Docker containers restart automatically (`restart: unless-stopped`)
6. Push a commit or manually trigger the deploy workflow to redeploy if needed
