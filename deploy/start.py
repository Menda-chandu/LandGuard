"""Launch with Render's assigned port and forward shutdown signals directly."""
import os
import sys

os.execvp(sys.executable, [sys.executable, "-m", "uvicorn", "app.main:app",
                          "--app-dir", "/app/backend", "--host", "0.0.0.0",
                          "--port", os.getenv("PORT", "10000")])
