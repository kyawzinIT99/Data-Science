import httpx
import time

def test_chat():
    base_url = "http://127.0.0.1:8000/api"
    # Assuming this file exists from earlier:
    file_id = "13e3f90d-cbfb-4ef9-9ad0-f225ec54e441"
    
    print(f"Chatting with file: {file_id}...")
    start = time.time()
    try:
        res = httpx.post(
            f"{base_url}/chat", 
            json={
                "file_id": file_id,
                "question": "what will be predicted in the next three months regarding this data",
                "chat_history": []
            },
            timeout=300
        )
        print(f"Chat took {time.time()-start:.2f}s")
        print("Chat status:", res.status_code)
        if res.status_code != 200:
            print("Chat failed:", res.text)
        else:
            print("Chat Response:", res.json())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat()
