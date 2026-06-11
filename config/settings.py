import os
from pathlib import Path
from dotenv import load_dotenv

# Load the .env file from the root directory
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    # Existing MinIO Configurations
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    MINIO_USER: str = os.getenv("MINIO_USER", "minicrypto")
    MINIO_PASSWORD: str = os.getenv("MINIO_PASSWORD", "cryptopassword123")
    MINIO_REGION: str = os.getenv("MINIO_REGION", "us-east-1")
    
    # 🌟 NEW: Snowflake Configurations
    SNOWFLAKE_USER: str = os.getenv("SNOWFLAKE_USER")
    SNOWFLAKE_PASSWORD: str = os.getenv("SNOWFLAKE_PASSWORD")
    SNOWFLAKE_ACCOUNT: str = os.getenv("SNOWFLAKE_ACCOUNT")
    SNOWFLAKE_DATABASE: str = os.getenv("SNOWFLAKE_DATABASE", "CRYPTO_DW")
    SNOWFLAKE_SCHEMA: str = os.getenv("SNOWFLAKE_SCHEMA", "GOLD")
    SNOWFLAKE_WAREHOUSE: str = os.getenv("SNOWFLAKE_WAREHOUSE", "CRYPTO_WH")

settings = Settings()