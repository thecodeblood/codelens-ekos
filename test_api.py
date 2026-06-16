import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def wait_for_server():
    for _ in range(10):
        try:
            requests.get("http://127.0.0.1:8000/docs")
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False

def main():
    if not wait_for_server():
        print("Server did not start in time.")
        sys.exit(1)
    print("Server is up!")

    # 1. Register Source
    print("Registering source...")
    resp = requests.post(f"{BASE_URL}/sources", json={
        "name": "Little Lemon Web App",
        "type": "git",
        "uri": "d:/Personal_Projects/Little_Lemon_Web_App"
    })
    
    if resp.status_code not in (200, 201, 409):
        print(f"Failed to register source: {resp.text}")
        sys.exit(1)
        
    source = resp.json()
    source_id = source["id"]
    print(f"Registered source: {source_id}")

    # 2. Trigger Ingestion
    print("Triggering ingestion...")
    resp = requests.post(f"{BASE_URL}/sources/{source_id}/ingest")
    if resp.status_code not in (200, 201):
        print(f"Failed to trigger ingestion: {resp.text}")
        sys.exit(1)
        
    run_id = resp.json()["run_id"]
    print(f"Ingestion started with run_id: {run_id}")

    # 3. Poll Status
    while True:
        resp = requests.get(f"{BASE_URL}/sources/{source_id}/status")
        if resp.status_code != 200:
            print(f"Failed to get status: {resp.text}")
            sys.exit(1)
            
        status_data = resp.json()
        status = status_data["status"]
        print(f"Ingestion status: {status} - Processed: {status_data.get('files_processed', 0)}/{status_data.get('files_total', 0)}")
        
        if status in ["completed", "failed"]:
            print(f"Ingestion finished with status: {status}")
            print(f"Stats: {status_data}")
            if status == "failed":
                sys.exit(1)
            break
        time.sleep(2)

    # 4. Query Stats
    print("\nQuerying model stats...")
    resp = requests.get(f"{BASE_URL}/model/stats")
    if resp.status_code != 200:
        print(f"Failed to get stats: {resp.text}")
        sys.exit(1)
    print("Model Stats:")
    print(resp.json())

    # 5. Search
    print("\nSearching entities...")
    query = "model"
    resp = requests.get(f"{BASE_URL}/model/search", params={"q": query})
    if resp.status_code != 200:
        print(f"Failed to search: {resp.text}")
        sys.exit(1)
    results = resp.json()
    print(f"Search results for '{query}':")
    for r in results[:5]: # just show top 5
        print(f" - {r['name']} ({r['type']}) [Confidence: {r['confidence']}]")

if __name__ == "__main__":
    main()
