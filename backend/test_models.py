import requests
import json
import os
import sys

UPLOAD_URL = "http://localhost:8000/api/upload"

# Try to find a noisy dataset in the test_files directory or similar
test_file = "../time_series_sample.csv"
if not os.path.exists(test_file):
    test_file = "../test_data.csv"
    
if not os.path.exists(test_file):
    print("Could not find a test file.")
    sys.exit(1)

print(f"Uploading and analyzing {test_file}...")

with open(test_file, 'rb') as f:
    # Use kyawzin_cloud_access_v4 token based on auth.py inspection from Phase 7
    headers = {"Authorization": "Bearer kyawzin_cloud_access_v4"}
    files = {"file": (os.path.basename(test_file), f, "text/csv")}
    
    # 1. Upload the file
    upload_res = requests.post(UPLOAD_URL, headers=headers, files=files)
    
    if upload_res.status_code != 200:
        print(f"Upload failed: {upload_res.status_code}")
        print(upload_res.text)
        sys.exit(1)
        
    upload_data = upload_res.json()
    file_id = upload_data.get("file_id")
    print(f"Upload successful. File ID: {file_id}")
    
    # 2. Generate Dashboard directly via the analysis endpoint
    ANALYSIS_URL = "http://localhost:8000/api/dashboard"
    print("Requesting dashboard generation...")
    dash_res = requests.post(ANALYSIS_URL, headers=headers, json={"file_id": file_id})
    
    if dash_res.status_code != 200:
        print(f"Dashboard generation failed: {dash_res.status_code}")
        print(dash_res.text)
        sys.exit(1)
        
    dash_data = dash_res.json()
    
    print("\n--- Dashboard Verification ---")
    
    # Verify Models
    print(f"1. Profit & Loss Data: {'✅ Found' if dash_data.get('profit_loss') else '❌ Missing'}")
    if dash_data.get('profit_loss'):
        print(f"   - Revenue: {dash_data['profit_loss'].get('total_revenue')}")
        print(f"   - Cost: {dash_data['profit_loss'].get('total_cost')}")
        
    print(f"2. Time Series Decomposition: {'✅ Found' if dash_data.get('time_series_decomposition') else '❌ Missing'}")
    if dash_data.get('time_series_decomposition'):
        print(f"   - Points: len({len(dash_data['time_series_decomposition'].get('observed', []))})")
        
    print(f"3. Market Segments: {'✅ Found' if dash_data.get('segments') else '❌ Missing'}")
    if dash_data.get('segments'):
        print(f"   - Number of Segments: {len(dash_data.get('segments', []))}")
        
    print(f"4. AI Swarm Intelligence (Agents): {'✅ Found' if dash_data.get('agent_insights') else '❌ Missing'}")
    if dash_data.get('agent_insights'):
        print(f"   - Number of Agents: {len(dash_data.get('agent_insights', []))}")

print("\nVerification script finished.")
