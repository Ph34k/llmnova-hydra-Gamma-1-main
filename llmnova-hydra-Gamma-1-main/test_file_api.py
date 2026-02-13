import sys
import os
import shutil
from fastapi.testclient import TestClient

# Add current directory to path so we can import gamma_server
sys.path.append(os.getcwd())

from gamma_server import app, FILE_STORAGE_PATH

client = TestClient(app)

def test_file_operations():
    session_id = "test_session_123"
    # clean up before test
    session_dir = os.path.join(FILE_STORAGE_PATH, session_id)
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)

    print("Testing Write File...")
    # 1. Write File
    response = client.post(f"/api/files/write/{session_id}", json={
        "path": "test.txt",
        "content": "Hello World"
    })
    print("Write response:", response.json())
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    print("Testing Read File...")
    # 2. Read File
    response = client.get(f"/api/files/read/{session_id}?path=test.txt")
    print("Read response:", response.json())
    assert response.status_code == 200
    assert response.json()["content"] == "Hello World"

    print("Testing List Files...")
    # 3. List Files
    response = client.get(f"/api/files/list/{session_id}")
    print("List response:", response.json())
    assert response.status_code == 200
    files = response.json()
    assert len(files) == 1
    assert files[0]["name"] == "test.txt"

    print("Testing Nested Files...")
    # 4. Nested File
    client.post(f"/api/files/write/{session_id}", json={
        "path": "src/main.py",
        "content": "print('hello')"
    })

    response = client.get(f"/api/files/list/{session_id}")
    print("List Recursive response:", response.json())
    files = response.json()
    # Expect 'src' folder and 'test.txt' file.
    # 'src' should have children.
    src_folder = next((f for f in files if f["name"] == "src"), None)
    assert src_folder is not None
    assert src_folder["type"] == "directory"
    assert len(src_folder["children"]) == 1
    assert src_folder["children"][0]["name"] == "main.py"

    print("All tests passed!")

    # Cleanup
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)

if __name__ == "__main__":
    test_file_operations()
