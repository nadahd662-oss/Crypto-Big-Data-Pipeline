import sys
from pathlib import Path
from io import BytesIO
import pandas as pd
import boto3
from botocore.client import Config

# Assurer que la racine du projet est dans le chemin Python pour l'import de la config
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import settings

def show_gold_market_report():
    print("Fetching the latest financial data from the Gold Layer in MinIO...\n")
    
    # 1. 🛠️ Connexion sécurisée à MinIO avec les variables globales unifiées
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name=settings.MINIO_REGION
    )
    
    # 2. Recherche dynamique des dernières tables de faits et dimensions dans le bucket Gold
    try:
        bucket = "crypto-gold"
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
            print("❌ Could not find the Gold tables. Did you run run_pipeline.py?")
            return
            
        # 3. Téléchargement et chargement des fichiers Parquet dans Pandas
        fact_obj = s3_client.get_object(Bucket=bucket, Key=fact_key)
        fact_df = pd.read_parquet(BytesIO(fact_obj['Body'].read()))
        
        dim_obj = s3_client.get_object(Bucket=bucket, Key=dim_key)
        dim_df = pd.read_parquet(BytesIO(dim_obj['Body'].read()))
        
    except Exception as e:
        print(f"❌ Failed to read from Gold storage: {e}")
        return

    # 4. Fusion des données (Merge) basée sur la clé de jointure 'crypto_key'
    # On passe temporairement toutes les colonnes en minuscules pour garantir la réussite du merge
    fact_df.columns = [c.lower() for c in fact_df.columns]
    dim_df.columns = [c.lower() for c in dim_df.columns]
    
    report_df = pd.merge(fact_df, dim_df, on='crypto_key')
    
    # 5. Affichage du rapport final mis en forme
    print("=============================================================================")
    print("🪙                 CRYPTO DATA PIPELINE: LIVE MARKET REPORT                  ")
    print("=============================================================================")
    
    # Identification sécurisée des colonnes requises
    try:
        market_cap_col = [c for c in report_df.columns if 'cap' in c][0]
        price_col = [c for c in report_df.columns if 'price' in c or 'current' in c][0]
        volume_col = [c for c in report_df.columns if 'volume' in c or 'total' in c][0]
        name_col = 'name' if 'name' in report_df.columns else 'id'
        symbol_col = 'symbol'
    except IndexError:
        print("❌ Error: Could not map the expected Star Schema columns automatically.")
        print(f"Available columns: {list(report_df.columns)}")
        return

    # Tri pour obtenir le Top 5 des cryptos par capitalisation boursière
    top_5 = report_df.sort_values(by=market_cap_col, ascending=False).head(5)
    
    for idx, row in top_5.iterrows():
        name = str(row[name_col]).title()
        symbol = str(row[symbol_col]).upper()
        price = f"${row[price_col]:,.2f}"
        volume = f"${row[volume_col]:,.0f}"
        market_cap = f"${row[market_cap_col]:,.0f}"
        
        print(f"🔹 {name} ({symbol})")
        print(f"   Price:      {price:<15} Market Cap: {market_cap}")
        print(f"   24h Volume: {volume}")
        print("-" * 77)

if __name__ == "__main__":
    show_gold_market_report()