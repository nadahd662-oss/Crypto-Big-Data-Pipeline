import sys
from pathlib import Path
from io import BytesIO
import pandas as pd
import boto3
from botocore.client import Config
import snowflake.connector

# Set up configurations
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import settings

def load_gold_to_snowflake():
    print("❄️ Connecting to local MinIO storage...")
    # 1. Connect to MinIO
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_USER,
        aws_secret_access_key=settings.MINIO_PASSWORD,
        config=Config(signature_version="s3v4"),
        region_name=settings.MINIO_REGION
    )
    
    bucket = "crypto-gold"
    
    # 2. Find the latest gold parquet files in MinIO
    print("🔍 Searching for your latest Star Schema Parquet tables...")
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket)
    
    files = {"dim_date": None, "dim_crypto": None, "fact_crypto_metrics": None}
    
    for page in pages:
        for obj in page.get('Contents', []):
            key = obj['Key']
            if not key.endswith('.parquet'):
                continue
            if 'dim_date' in key:
                files['dim_date'] = key
            elif 'dim_crypto' in key:
                files['dim_crypto'] = key
            elif 'fact_crypto_metrics' in key:
                files['fact_crypto_metrics'] = key

    if not all(files.values()):
        print("❌ Could not locate all 3 Gold Parquet tables in MinIO. Run main.py first!")
        return

    # 3. Connect to Snowflake Cloud Database
    print("❄️ Opening secure connection to Snowflake Cloud...")
    ctx = snowflake.connector.connect(
        user=settings.SNOWFLAKE_USER,
        password=settings.SNOWFLAKE_PASSWORD,
        account=settings.SNOWFLAKE_ACCOUNT,
        warehouse=settings.SNOWFLAKE_WAREHOUSE,
        database=settings.SNOWFLAKE_DATABASE,
        schema=settings.SNOWFLAKE_SCHEMA
    )
    cursor = ctx.cursor()
    
    try:
        # Disable automatic transaction commit to do it manually per table
        cursor.execute("BEGIN;")

        # 4. Read and Load each table systematically
        # 4. Read and Load each table systematically
        for table_name, file_key in files.items():
            print(f"📥 Pulling {table_name} from MinIO...")
            obj = s3_client.get_object(Bucket=bucket, Key=file_key)
            df = pd.read_parquet(BytesIO(obj['Body'].read()))
            
            # 🔍 LIGNES D'INSPECTION TEMPORAIRES :
            if table_name == "dim_date":
                print("\n--- 🛠️ INSPECTION DU DATAFRAME DIM_DATE ---")
                print("Colonnes lues depuis le Parquet :", df.columns.tolist())
                print("Aperçu des données :\n", df.head(1))
                print("Y a-t-il des valeurs nulles ? :\n", df.isnull().sum())
                print("-------------------------------------------\n")
            
            # 🌟 1. Passage en majuscules
            df.columns = [col.upper() for col in df.columns]
            
            # 🌟 2. Tri explicite des colonnes pour garantir l'alignement physique des données
            target_columns = sorted(df.columns)
            df = df[target_columns]
            
            # Ensure proper handling of NaN/None values for database compatibility
            df = df.where(pd.notnull(df), None)
            
            print(f"🚀 Uploading {len(df)} rows straight to Snowflake table: {table_name.upper()}...")
            
            # 🌟 3. Construction de la requête SQL avec l'ordre trié garanti
            cols = ", ".join(target_columns)
            binds = ", ".join(["%s"] * len(target_columns))
            insert_sql = f"INSERT INTO {table_name.upper()} ({cols}) VALUES ({binds})"
            
            # Execute batch insert
            cursor.executemany(insert_sql, df.values.tolist())
            print(f"✅ Successfully loaded rows into {table_name.upper()}!")

        cursor.execute("COMMIT;")
        print("\n🎉 All data successfully saved permanently in Snowflake!")

    except Exception as e:
        cursor.execute("ROLLBACK;")
        print(f"❌ Pipeline load crash details: {e}")
        
    finally:
        # Clean up connections
        cursor.close()
        ctx.close()
        print("🔒 Snowflake pipeline session safely disconnected.")

if __name__ == "__main__":
    load_gold_to_snowflake()