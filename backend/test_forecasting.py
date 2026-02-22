from app.services.forecast import PriceForecaster

file_path = ".storage/uploads/f9c05ec6-827f-49cc-ada8-2c040987a462.csv"
try:
    forecaster = PriceForecaster(file_path, date_column="Timestamp", price_column="Gross_Revenue")
    df_agg = forecaster.load_data()
    print("Forecaster loaded data successfully. Rows:", len(df_agg))
    decomp = forecaster.decompose_series()
    if decomp:
        print("Decomposition succeeded. Keys:", list(decomp.keys()))
    else:
        print("Decomposition returned None")
except Exception as e:
    import traceback
    traceback.print_exc()
