import pandas as pd
from app.services.analyzer import generate_dashboard

df = pd.read_csv("../complex_stress_test.csv")
# Generate dashboard (mocking file id and text)
dash = generate_dashboard("test_id", "test text", df)
print("Growth Suggestions:", len(dash.growth_suggestions))
for g in dash.growth_suggestions:
    print(f"- {g.title}: {g.description}")
