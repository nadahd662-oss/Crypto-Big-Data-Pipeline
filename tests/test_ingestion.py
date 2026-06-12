import pandas as pd

def test_silver_layer_quality(df_silver: pd.DataFrame):
    """
    Data Quality check to run during the Silver processing phase
    """
    print("🧪 Running Data Quality Tests on Silver DataFrame...")
    
    # Test 1: Check that data actually exists
    assert len(df_silver) > 0, "❌ DQ Error: DataFrame is empty!"
    
    # Test 2: Check that our unique business identifiers are completely filled
    assert df_silver['id'].isnull().sum() == 0, "❌ DQ Error: Found null values in 'id' column!"
    
    # Test 3: Verify strict numeric boundaries (Prices shouldn't be negative)
    assert (df_silver['current_price'] >= 0).all(), "❌ DQ Error: Found negative cryptocurrency prices!"
    
    print("✅ All Data Quality tests passed successfully!")