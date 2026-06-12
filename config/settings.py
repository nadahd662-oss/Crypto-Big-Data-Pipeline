import os
from pathlib import Path
from dotenv import load_dotenv

# 📂 Localisation et chargement automatique du fichier .env au niveau de la racine
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    # =================================================================
    # 🌐 API CONFIGURATION
    # =================================================================
    COINGECKO_URL: str = os.getenv("COINGECKO_URL", "https://api.coingecko.com/api/v3/coins/markets")
    
    # =================================================================
    # 🪣 MINIO / LOCAL STORAGE CONFIGURATION
    # =================================================================
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    
    # Gestion adaptative des doublons de nomenclature (Access Key / User)
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", os.getenv("MINIO_USER"))
    MINIO_USER: str = os.getenv("MINIO_ACCESS_KEY", os.getenv("MINIO_USER"))
    
    # Gestion adaptative des doublons de nomenclature (Secret Key / Password)
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", os.getenv("MINIO_PASSWORD"))
    MINIO_PASSWORD: str = os.getenv("MINIO_SECRET_KEY", os.getenv("MINIO_PASSWORD"))
    
    # Paramètres de structure requis par Boto3 pour le stockage local S3
    MINIO_REGION: str = os.getenv("MINIO_REGION", "us-east-1")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "crypto-bucket")

    # =================================================================
    # ❄️ SNOWFLAKE CLOUD DATA WAREHOUSE CONFIGURATION
    # =================================================================
    SNOWFLAKE_USER: str = os.getenv("SNOWFLAKE_USER")
    SNOWFLAKE_PASSWORD: str = os.getenv("SNOWFLAKE_PASSWORD")
    SNOWFLAKE_ACCOUNT: str = os.getenv("SNOWFLAKE_ACCOUNT")
    SNOWFLAKE_WAREHOUSE: str = os.getenv("SNOWFLAKE_WAREHOUSE")
    SNOWFLAKE_DATABASE: str = os.getenv("SNOWFLAKE_DATABASE")
    SNOWFLAKE_SCHEMA: str = os.getenv("SNOWFLAKE_SCHEMA")

# ⚡ Instanciation de la configuration pour un accès direct via les imports
settings = Settings()