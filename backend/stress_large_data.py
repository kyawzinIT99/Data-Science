import httpx
import time
import pandas as pd
import numpy as np
import os
import hashlib

BASE_URL = "http://127.0.0.1:8000/api"
LARGE_FILE_PATH = "stress_large_50mb.csv"
UPLOADS_DIR = ".storage/uploads"

def generate_large_csv(rows=500000):
    print(f"Generating {rows} rows of data (~50MB)...")
    df = pd.DataFrame({
        "ID": np.arange(rows),
        "Date": pd.date_range("2020-01-01", periods=rows, freq="min"),
        "Category": np.random.choice(["A", "B", "C", "D"], rows),
        "Value": np.random.randn(rows),
        "Note": ["Long string to increase file size " * 5 for _ in range(rows)]
    })
    df.to_csv(LARGE_FILE_PATH, index=False)
    size_mb = os.path.getsize(LARGE_FILE_PATH) / (1024 * 1024)
    print(f"File generated: {size_mb:.2f} MB")
    return LARGE_FILE_PATH

def get_file_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_large_upload_test():
    filepath = generate_large_csv()
    local_hash = get_file_hash(filepath)
    
    print("Uploading large file via streaming...")
    start_time = time.time()
    
    try:
        with httpx.Client(timeout=300.0) as client:
            with open(filepath, "rb") as f:
                resp = client.post(f"{BASE_URL}/upload", files={"file": (filepath, f, "text/csv")})
            
            if resp.status_code != 200:
                print(f"Upload failed: {resp.text}")
                return
            
            file_id = resp.json()["file_id"]
            duration = time.time() - start_time
            print(f"Upload successful: {file_id} (Duration: {duration:.2f}s)")
            
            # Verify persistence
            server_path = os.path.join(UPLOADS_DIR, f"{file_id}.csv")
            if os.path.exists(server_path):
                server_hash = get_file_hash(server_path)
                if server_hash == local_hash:
                    print("✅ Hash Verification: PASS (Perfect Persistence)")
                else:
                    print("❌ Hash Verification: FAIL (Data Corruption)")
            else:
                print("❌ File Missing on Server")
                
            # Try dashboard generation on large file (stress processing)
            print("Requesting dashboard for large file...")
            dash_start = time.time()
            resp = client.post(f"{BASE_URL}/dashboard", json={"file_id": file_id})
            if resp.status_code == 200:
                print(f"Dashboard success in {time.time() - dash_start:.2f}s")
            else:
                print(f"Dashboard failed: {resp.text}")

    except Exception as e:
        print(f"Test Error: {e}")
    finally:
        if os.path.exists(LARGE_FILE_PATH):
            os.remove(LARGE_FILE_PATH)

if __name__ == "__main__":
    run_large_upload_test()
