import pandas as pd
from app.services.analyzer import refine_dataframe
from app.services.forecast import PriceForecaster

# 1. Simulating the backend upload / finding the raw file
file_path = ".storage/uploads/3d118599-efb5-4891-8a5f-7d09de33cdf4.csv"
df_raw = pd.read_csv(file_path)

# 2. Simulating what the AI Refiner does 
df_clean = refine_dataframe(df_raw)

# 3. Simulate overwriting the storage layer with the cleaned variant
cleaned_path = "/tmp/cleaned_test.csv"
df_clean.to_csv(cleaned_path, index=False)

# 4. Simulate the Time-Series Forecaster 
try:
    forecaster = PriceForecaster(cleaned_path) # Now completely auto-detecting everything 
    df_agg = forecaster.load_data()
    print("Auto-detection worked! Date:", forecaster.date_column, "Price:", forecaster.price_column)
    print("Aggregated Monthly Rows:", len(df_agg))
    
    decomp = forecaster.decompose_series()
    if decomp:
        print("SUCCESS! Decomposed keys:", decomp.keys())
    else:
        print("FAIL: Decomposition returned None")
except Exception as e:
    import traceback
    traceback.print_exc()
