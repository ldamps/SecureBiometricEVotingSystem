"""
FastAPI backend for Secure Biometric E-Voting System.
Run with: uvicorn main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Secure Biometric E-Voting System API",
    description="Backend API for the Secure Biometric Electronic Voting System",
    version="0.1.0",
)

# Allow React frontend (default CRA port) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Secure Biometric E-Voting System API", "docs": "/docs"}


@app.get("/health")
def health():
    """Health check for deployment and monitoring."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
