import sys
from pathlib import Path

# Tell Python where to find your scripts folder
sys.path.append(str(Path(__file__).resolve().parent))

# Import the core functions from the scripts you already wrote
from scripts.ingest_bronze import run_bronze_ingestion
from scripts.process_silver import process_bronze_to_silver
from scripts.model_gold import process_silver_to_gold

def run_complete_pipeline():
    print("=================================================================")
    print("🚀 STARTING CRYPTO END-TO-END MEDALLION PIPELINE")
    print("=================================================================\n")
    
    # -----------------------------------------------------------------
    # STEP 1: BRONZE LAYER
    # -----------------------------------------------------------------
    print("📥 [1/3] Launching Step 1: Bronze Ingestion...")
    # This runs your script and returns the exact file name it created
    bronze_file_key = run_bronze_ingestion()
    
    if not bronze_file_key:
        print("❌ Pipeline failed at the Bronze layer. Stopping execution.")
        return
        
    print(f"✅ Bronze layer finished! File landed: {bronze_file_key}\n")
    print("-" * 65)

    # -----------------------------------------------------------------
    # STEP 2: SILVER LAYER
    # -----------------------------------------------------------------
    print("🧹 [2/3] Launching Step 2: Silver Transformation...")
    # We pass the file name from Bronze directly into Silver automatically!
    process_bronze_to_silver(bronze_file_key)
    
    # Generate what the silver file name will be (.parquet instead of .json)
    silver_file_key = bronze_file_key.replace(".json", ".parquet")
    print(f"✅ Silver layer finished! Clean file landed: {silver_file_key}\n")
    print("-" * 65)

    # -----------------------------------------------------------------
    # STEP 3: GOLD LAYER
    # -----------------------------------------------------------------
    print("🌟 [3/3] Launching Step 3: Gold Dimensional Modeling...")
    # We pass the clean silver file directly into Gold automatically!
    process_silver_to_gold(silver_file_key)
    print("✅ Gold layer finished! Star Schema tables updated successfully.\n")
    
    print("=================================================================")
    print("🎉 SUCCESS: ALL LOCAL PIPELINE LAYERS FULLY AUTOMATED!")
    print("=================================================================")

if __name__ == "__main__":
    run_complete_pipeline()