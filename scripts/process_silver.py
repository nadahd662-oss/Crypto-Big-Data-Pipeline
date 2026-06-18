import json
import pandas as pd
import boto3
from io import BytesIO
from botocore.client import Config
import sys
from pathlib import Path

# Include project root path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from dags.config.settings import settings

def process_bronze_to_silver(bronze_object_key):
    print(f"🧹 Starting Silver layer transformation for: {bronze_object_key}...")
    
    # 1. Initialize S3/MinIO Client
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_USER,
        aws_secret_access_key=settings.MINIO_PASSWORD,
        config=Config(signature_version="s3v4"),
        region_name=settings.MINIO_REGION
    )
    
    # 2. Pull the raw JSON object from the Bronze bucket
    try:
        response = s3_client.get_object(Bucket="crypto-bronze", Key=bronze_object_key)
        file_content = response['Body'].read().decode('utf-8')
        payload = json.loads(file_content)
    except Exception as e:
        print(f"❌ Failed to read data from Bronze layer: {e}")
        return

    # Extract our core list and the structural tracking timestamp
    raw_records = payload["data"]
    ingested_at = payload["ingested_at"]

    # 3. Load records directly into a Pandas DataFrame
    df = pd.DataFrame(raw_records)

    # 4. Data Cleansing & Selection Step
    # Filter columns to keep only data fields necessary for downstream modeling
    columns_to_keep = [
        'id', 'symbol', 'name', 'current_price', 
        'market_cap', 'total_volume', 'price_change_percentage_24h'
    ]
    df = df[columns_to_keep]

    # Enforce strict data types to protect downstream schemas from errors
    df['current_price'] = df['current_price'].astype(float)
    df['market_cap'] = df['market_cap'].astype(float)
    df['total_volume'] = df['total_volume'].astype(float)
    df['price_change_percentage_24h'] = df['price_change_percentage_24h'].fillna(0.0).astype(float)

    # Inject data lineage attributes to keep audit paths clear
    df['source_file'] = bronze_object_key
    df['processed_at'] = pd.Timestamp.utcnow()

    # 5. Convert clean DataFrame to Parquet format in-memory
    parquet_buffer = BytesIO()
    df.to_parquet(parquet_buffer, index=False, engine='pyarrow')
    parquet_buffer.seek(0)

    # 6. Generate matching Silver destination path
    # Keeps identical folder layout but swaps out file format extension
    silver_object_key = bronze_object_key.replace(".json", ".parquet")

    # 7. Push pristine clean file up to crypto-silver
    try:
        s3_client.put_object(
            Bucket="crypto-silver",
            Key=silver_object_key,
            Body=parquet_buffer.getvalue(),
            ContentType="application/octet-stream"
        )
        print(f"✅ Success! Clean data stored at: crypto-silver/{silver_object_key}")
    except Exception as e:
        print(f"❌ Failed saving data to Silver layer: {e}")

if __name__ == "__main__":
    # Test path (Replace this with a real file path visible in your crypto-bronze bucket)
    # Example: "year=2026/month=06/day=09/coingecko_snapshot_143000.json"
    example_key = "year=2026/month=06/day=09/coingecko_snapshot_140149.json"
    process_bronze_to_silver(example_key)