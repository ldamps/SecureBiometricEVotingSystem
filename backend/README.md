# Secure Biometric E-Voting System – Backend

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

### 3. Run the server

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
