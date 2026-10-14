"""
RefundShield AI - High-Performance Enterprise FastAPI Application
Production-grade asynchronous backend for E-Commerce Refund & Return Fraud Detection.
Features multi-layer machine learning inference, identity graph analytics, and automated DB migration.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import uvicorn

from database import seed_database_if_empty
from src.scoring.hybrid_engine import HybridFraudEngine
from src.graph.network_analyzer import IdentityNetworkAnalyzer
from src.api.routes import api_router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Context:
    1. Runs database auto-migration and seeds 10 benchmark datasets if empty.
    2. Pre-loads XGBoost ML models, Typology Classifier, and NetworkX Identity Graph
       into memory for sub-millisecond inference latency.
    """
    print("[Startup] Initializing RefundShield AI Enterprise Engine...")

    # 1. Database Auto-Migration & Seeding
    try:
        seed_database_if_empty()
    except Exception as e:
        print(f"[Startup Warning] Database seeder encounter: {e}")

    # 2. Pre-load Hybrid Scoring Engine
    hybrid_engine = HybridFraudEngine()
    app.state.hybrid_engine = hybrid_engine
    print(f"[Startup] Hybrid Engine loaded successfully (Model: {hybrid_engine.model_type})")

    # 3. Pre-load Identity Network Graph Analyzer
    network_analyzer = hybrid_engine.network_analyzer
    app.state.network_analyzer = network_analyzer
    print(f"[Startup] Network Graph loaded: {network_analyzer.graph.number_of_nodes()} entities, {network_analyzer.graph.number_of_edges()} relations")

    yield

    print("[Shutdown] Releasing RefundShield AI resources.")


app = FastAPI(
    title="RefundShield AI - Dynamic Fraud Detection Platform",
    description=(
        "Production-grade REST API & Investigation Command Center for E-Commerce Return & Refund Fraud Detection. "
        "Powered by XGBoost, Supervised Classification, Identity Syndicate Graphs, and Business Rules."
    ),
    version="2.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# -----------------------------------------------------------------------------
# Cross-Origin Resource Sharing (CORS) Configuration
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Custom Error Handlers (Graceful failure without crashes)
# -----------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Formats all standard HTTP exceptions into consistent JSON contract."""
    detail = exc.detail
    if isinstance(detail, dict):
        error_code = detail.get("error", "HTTP_EXCEPTION")
        message = detail.get("message", str(detail))
        details = detail.get("suggested_ids")
    else:
        error_code = "HTTP_EXCEPTION"
        message = str(detail)
        details = None

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": error_code,
            "message": message,
            "status_code": exc.status_code,
            "details": details
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats Pydantic validation errors cleanly for API consumers."""
    error_list = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err.get("loc", []) if loc != "body"])
        error_list.append({
            "field": field,
            "issue": err.get("msg", "Invalid input value"),
            "type": err.get("type", "value_error")
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request payload failed schema validation.",
            "status_code": 422,
            "details": error_list
        }
    )


# -----------------------------------------------------------------------------
# Static Assets & Core API Routes
# -----------------------------------------------------------------------------
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(api_router)


# -----------------------------------------------------------------------------
# Web UI Command Center Endpoints
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, tags=["Web Dashboard"], summary="Interactive Fraud Investigation Console")
@app.get("/dashboard", response_class=HTMLResponse, tags=["Web Dashboard"], summary="Interactive Fraud Investigation Console")
async def get_dashboard():
    """
    Renders the modern, dark glassmorphic investigation console.
    """
    index_file = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<h2>RefundShield AI Dashboard Template Not Found</h2>")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"\n========================================================")
    print(f"🛡️  RefundShield AI Dynamic Enterprise Platform Starting...")
    print(f"🌐  Console: http://127.0.0.1:{port}")
    print(f"⚡  Interactive Swagger API Docs: http://127.0.0.1:{port}/docs")
    print(f"========================================================\n")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
