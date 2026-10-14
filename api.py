"""
RefundShield AI - API Alias Entrypoint
Exposes the FastAPI application instance for uvicorn workers and external runners.
"""

from main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
