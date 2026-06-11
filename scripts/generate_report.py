import sys
from pathlib import Path
from io import BytesIO
import pandas as pd
import boto3
from botocore.client import Config

# Connect to our configuration settings
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import settings

def show_gold_market_report():
    print("Fetching the latest financial data from the Gold Layer...\n")
    
    # 1. Connect to MinIO
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_USER,
        aws_secret_access_key=settings.MINIO_PASSWORD,
        config=Config(signature_version="s3v4"),
        region_name=settings.MINIO_REGION
    )
    
    # 2. Look inside the crypto-gold bucket to find our tables
    try:
        # We will pull the Fact table and the Crypto dimension table
        # We use a shortcut here to find the files we just created
        bucket = "crypto-gold"
        
        # Let's find the files in your bucket
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket)
        
        fact_key = None
        dim_key = None
        
        for page in pages:
            for obj in page.get('Contents', []):
                if 'fact_crypto_metrics' in obj['Key'] and obj['Key'].endswith('.parquet'):
                    fact_key = obj['Key']
                if 'dim_crypto' in obj['Key'] and obj['Key'].endswith('.parquet'):
                    dim_key = obj['Key']
        
        if not fact_key or not dim_key:
            print("❌ Could not find the Gold tables. Did you run model_gold.py?")
            return
            
        # 3. Download both tables into Pandas
        fact_obj = s3_client.get_object(Bucket=bucket, Key=fact_key)
        fact_df = pd.read_parquet(BytesIO(fact_obj['Body'].read()))
        
        dim_obj = s3_client.get_object(Bucket=bucket, Key=dim_key)
        dim_df = pd.read_parquet(BytesIO(dim_obj['Body'].read()))
        
    except Exception as e:
        print(f"❌ Failed to read from Gold storage: {e}")
        return

    # 4. Human-Readable Merge (The Magic Step)
    # We join the Fact table (numbers) with the Dimension table (names) using the 'crypto_key'
    report_df = pd.merge(fact_df, dim_df, on='crypto_key')
    
    # 5. Clean up the look for human eyes
    print("=============================================================================")
    print("🪙               CRYPTO DATA PIPELINE: LIVE MARKET REPORT                    ")
    print("=============================================================================")
    
    # Grab the top 5 cryptocurrencies by market size
    top_5 = report_df.sort_values(by='market_cap_usd', ascending=False).head(5)
    
    for idx, row in top_5.iterrows():
        name = row['name']
        symbol = row['symbol'].upper()
        price = f"${row['price_usd']:,.2f}"
        volume = f"${row['volume_usd']:,.0f}"
        change = row['pct_change_24h']
        
        # Add a green arrow for up, red arrow for down
        arrow = "🔺" if change >= 0 else "🔻"
        
        print(f"🔹 {name} ({symbol})")
        print(f"   Price:  {price:<15} 24h Change: {arrow} {change:+.2f}%")
        print(f"   Volume: {volume}")
        print("-" * 77)

if __name__ == "__main__":
    show_gold_market_report()