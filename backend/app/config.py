import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from .env or landguard.env in project root or backend directory
base_dir = Path(__file__).resolve().parent.parent
root_dir = base_dir.parent
for env_name in (".env", "landguard.env"):
    load_dotenv(dotenv_path=root_dir / env_name, override=False)
    load_dotenv(dotenv_path=base_dir / env_name, override=False)
load_dotenv(override=False)


class Settings:
    PROJECT_NAME: str = "AI-Powered Land Record Validation and Fraud Detection System"
    VERSION: str = "1.0.0"
    DATASET_DIR: Path = Path(os.getenv("LANDGUARD_DATASET_DIR", str(root_dir / "sample_data"))).resolve()
    SEED_DEMO_DATA: bool = os.getenv("SEED_DEMO_DATA", "0") == "1"
    KEEP_LOCAL_UPLOADS: bool = os.getenv("KEEP_LOCAL_UPLOADS", "1") == "1"
    FRONTEND_DIST: Path = Path(os.getenv("FRONTEND_DIST", str(root_dir / "frontend" / "dist"))).resolve()

    # Database Configuration
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "127.0.0.1")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "landguard_db")

    # OCR Configuration
    TESSERACT_PATH: str = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

    @property
    def DATABASE_URL(self) -> str:
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return env_url.replace("postgres://", "postgresql://", 1) if env_url.startswith("postgres://") else env_url
        user = os.getenv("POSTGRES_USER", self.POSTGRES_USER)
        raw_password = os.getenv("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        password = quote_plus(raw_password)
        host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        port = os.getenv("POSTGRES_PORT", self.POSTGRES_PORT)
        db = os.getenv("POSTGRES_DB", self.POSTGRES_DB)
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"


settings = Settings()
