import json
import requests
from datetime import datetime
import boto3
from botocore.client import Config
import sys
import os 
from pathlib import Path
# 1. On configure le chemin absolu pour Docker d'abord
sys.path.append("/opt/airflow")
# 2. On importe tes settings maintenant que Python sait où chercher
from dags.config.settings import settings


def run_bronze_ingestion():
    print("🚀 Fetching raw market data from CoinGecko API...")
    
    # 1. API Extraction parameters
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1
    }
    
    try:
        response = requests.get(settings.COINGECKO_URL, params=params)
        response.raise_for_status()
        raw_json = response.json()
    except Exception as e:
        print(f"❌ API Extraction failed: {e}")
        return None

    # 2. Wrap payload with an ingestion timestamp for historical lineage tracking
    now = datetime.utcnow()
    payload = {
        "ingested_at": now.isoformat() + "Z",
        "data": raw_json
    }

    # 🛠️ 3. Configuration du client MinIO (BIEN INDENTÉ À L'INTÉRIEUR DE LA FONCTION)
    # Puisque ton .env contient déjà "http://", on passe directement settings.MINIO_ENDPOINT
    s3_client = boto3.client(
        's3',
        endpoint_url=settings.MINIO_ENDPOINT,  
        aws_access_key_id=settings.MINIO_ACCESS_KEY,       
        aws_secret_access_key=settings.MINIO_SECRET_KEY,   
        region_name=settings.MINIO_REGION
    )

    # 4. Generate Hive-style partition path matching our architecture
    partition_path = f"year={now.strftime('%Y')}/month={now.strftime('%m')}/day={now.strftime('%d')}"
    file_name = f"coingecko_snapshot_{now.strftime('%H%M%S')}.json"
    object_key = f"{partition_path}/{file_name}"

    # 5. Land raw data into the Bronze bucket
    try:
        s3_client.put_object(
            Bucket="crypto-bronze",
            Key=object_key,
            Body=json.dumps(payload, indent=4),
            ContentType="application/json"
        )
        print(f"📁 Raw JSON successfully landed in: crypto-bronze/{object_key}")
        return object_key  # Returning this path so our next layer script can find it easily
    except Exception as e:
        print(f"❌ MinIO Upload failed: {e}")
        return None

if __name__ == "__main__":
    run_bronze_ingestion()