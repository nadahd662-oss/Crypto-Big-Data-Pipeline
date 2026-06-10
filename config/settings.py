import os
from pathlib import Path
from dotenv import load_dotenv

# Locate the root directory and load the .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings:
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    MINIO_USER = os.getenv("MINIO_ROOT_USER")
    MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
    MINIO_REGION = os.getenv("MINIO_REGION", "us-east-1")
    
    COINGECKO_URL = f"{os.getenv('COINGECKO_BASE_URL')}/coins/markets"

settings = Settings()