import pandas as pd
from app.services.causal import generate_causal_network

df = pd.read_csv("../complex_stress_test.csv")
net = generate_causal_network(df)
print("Nodes:", len(net.nodes))
print("Links:", len(net.links))
print("Counterfactuals:")
for c in net.counterfactuals:
    print(f"- {c.description}")
print("Error:", net.error)
