import json
import pandas as pd
import boto3
from io import BytesIO
from botocore.client import Config
import sys
from pathlib import Path
from datetime import datetime

# Include project root path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from scripts.settings import settings

# Logique dynamique pour attraper la date passée par Airflow
if len(sys.argv) > 1:
    date_str = sys.argv[1]
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    year = date_obj.strftime('%Y')
    month = date_obj.strftime('%m')
    day = date_obj.strftime('%d')
else:
    year, month, day = "2026", "06", "24" 

print(f"🧹 Starting Silver layer transformation for: year={year}/month={month}/day={day}")

def process_bronze_to_silver(year, month, day):
    # =========================================================================
    # 1. Initialize S3/MinIO Client (Session isolée pour éviter les conflits)
    # =========================================================================
    # On crée une session boto3 explicite pour ignorer les configurations AWS locales parasites
    session = boto3.Session(
        aws_access_key_id="minicrypto",          # Ton login console MinIO
        aws_secret_access_key="cryptopassword123"   # Ton mot de passe console MinIO
    )
    
    s3_client = session.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,    # Assure-toi que c'est bien l'URL de ton service Docker MinIO
        config=Config(signature_version="s3v4"),
        region_name="us-east-1"
    )
    # =========================================================================
    
    prefix = f"year={year}/month={month}/day={day}/"
    
    # Trouver le fichier JSON dynamique dans le dossier du jour
    try:
        response = s3_client.list_objects_v2(Bucket="crypto-bronze", Prefix=prefix)
        if 'Contents' not in response:
            print(f"⚠️ No files found in crypto-bronze for path: {prefix}")
            return
        
        # On prend le premier fichier trouvé pour ce jour
        bronze_object_key = response['Contents'][0]['Key']
        print(f"🧹 Processing file: {bronze_object_key}...")
        
        # 2. Pull the raw JSON object
        obj_response = s3_client.get_object(Bucket="crypto-bronze", Key=bronze_object_key)
        file_content = obj_response['Body'].read().decode('utf-8')
        payload = json.loads(file_content)
    except Exception as e:
        print(f"❌ Failed to read data from Bronze layer: {e}")
        raise e  # Force Airflow à voir l'erreur (Fini le faux Return Code 0 !)

    # Extract our core list
    raw_records = payload["data"]

    # 3. Load records directly into a Pandas DataFrame
    df = pd.DataFrame(raw_records)

    # 4. Data Cleansing & Selection Step
    columns_to_keep = [
        'id', 'symbol', 'name', 'current_price', 
        'market_cap', 'total_volume', 'price_change_percentage_24h'
    ]
    df = df[columns_to_keep]

    # Enforce strict data types
    df['current_price'] = df['current_price'].astype(float)
    df['market_cap'] = df['market_cap'].astype(float)
    df['total_volume'] = df['total_volume'].astype(float)
    df['price_change_percentage_24h'] = df['price_change_percentage_24h'].fillna(0.0).astype(float)

    # Inject data lineage attributes
    df['source_file'] = bronze_object_key
    df['processed_at'] = pd.Timestamp.utcnow()

    # 5. Convert clean DataFrame to Parquet format in-memory
    parquet_buffer = BytesIO()
    df.to_parquet(parquet_buffer, index=False, engine='pyarrow')
    parquet_buffer.seek(0)

    # 6. Generate matching Silver destination path
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
        raise e

if __name__ == "__main__":
    # On passe les variables dynamiques calculées grâce à sys.argv
    process_bronze_to_silver(year, month, day)