import pandas as pd
import numpy as np
from app.services.analyzer import classify_segments
import json

def test_hdbscan():
    # Create a synthetic dataset with two clear clusters and some noise
    np.random.seed(42)
    
    # Cluster 1: Low values
    c1 = pd.DataFrame({
        'price': np.random.normal(10, 2, 20),
        'quantity': np.random.normal(5, 1, 20),
        'revenue': np.random.normal(50, 5, 20)
    })
    
    # Cluster 2: High values
    c2 = pd.DataFrame({
        'price': np.random.normal(100, 10, 20),
        'quantity': np.random.normal(50, 5, 20),
        'revenue': np.random.normal(5000, 500, 20)
    })
    
    # Noise: Outliers
    noise = pd.DataFrame({
        'price': [1000, 1],
        'quantity': [1, 1000],
        'revenue': [1000, 1]
    })
    
    df = pd.concat([c1, c2, noise], ignore_index=True)
    
    print(f"Testing with {len(df)} rows...")
    segments = classify_segments(df)
    
    print(f"Detected {len(segments)} segments:")
    for i, seg in enumerate(segments):
        print(f"\nSegment {i+1}: {seg.name}")
        print(f"Size: {seg.size}")
        print(f"Characteristics: {seg.characteristics}")
        print(f"Strategy: {seg.growth_strategy}")

    if len(segments) > 1:
        print("\nSUCCESS: Multiple segments detected.")
    else:
        print("\nFAILED: Only one segment detected.")

if __name__ == "__main__":
    test_hdbscan()
