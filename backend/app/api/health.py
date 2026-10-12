from fastapi import APIRouter
from app.database import check_db_connection

router = APIRouter()


@router.get("/health")
def health_check():
    """
    Health check endpoint to verify backend server & database status.
    """
    db_status = check_db_connection()
    return {
        "status": "ok",
        "system": "LandGuard Backend",
        "database": db_status
    }
