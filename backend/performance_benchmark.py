import time
import pandas as pd
import numpy as np
import os
import json
from app.services.analyzer import classify_segments
# Note: Forecasting is harder to test directly without full environment setup, 
# but we can benchmark the clustering logic which is also offloaded to Modal.

def generate_benchmark_data(n_rows):
    return pd.DataFrame({
        "Feature1": np.random.randn(n_rows),
        "Feature2": np.random.randn(n_rows),
        "Feature3": np.random.randn(n_rows),
        "Feature4": np.random.randn(n_rows)
    })

def run_benchmarks():
    print("--- Local Performance Benchmark ---")
    scales = [1000, 5000, 10000]
    results = []

    for scale in scales:
        print(f"Benchmarking Scale: {scale} rows...")
        df = generate_benchmark_data(scale)
        df_json = df.to_json(orient="records")
        
        start_time = time.time()
        # Direct call to the service function that would be offloaded
        segments = classify_segments(df)
        duration = time.time() - start_time
        
        results.append({
            "Scale": scale,
            "Duration": duration,
            "SegmentsFound": len(segments)
        })
        print(f"  Duration: {duration:.4f}s")

    print("\n--- Summary Table ---")
    print(f"{'Scale':<10} | {'Duration (s)':<15} | {'Segments'}")
    print("-" * 40)
    for r in results:
        print(f"{r['Scale']:<10} | {r['Duration']:<15.4f} | {r['SegmentsFound']}")

if __name__ == "__main__":
    # Ensure we are in the correct directory to import app
    run_benchmarks()
