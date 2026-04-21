# Secure Biometric Electronic Voting System

A secure online voting platform for UK elections and referendums, with biometric voter authentication, field-level encryption of personal data, and a full audit trail.

The system supports the four electoral systems used across the United Kingdom — First Past the Post, Alternative Vote, Single Transferable Vote, and the Additional Member System — covering general elections, Scottish Parliament, Senedd, Northern Ireland Assembly, London Assembly, local councils, mayoral elections, and referendums.

---

## How it works, at a glance

- **Voters** register on a web portal, verify their identity through Stripe Identity (passport/driving licence + selfie + proof of address), and enrol their face and ear biometrics on a personal smartphone installed as a Progressive Web App.
- When voting, the voter scans a QR code on the voting website with their phone. The phone matches their biometrics locally and signs a challenge with an on-device private key. The server only ever sees a public key and a cryptographic signature — no biometric data ever leaves the phone.
- Once identity is verified, the voter has a **10-minute window** to mark and submit their ballot. A one-time ballot token is issued, used, and burned. Vote records are not linked to the voter's identity.
- **Election officials** create and manage elections and referendums from a separate protected interface, review live and final results, triage incident reports, and — as administrators — generate a formal PDF audit report at close.

---

## Documentation

| Guide | Audience | What it covers |
|-------|----------|----------------|
| [VoterGuide.md](VoterGuide.md) | Voters | Registration, installing the authenticator PWA, biometric enrolment, casting a vote, managing your registration, troubleshooting. |
| [OfficialGuide.md](OfficialGuide.md) | Election officials | First-time login, dashboard and results, creating and closing elections/referendums, investigations, audit reports, managing officials. |
| [TechnicalManual.md](TechnicalManual.md) | Engineers / operators | System architecture, Docker setup, AWS EC2 deployment, CI/CD, encryption architecture, biometric protocol, testing, seeding, operational runbooks. |

---

## Architecture

The system is deployed on AWS EC2 using Docker Compose. Six services sit across two Docker networks:

```
Internet
   │
   ├── :80  (HTTP → HTTPS redirect + ACME challenge)
   └── :443 (HTTPS)
         │
    ┌────▼────────────── public network ────────┐
    │  frontend (React + Nginx)                  │
    │  backend  (FastAPI, outbound only)         │
    │  certbot  (Let's Encrypt renewal)          │
    └────┬───────────────────────────────────────┘
         │ /api/* proxy
    ┌────▼────────────── internal network ──────┐
    │  frontend → gateway (Nginx) → backend → db │
    │  db-backup (daily pg_dump)                 │
    └────────────────────────────────────────────┘
```

| Container | Technology | Purpose |
|-----------|-----------|---------|
| `frontend` | React 19 + TypeScript + Nginx | SPA, HTTPS termination, API proxy |
| `gateway` | Nginx | Rate limiting, security headers, request validation |
| `backend` | FastAPI + Uvicorn | Layered REST API (routes → services → repositories) |
| `db` | PostgreSQL 16 | Relational store (internal network only) |
| `db-backup` | PostgreSQL client + cron | Daily compressed backups with retention |
| `certbot` | certbot/certbot | Automated Let's Encrypt certificate renewal |

The backend exposes no ports to the host; the database and gateway are on an internal-only Docker network. Only the frontend accepts inbound traffic from the internet.

See [TechnicalManual.md](TechnicalManual.md#1-system-architecture) for the full architecture.

---

## Security properties

- **Field-level encryption.** All PII (name, NI number, passport details, address) is encrypted per-field using envelope encryption with a KEK / DEK hierarchy. Production uses AWS KMS; development uses local Fernet keys. HMAC-SHA256 blind indices allow equality searches without decryption. See [TechnicalManual.md §9](TechnicalManual.md#9-encryption-architecture).
- **Match-on-device biometrics.** Face and ear descriptors never leave the voter's phone. The server stores only an ECDSA P-256 public key and verifies signatures over single-use challenges. Liveness detection (blink + head turn) runs on-device. See [TechnicalManual.md §10](TechnicalManual.md#10-biometric-authentication).
- **Vote anonymity.** Vote records contain no voter identifier. A separate ballot-token table tracks who voted without recording how.
- **Single-use ballot tokens.** Each token is consumed on submission; replay is impossible.
- **Rate limiting.** The Nginx gateway applies per-IP rate limits on auth, registration, and voting endpoints.
- **Network isolation.** The `internal` Docker network has `internal: true`, preventing any external traffic from reaching the backend, gateway, or database directly.
- **Non-root containers**, **resource limits**, **health checks**, and **read-only volume mounts** throughout.
- **Audit log.** Every official action and every system-relevant event is recorded and surfaced in the end-of-election PDF audit report.

---

## Technology

**Backend** — Python 3, FastAPI, SQLAlchemy, Alembic, PostgreSQL 16, structlog, pytest, Locust.
**Frontend** — React 19, TypeScript, React Router 7, Recharts, face-api.js / TensorFlow.js, @stripe/stripe-js, jsPDF, qrcode.react, jsqr.
**Infrastructure** — Docker, Docker Compose, Nginx, Let's Encrypt (certbot), AWS EC2, AWS KMS, GitHub Actions.
**External services** — Stripe Identity (KYC), Resend (transactional email), postcodes.io (UK postcode → constituency lookup).

---

## Local development

```bash
# Bring up the full stack with dev overrides (exposes DB on :5433, gateway on :8080)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Run backend tests
cd backend
pip install -r requirements.txt
pytest

# Run the frontend in isolation
cd frontend
npm ci
npm start
```

See [TechnicalManual.md §3](TechnicalManual.md#3-docker-configuration) for the full Docker configuration and [§13](TechnicalManual.md#13-database-seeding--diagnostics) for seed scripts and diagnostics.

---

## Repository layout

```
SecureBiometricEVotingSystem/
├── backend/              FastAPI application, Alembic migrations, tests, seeds
├── frontend/             React SPA + authenticator PWA
├── gateway/              Nginx reverse proxy (rate limiting + headers)
├── scripts/              db-backup and Let's Encrypt provisioning scripts
├── docker-compose.yml    Production compose file (network-isolated)
├── docker-compose.dev.yml Dev overrides (ports exposed to host)
├── VoterGuide.md         End-user guide for voters
├── OfficialGuide.md      End-user guide for election officials
└── TechnicalManual.md    Operator and developer reference
```
