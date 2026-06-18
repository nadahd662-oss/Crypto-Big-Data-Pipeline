import os
from pathlib import Path
from dotenv import load_dotenv

# 📂 On force la recherche du .env local qui est dans le dossier scripts/
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    # =========================================================================
    # 🌐 API CONFIGURATION
    # =========================================================================
    COINGECKO_URL: str = os.getenv("COINGECKO_URL", "https://api.coingecko.com/api/v3/coins/markets")

    # =========================================================================
    # 🐳 MINIO / LOCAL STORAGE CONFIGURATION (FORCÉ POUR DOCKER)
    # =========================================================================
    # On force 'host.docker.internal' en dur pour qu'aucun fichier .env mal configuré ne vienne remettre 'localhost'
    MINIO_ENDPOINT: str = "http://host.docker.internal:9000"
    
    # Gestion adaptative des doublons de nomenclature (Access Key / User)
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_USER: str = os.getenv("MINIO_USER", "minioadmin")
    
    # Gestion adaptative des doublons de nomenclature (Secret Key / Password)
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_PASSWORD: str = os.getenv("MINIO_PASSWORD", "minioadmin")
    
    # Paramètres de structure requis par Boto3 pour le stockage local S3
    MINIO_REGION: str = os.getenv("MINIO_REGION", "us-east-1")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "crypto-bucket")

    # =========================================================================
    # ❄️ SNOWFLAKE CLOUD DATA WAREHOUSE CONFIGURATION
    # =========================================================================
    SNOWFLAKE_USER: str = os.getenv("nada")
    SNOWFLAKE_PASSWORD: str = os.getenv("Snowflake@Nada21")
    SNOWFLAKE_ACCOUNT: str = os.getenv("kk17361.switzerland-north.azure")
    SNOWFLAKE_WAREHOUSE: str = os.getenv("CRYPTO_DW")
    SNOWFLAKE_DATABASE: str = os.getenv("GOLD")
    SNOWFLAKE_SCHEMA: str = os.getenv("CRYPTO_WH")

# ⚡ Instanciation de la configuration pour un accès direct via les imports
settings = Settings()