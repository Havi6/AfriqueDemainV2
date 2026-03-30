import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.environ.get("ACCESS_TOKEN_EXPIRE_HOURS", 8))

DATABASE_URL = os.environ.get("DATABASE_URL")
#DATABASE_URL = "postgresql://postgres:havi6@localhost:5432/ChatDatabase"
ENCODING = "utf-8"
FILES_UPLOAD_DIR = os.environ.get("FILES_UPLOAD_DIR", os.path.join(BASE_DIR, "uploaded_files"))

# changement de db vers postgres
#
# os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'app_fastapi.db')}")