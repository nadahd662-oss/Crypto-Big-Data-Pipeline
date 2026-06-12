import sys
from pathlib import Path

# Tell Python where to find your scripts folder
sys.path.append(str(Path(__file__).resolve().parent))

# Import the core functions from the scripts you already wrote
from scripts.ingest_bronze import run_bronze_ingestion
from scripts.process_silver import process_bronze_to_silver
from scripts.model_gold import process_silver_to_gold
# ❄️ L'import manquant crucial pour l'étape finale !
from scripts.load_snowflake import load_gold_to_snowflake

def run_complete_pipeline():
    print("=================================================================")
    print("🚀 STARTING CRYPTO END-TO-END MEDALLION PIPELINE")
    print("=================================================================\n")
    
    # -----------------------------------------------------------------
    # STEP 1: BRONZE LAYER
    # -----------------------------------------------------------------
    print("📥 [1/4] Launching Step 1: Bronze Ingestion...")
    bronze_file_key = run_bronze_ingestion()
    
    if not bronze_file_key:
        print("❌ Pipeline failed at the Bronze layer. Stopping execution.")
        return
        
    print(f"✅ Bronze layer finished! File landed: {bronze_file_key}\n")
    print("-" * 65)

    # -----------------------------------------------------------------
    # STEP 2: SILVER LAYER
    # -----------------------------------------------------------------
    print("🧹 [2/4] Launching Step 2: Silver Transformation...")
    process_bronze_to_silver(bronze_file_key)
    
    silver_file_key = bronze_file_key.replace(".json", ".parquet")
    print(f"✅ Silver layer finished! Clean file landed: {silver_file_key}\n")
    print("-" * 65)

    # -----------------------------------------------------------------
    # STEP 3: GOLD LAYER
    # -----------------------------------------------------------------
    print("🌟 [3/4] Launching Step 3: Gold Dimensional Modeling...")
    process_silver_to_gold(silver_file_key)
    print("✅ Gold layer finished! Star Schema tables updated successfully in MinIO.\n")
    print("-" * 65)

    # -----------------------------------------------------------------
    # STEP 4: SNOWFLAKE LOAD (Le chaînon manquant !)
    # -----------------------------------------------------------------
    print("❄️ [4/4] Launching Step 4: Loading Star Schema into Snowflake Cloud...")
    # On appelle ton script de chargement qui a si bien fonctionné tout à l'heure
    load_gold_to_snowflake()
    print("✅ Snowflake layer finished! Data is permanently online.\n")
    
    print("=================================================================")
    print("🎉 SUCCESS: ALL PIPELINE LAYERS FULLY AUTOMATED FROM API TO CLOUD!")
    print("=================================================================")

if __name__ == "__main__":
    run_complete_pipeline()