import pytest
from fastapi.testclient import TestClient
from main import app
import httpx
import asyncio

client = TestClient(app)

def test_root_endpoint():
    """Test 1: Root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "AWS Containerized Microservice is running" in response.json()["message"]

def test_health_check():
    """Test 2: Health check returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "todo-api"

def test_create_and_get_todo():
    """Test 3: Create a todo and retrieve it."""
    todo_data = {
        "title": "Learn AWS ECS",
        "description": "Deploy containerized microservice to AWS",
        "completed": False
    }
    
    # Create
    create_response = client.post("/todos", json=todo_data)
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["title"] == todo_data["title"]
    assert created["id"] is not None
    
    # Get by ID
    get_response = client.get(f"/todos/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == todo_data["title"]

def test_todo_lifecycle():
    """Test 4: Full CRUD lifecycle with update and delete."""
    # Create
    todo = {"title": "Test CRUD", "description": "Lifecycle test"}
    create_res = client.post("/todos", json=todo)
    assert create_res.status_code == 200
    todo_id = create_res.json()["id"]
    
    # Update
    update_data = {"title": "Updated Title", "completed": True}
    update_res = client.put(f"/todos/{todo_id}", json=update_data)
    assert update_res.status_code == 200
    assert update_res.json()["completed"] is True
    assert update_res.json()["title"] == "Updated Title"
    
    # Delete
    delete_res = client.delete(f"/todos/{todo_id}")
    assert delete_res.status_code == 200
    
    # Verify gone
    get_res = client.get(f"/todos/{todo_id}")
    assert get_res.status_code == 404

@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test 5: Service handles concurrent requests (simulating load)."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as async_client:
        tasks = [
            async_client.get("/health"),
            async_client.get("/"),
            async_client.post("/todos", json={"title": "Concurrent task"})
        ]
        responses = await asyncio.gather(*tasks)
        
        for r in responses:
            assert r.status_code in (200, 201)
