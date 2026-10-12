from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.api.documents import router as documents_router
from app.api.verification import router as verification_router
from app.api.risk import router as risk_router
from app.api.gis import router as gis_router

app = FastAPI(
    title="AI-Powered Land Record Validation and Fraud Detection System API",
    description="Backend service providing OCR document ingestion, NLP parsing, land record verification, anomaly detection, explainable risk scoring, and GIS spatial mapping.",
    version="1.0.0",
)

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


@app.get("/")
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
