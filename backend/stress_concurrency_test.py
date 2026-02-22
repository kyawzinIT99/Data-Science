import asyncio
import httpx
import time
import pandas as pd
import numpy as np
import io
import os

BASE_URL = "http://127.0.0.1:8000/api"
CONCURRENCY_LEVEL = 5
REQUESTS_PER_USER = 2

def generate_test_csv():
    df = pd.DataFrame({
        "Date": pd.date_range("2023-01-01", periods=100),
        "Value": np.random.randn(100).cumsum()
    })
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()

async def simulate_user(user_id):
    csv_data = generate_test_csv()
    async with httpx.AsyncClient(timeout=120.0) as client:
        print(f"User {user_id}: Starting...")
        
        # 1. Upload
        upload_start = time.time()
        files = {"file": ("test.csv", csv_data, "text/csv")}
        resp = await client.post(f"{BASE_URL}/upload", files=files)
        if resp.status_code != 200:
            print(f"User {user_id}: Upload failed: {resp.text}")
            return False
        
        file_id = resp.json()["file_id"]
        print(f"User {user_id}: Uploaded {file_id} in {time.time() - upload_start:.2f}s")
        
        # 2. Parallel Dashboard Requests
        for i in range(REQUESTS_PER_USER):
            dash_start = time.time()
            resp = await client.post(f"{BASE_URL}/dashboard", json={"file_id": file_id})
            if resp.status_code == 200:
                print(f"User {user_id}: Dashboard {i} success in {time.time() - dash_start:.2f}s")
            else:
                print(f"User {user_id}: Dashboard {i} failed: {resp.text}")
                return False
                
        # 3. Cleanup
        await client.delete(f"{BASE_URL}/files/{file_id}")
        return True

async def main():
    print(f"Starting concurrency test with {CONCURRENCY_LEVEL} users...")
    start_time = time.time()
    tasks = [simulate_user(i) for i in range(CONCURRENCY_LEVEL)]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    success_count = sum(1 for r in results if r)
    print(f"\n--- Concurrency Test Report ---")
    print(f"Total Users: {CONCURRENCY_LEVEL}")
    print(f"Successes: {success_count}")
    print(f"Failures: {CONCURRENCY_LEVEL - success_count}")
    print(f"Total Duration: {end_time - start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
