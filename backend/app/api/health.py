from fastapi import APIRouter, Response
from app.database import check_db_connection

router = APIRouter()


@router.get("/health")
def health_check(response: Response):
    """
    Health check endpoint to verify backend server & database status.
    """
    db_status = check_db_connection()
    connected = db_status.get("status") == "connected"
    if not connected:
        response.status_code = 503
    return {
        "status": "ok" if connected else "unhealthy",
        "system": "LandGuard Backend",
        "database": db_status
    }
