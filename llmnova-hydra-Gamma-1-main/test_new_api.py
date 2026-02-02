
import sys
import os
import shutil
from fastapi.testclient import TestClient

# Add current directory to path so we can import gamma_server
sys.path.append(os.getcwd())

from gamma_server import app, FILE_STORAGE_PATH
from test_file_api import test_file_operations, client

def test_new_endpoints():
    print("\nTesting New Endpoints...")

    print("Testing Scheduler Jobs...")
    response = client.get("/api/scheduler/jobs")
    print("Jobs response:", response.json())
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    print("Testing WebDev Servers...")
    response = client.get("/api/webdev/servers")
    print("Servers response:", response.json())
    assert response.status_code == 200
    assert len(response.json()) == 2

    print("Testing System Status...")
    response = client.get("/api/system/status")
    print("Status response:", response.json())
    assert response.status_code == 200
    assert "cpu_percent" in response.json()

    print("Testing List Sessions...")
    response = client.get("/api/sessions")
    print("Sessions response:", response.json())
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    print("Testing List Tools...")
    response = client.get("/api/tools")
    # print("Tools response:", response.json()) # Too verbose
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

    print("New Endpoint Tests Passed!")

if __name__ == "__main__":
    test_file_operations()
    test_new_endpoints()
