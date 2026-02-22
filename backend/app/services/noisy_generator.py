import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_noisy_data():
    np.random.seed(42)
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(days=30 * i) for i in range(24)] # 2 years of data
    
    # Base trends
    # Marketing spend increases over time with noise
    marketing_spend = [500 + 50 * i + np.random.normal(0, 50) for i in range(24)]
    
    # Revenue is correlated with marketing but has noise and seasonal shocks
    # formula: Revenue = 2000 + 4 * Marketing + noise
    revenue = [2000 + 4 * spend + np.random.normal(0, 500) for spend in marketing_spend]
    
    # Cost has a moderate correlation with revenue but its own independent noise
    # formula: Cost = 1000 + 0.3 * Revenue + noise
    cost = [1000 + 0.3 * rev + np.random.normal(0, 300) for rev in revenue]
    
    # Inject intentional anomalies (outliers)
    # 1. Flash Sale at row 12: High revenue
    revenue[12] *= 2.5 
    
    # 2. Supply Chain Crisis at row 18: Massive cost spike
    cost[18] *= 3.0
    
    # 3. Data Entry Error at row 5: Tiny revenue
    revenue[5] = 100

    df = pd.DataFrame({
        "Date": dates,
        "Marketing Spend": [round(x, 2) for x in marketing_spend],
        "Revenue": [round(x, 2) for x in revenue],
        "Cost": [round(x, 2) for x in cost]
    })
    
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    
    output_path = "/Users/berry/Antigravity/Data analysis anti/backend/uploads/noisy_financial.csv"
    df.to_csv(output_path, index=False)
    print(f"Noisy data generated at {output_path}")

if __name__ == "__main__":
    generate_noisy_data()
