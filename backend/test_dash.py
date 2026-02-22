import pandas as pd
import sys
from app.services.analyzer import generate_dashboard
from app.api.routes.refine import _find_file_path

file_id = "3d118599-efb5-4891-8a5f-7d09de33cdf4"
file_path = _find_file_path(file_id)
df = pd.read_csv(file_path)

try:
    dash = generate_dashboard(file_id, "mock text", df=df)
    print("Success. Charts generated:", len(dash.charts))
    print("Has time series decomp:", dash.time_series_decomposition is not None)
    if dash.time_series_decomposition:
        print("Time series keys:", dash.time_series_decomposition.keys())
except Exception as e:
    print("Dashboard Exception:", str(e))
    import traceback
    traceback.print_exc()

