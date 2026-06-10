import sys
from pathlib import Path
from io import BytesIO
import pandas as pd
import boto3
from botocore.client import Config

# Ensure the project root is in the Python path to import settings
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import settings

def process_silver_to_gold(silver_object_key):
    print(f"🌟 Starting Gold layer Star-Schema modeling for: {silver_object_key}...")
    
    # 1. Initialize S3 Client for MinIO
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_USER,
        aws_secret_access_key=settings.MINIO_PASSWORD,
        config=Config(signature_version="s3v4"),
        region_name=settings.MINIO_REGION
    )
    
    # 2. Download the cleaned Parquet file from the Silver layer
    try:
        response = s3_client.get_object(Bucket="crypto-silver", Key=silver_object_key)
        silver_data = response['Body'].read()
        df = pd.read_parquet(BytesIO(silver_data))
    except Exception as e:
        print(f"❌ Failed to read data from Silver layer: {e}")
        return

    # Extract time context using the processed time from the Silver run
    # (Using the first row as an anchor point)
    run_timestamp = pd.to_datetime(df['processed_at'].iloc[0])
    
    # ==========================================
    # DIMENSION 1: dim_date
    # ==========================================
    date_key = int(run_timestamp.strftime("%Y%m%d"))
    dim_date_df = pd.DataFrame([{
        "date_key": date_key,
        "full_date": run_timestamp.date(),
        "day_name": run_timestamp.strftime("%A"),
        "month": run_timestamp.month,
        "quarter": (run_timestamp.month - 1) // 3 + 1,
        "year": run_timestamp.year
    }])

    # ==========================================
    # DIMENSION 2: dim_crypto
    # ==========================================
    dim_crypto_df = df[['id', 'symbol', 'name']].copy()
    dim_crypto_df.rename(columns={'id': 'crypto_key'}, inplace=True)
    # Deduplicate to guarantee unique primary keys in the dimension
    dim_crypto_df.drop_duplicates(subset=['crypto_key'], inplace=True)

    # ==========================================
    # CENTRAL FACT TABLE: fact_crypto_metrics
    # ==========================================
    fact_df = df.copy()
    fact_df.rename(columns={'id': 'crypto_key'}, inplace=True)
    
    # Attach our foreign key references
    fact_df['date_key'] = date_key
    
    # Transform names to match our ERD design blueprint exactly
    fact_df.rename(columns={
        'current_price': 'price_usd',
        'market_cap': 'market_cap_usd',
        'total_volume': 'volume_usd',
        'price_change_percentage_24h': 'pct_change_24h'
    }, inplace=True)
    
    # Retain columns matching the architectural ERD
    fact_cols = ['crypto_key', 'date_key', 'price_usd', 'volume_usd', 'market_cap_usd', 'pct_change_24h']
    fact_df = fact_df[fact_cols]
    
    # Generate an auto-incrementing surrogate Primary Key (fact_id)
    fact_df.insert(0, 'fact_id', range(1, len(fact_df) + 1))

    # ==========================================
    # SAVE AND UPLOAD BACK TO MINIO (GOLD BUCKET)
    # ==========================================
    tables_to_upload = {
        "dim_date": dim_date_df,
        "dim_crypto": dim_crypto_df,
        "fact_crypto_metrics": fact_df
    }
    
    # Maintain identical Hive partition structure for easy directory traversal
    base_partition = silver_object_key.split("/coingecko_")[0]
    run_id = silver_object_key.split("snapshot_")[-1].replace(".parquet", "")

    for table_name, target_df in tables_to_upload.items():
        buffer = BytesIO()
        target_df.to_parquet(buffer, index=False, engine='pyarrow')
        buffer.seek(0)
        
        gold_key = f"{table_name}/{base_partition}/gold_{table_name}_{run_id}.parquet"
        
        try:
            s3_client.put_object(
                Bucket="crypto-gold",
                Key=gold_key,
                Body=buffer.getvalue(),
                ContentType="application/octet-stream"
            )
            print(f"👑 Landed in Gold: crypto-gold/{gold_key}")
        except Exception as e:
            print(f"❌ Failed saving {table_name} to Gold layer: {e}")

if __name__ == "__main__":
    # Test stub (Provide an existing key from your crypto-silver bucket folder to test execution)
    # Example: "year=2026/month=06/day=09/coingecko_snapshot_143000.parquet"
    test_silver_key = "year=2026/month=06/day=09/coingecko_snapshot_140149.parquet"               
    process_silver_to_gold(test_silver_key)