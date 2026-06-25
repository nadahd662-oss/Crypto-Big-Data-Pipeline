import sys
from pathlib import Path
from io import BytesIO
import pandas as pd
import boto3
from botocore.client import Config
from datetime import datetime

# Ensure the project root is in the Python path to import settings
sys.path.append(str(Path(__file__).resolve().parent.parent))
from scripts.settings import settings

# 1. Logique dynamique pour attraper la date passée par Airflow {{ ds }}
if len(sys.argv) > 1:
    date_str = sys.argv[1]
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    year = date_obj.strftime('%Y')
    month = date_obj.strftime('%m')
    day = date_obj.strftime('%d')
else:
    # Valeur de secours par défaut si exécuté à la main
    year, month, day = "2026", "06", "25" 

print(f"🌟 Starting Gold layer Star-Schema modeling for: year={year}/month={month}/day={day}")

def process_silver_to_gold(year, month, day):
    # 2. Initialize S3 Client for MinIO (Session isolée & Endpoint fonctionnel)
    session = boto3.Session(
        aws_access_key_id="admin",          
        aws_secret_access_key="minioadmin"   
    )
    
    s3_client = session.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,  # URL réseau Docker propre
        config=Config(signature_version="s3v4"),
        region_name="us-east-1"
    )
    
    prefix = f"year={year}/month={month}/day={day}/"
    
    # 3. Download the cleaned Parquet file from the Silver layer
    try:
        response = s3_client.list_objects_v2(Bucket="crypto-silver", Prefix=prefix)
        if 'Contents' not in response:
            print(f"⚠️ No files found in crypto-silver for path: {prefix}")
            return
            
        silver_object_key = response['Contents'][0]['Key']
        print(f"🌟 Found Silver file: {silver_object_key}. Loading data...")
        
        obj_response = s3_client.get_object(Bucket="crypto-silver", Key=silver_object_key)
        silver_data = obj_response['Body'].read()
        df = pd.read_parquet(BytesIO(silver_data))
    except Exception as e:
        print(f"❌ Failed to read data from Silver layer: {e}")
        raise e

    # Extract time context using the processed time from the Silver run
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
    dim_crypto_df.drop_duplicates(subset=['crypto_key'], inplace=True)

    # ==========================================
    # CENTRAL FACT TABLE: fact_crypto_metrics
    # ==========================================
    fact_df = df.copy()
    fact_df.rename(columns={'id': 'crypto_key'}, inplace=True)
    fact_df['date_key'] = date_key
    
    fact_df.rename(columns={
        'current_price': 'price_usd',
        'market_cap': 'market_cap_usd',
        'total_volume': 'volume_usd',
        'price_change_percentage_24h': 'pct_change_24h'
    }, inplace=True)
    
    fact_cols = ['crypto_key', 'date_key', 'price_usd', 'volume_usd', 'market_cap_usd', 'pct_change_24h']
    fact_df = fact_df[fact_cols]
    fact_df.insert(0, 'fact_id', range(1, len(fact_df) + 1))

    # ==========================================
    # SAVE AND UPLOAD BACK TO MINIO (GOLD BUCKET)
    # ==========================================
    tables_to_upload = {
        "dim_date": dim_date_df,
        "dim_crypto": dim_crypto_df,
        "fact_crypto_metrics": fact_df
    }
    
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
            raise e

if __name__ == "__main__":
    # Exécution avec les paramètres de date dynamiques
    process_silver_to_gold(year, month, day)