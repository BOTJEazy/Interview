# Import sys module for modifying Python's runtime environment
import sys

# Import os module for interacting with the operating system
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app instance from the main app file
from config import TASKS_ENDPOINT
from app import app, tasks
from notification_consumer import NotificationConsumer, NOTIFICATION_QUEUE

# Import pytest for writing and running tests
import pytest
import json

notification_thread = None


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_task_get(client):
    """Test task get."""
    response = client.get(TASKS_ENDPOINT)
    assert response.status_code == 200
    assert response.json == tasks


def test_task_post(client):
    """Test task creation."""
    task_added = {"title": "Pay Bills 2", "completed": False, "due_date": "2024-03-31"}
    response = client.post(
        TASKS_ENDPOINT,
        data=json.dumps(task_added),
        content_type="application/json",
    )
    assert response.status_code == 201

    response = client.get(TASKS_ENDPOINT)
    assert response.status_code == 200
    assert any(
        task_added.items() <= task.items() for task in response.json
    )  # Check if there is a task that contains the information of the new task 'subset operation'


def test_task_update(client):
    """Test task update."""
    task_to_update = tasks[0].copy()
    update = {"title": "Pay Bills 3"}

    response = client.put(
        f"/api/tasks/{task_to_update['id']}",
        data=json.dumps(update),
        content_type="application/json",
    )

    assert response.status_code == 200
    task_to_update.update(update)
    assert response.json == task_to_update
    assert not NOTIFICATION_QUEUE.empty()  # Notification in the queue

    response = client.get(TASKS_ENDPOINT)
    assert response.status_code == 200

    assert any(task == task_to_update for task in response.json)


def test_task_delete(client):
    """Test task delete."""
    task_to_delete = tasks[0]

    response = client.delete(
        f"/api/tasks/{task_to_delete['id']}",
    )
    assert response.status_code == 204

    response = client.get(TASKS_ENDPOINT)
    assert response.status_code == 200

    assert not any(task == task_to_delete for task in response.json)
