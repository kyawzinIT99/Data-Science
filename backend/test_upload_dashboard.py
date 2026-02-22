import httpx
import time

def test_workflow():
    base_url = "http://127.0.0.1:8000/api"
    file_path = "/Users/berry/Antigravity/Data analysis anti copy/time_series_sample.csv"
    
    # 1. Upload
    print("Uploading file...")
    with open(file_path, "rb") as f:
        files = {"file": f}
        start = time.time()
        res = httpx.post(f"{base_url}/upload", files=files, timeout=120)
        print(f"Upload took {time.time()-start:.2f}s")
        print("Upload status:", res.status_code)
        if res.status_code != 200:
            print("Upload failed:", res.text)
            return
        file_id = res.json()["file_id"]

    # 2. Analyze
    print(f"Analyzing file {file_id}...")
    start = time.time()
    res = httpx.post(f"{base_url}/analyze", json={"file_id": file_id}, timeout=120)
    print(f"Analyze took {time.time()-start:.2f}s")
    print("Analyze status:", res.status_code)

    # 3. Dashboard
    print(f"Generating dashboard for {file_id}...")
    start = time.time()
    try:
        res = httpx.post(f"{base_url}/dashboard", json={"file_id": file_id}, timeout=120)
        print(f"Dashboard took {time.time()-start:.2f}s")
        print("Dashboard status:", res.status_code)
        if res.status_code != 200:
            print(res.text)
    except Exception as e:
        print(f"Dashboard error: {e}")

if __name__ == "__main__":
    test_workflow()
