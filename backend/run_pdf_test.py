import httpx
import time
import os

def check_pdf():
    base_url = "http://127.0.0.1:8000/api"
    file_id = "13e3f90d-cbfb-4ef9-9ad0-f225ec54e441"
    
    print(f"Downloading PDF for {file_id}...")
    start = time.time()
    res = httpx.get(f"{base_url}/export/{file_id}/pdf", timeout=120)
    print(f"Time: {time.time()-start:.2f}s")
    print(f"Status: {res.status_code}")
    
    if res.status_code == 200:
        with open("test_output.pdf", "wb") as f:
            f.write(res.content)
        print(f"Saved test_output.pdf, size: {os.path.getsize('test_output.pdf')} bytes")
        
        # Check first 5 bytes
        with open("test_output.pdf", "rb") as f:
            print("Header:", f.read(10))

if __name__ == "__main__":
    check_pdf()
