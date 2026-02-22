import httpx
import time

def test_workflow():
    base_url = "http://127.0.0.1:8000/api"
    file_path = "audit_stress_test_high_scale.csv"
    
    # 1. Upload
    print(f"Uploading file: {file_path}...")
    with open(file_path, "rb") as f:
        files = {"file": f}
        start = time.time()
        res = httpx.post(f"{base_url}/upload", files=files, timeout=300)
        print(f"Upload took {time.time()-start:.2f}s")
        print("Upload status:", res.status_code)
        if res.status_code != 200:
            print("Upload failed:", res.text)
            return
        
        file_id = res.json()["file_id"]
        print(f"Upload successful. File ID: {file_id}")

if __name__ == "__main__":
    test_workflow()
