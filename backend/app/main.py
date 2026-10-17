from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
from app.api.health import router as health_router
from app.api.documents import router as documents_router
from app.api.verification import router as verification_router
from app.api.risk import router as risk_router
from app.api.gis import router as gis_router
from app.api.dashboard import router as dashboard_router
from app.api.registry import router as registry_router
from app.database import engine, Base, SessionLocal
from app.config import settings
from app.seed import seed_demo_registry
from app.migrations import upgrade_document_evidence
import app.models  # noqa: F401

logger = logging.getLogger("landguard.main")

app = FastAPI(
    title="AI-Powered Land Record Validation and Fraud Detection System API",
    description="Backend service providing OCR document ingestion, NLP parsing, land record verification, anomaly detection, explainable risk scoring, and GIS spatial mapping.",
    version="1.0.0",
)

@app.on_event("startup")
def init_db_tables():
    """
    Ensure all application tables (document_records, verification_results,
    risk_assessments, land_records, ownership_history) exist in PostgreSQL.
    Leaves existing data and schemas fully intact.
    """
    Base.metadata.create_all(bind=engine)
    upgrade_document_evidence(engine)
    if settings.SEED_DEMO_DATA:
        with SessionLocal() as db:
            seed_demo_registry(db, settings.DATASET_DIR)
    logger.info("Database tables initialized successfully.")

# Enable CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(documents_router, prefix="/api/documents", tags=["Document Ingestion & OCR"])
app.include_router(verification_router, prefix="/api/verification", tags=["Land Verification & Anomaly Detection"])
app.include_router(risk_router, prefix="/api/risk", tags=["Explainable Risk Scoring Engine"])
app.include_router(gis_router, prefix="/api/gis", tags=["GIS Spatial Mapping & Parcels"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dataset & Dashboard"])
app.include_router(registry_router, prefix="/api/registry", tags=["Reference Registry"])


@app.get("/api")
def read_root():
    return {
        "system": "AI-Powered Land Record Validation and Fraud Detection System",
        "status": "online",
        "health_check": "/api/health",
        "ocr_upload": "/api/documents/upload",
        "verification": "/api/verification/verify/{document_id}",
        "risk_assessment": "/api/risk/assess/{document_id}",
        "gis_parcels": "/api/gis/parcels",
        "docs": "/docs",
    }


if settings.FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=settings.FRONTEND_DIST, html=True), name="frontend")
else:
    app.add_api_route("/", read_root)
