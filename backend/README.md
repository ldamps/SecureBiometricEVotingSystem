# Secure Biometric E-Voting System – Backend //update needed//

FastAPI backend for the Secure Biometric Electronic Voting System.

## Setup

### 1. Create a virtual environment (recommended)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# or: venv\Scripts\activate   # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Database setup

1. **Create a PostgreSQL database** (e.g. `secure_evoting`) and note the connection details (user, password, host, port).

2. **Configure the connection**  
   Copy the example env file and set `DATABASE_URL`:
   ```bash
   cp example.env .env
   ```
   Edit `.env` and set:
   ```bash
   DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
   ```
   Example for a local DB named `secure_evoting`:
   ```bash
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/secure_evoting
   ```

3. **Create all tables** (run from the `backend` directory, with your venv activated):
   ```bash
   alembic upgrade head
   ```
   This applies the initial migration and creates every table (constituency, election, voter, address, ballot_token, vote, seat_allocation, tally_result, etc.). For later schema changes, add new migrations with `alembic revision --autogenerate -m "description"` then `alembic upgrade head`.

   **Note:** Use a virtual environment (`python3 -m venv venv` then `source venv/bin/activate`) and install dependencies with `pip install -r requirements.txt` so that `psycopg2-binary` and `alembic` are available.

### 4. Run the server

**Development (with auto-reload):**

```bash
uvicorn main:app --reload
```

Or from the project root:

```bash
cd backend && uvicorn main:app --reload
```

The API will be available at **http://localhost:8000**.

- **API root:** http://localhost:8000/
- **Health check:** http://localhost:8000/health
- **Interactive docs (Swagger):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Project layout

```
backend/
├── main.py           # FastAPI app and routes
├── requirements.txt
├── README.md
└── app/              # Optional: routers, models, services
    └── __init__.py
```

CORS is configured so the React frontend at `http://localhost:3000` can call this API.

## pgAdmin

1. Install PostgreSQL
2. Install pgAdmin
3. In pgAdmin, add a Server:
Right‑click Servers → Register → Server.
General tab: name it e.g. “Local” or “E-Voting”.
Connection tab:
Host: localhost
Port: 5432
Username: postgres (default superuser)
Password: the one you set during PostgreSQL install (or the default if you didn’t change it).
Save; pgAdmin will connect to PostgreSQL.
Create a database:
Right‑click the server → Create → Database.
Name it e.g. secure_evoting or evoting_db.
Owner: postgres (or a user you create).
Save.
(Optional but recommended) Create a user for the app:
Right‑click Login/Group Roles → Create → Login/Group Role.
General: name e.g. evoting_app.
Definition: set a password.
Privileges: enable “Can login”.
Then grant that role privileges on your database (e.g. right‑click the database → Properties → Security or use SQL to GRANT ALL ON DATABASE secure_evoting TO evoting_app;).