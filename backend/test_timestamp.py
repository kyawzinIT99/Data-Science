import pandas as pd
from app.services.analyzer import refine_dataframe

df = pd.read_csv('/Users/berry/Antigravity/Data analysis anti version2/backend/.storage/uploads/3d118599-efb5-4891-8a5f-7d09de33cdf4.csv')
print("Original Timestamps (Top 5):", df['Timestamp'].head(5).tolist())

df_clean = refine_dataframe(df)

print("Cleaned Timestamps (Top 5):", df_clean['Timestamp'].head(5).tolist())
print("NaN count in Timestamp:", df_clean['Timestamp'].isna().sum())

