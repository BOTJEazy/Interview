import json
import time
import signal
import datetime

from flask import Flask, jsonify, request, Response
from collections import deque

from config import TASKS_ENDPOINT
from notification_consumer import NOTIFICATION_QUEUE, NotificationConsumer


app = Flask(__name__)
task_updates_queue = deque()  # thread safe list

tasks = [
    {
        "id": 1,
        "title": "Grocery Shopping",
        "completed": False,
        "due_date": "2024-03-15",
    },
    {"id": 2, "title": "Pay Bills", "completed": False, "due_date": "2024-03-20"},
]
next_task_id = 3  # For assigning new task IDs


@app.route(TASKS_ENDPOINT, methods=["GET"])
def get_tasks():
    return jsonify(tasks)


@app.route(TASKS_ENDPOINT, methods=["POST"])
def create_task():
    global next_task_id  # Declare as global at the start
    data = request.get_json()
    new_task = {
        "id": next_task_id,
        "title": data["title"],
        "completed": False,
        "due_date": data.get("due_date") or datetime.date.today().strftime("%Y-%m-%d"),
    }

    next_task_id += 1
    tasks.append(new_task)
    task_updates_queue.append({"type": "create", "data": new_task})

    return jsonify(new_task), 201


def new_update_notification(task):
    NOTIFICATION_QUEUE.put(f"Task updated {task}")


@app.route(f"{TASKS_ENDPOINT}/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json()
    for task in tasks:
        if task["id"] == task_id:
            task.update(data)  # Update task attributes
            new_update_notification(task)  # Add task to the queue
            task_updates_queue.append({"type": "update", "data": task})

            return jsonify(task), 200
    return jsonify({"error": "Task not found"}), 404


@app.route(f"{TASKS_ENDPOINT}/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            del tasks[i]
            task_updates_queue.append(
                {"type": "delete", "data": {"id": tasks[i]["id"]}}
            )
            return jsonify({"message": "Task deleted"}), 204
    return jsonify({"error": "Task not found"}), 404


def event_stream():
    start_update_index = len(task_updates_queue) - 1
    yield f"event: connected\ndata: {json.dumps(tasks)}\n\n"
    while True:
        try:
            tasks_updated = task_updates_queue[start_update_index + 1]
            start_update_index += 1
            yield f"event: {tasks_updated['type']}\ndata: {json.dumps(tasks_updated['data'])}\n\n"
        except IndexError:
            time.sleep(1)


@app.route("/api/task-updates", methods=["GET"])
def stream():  # a PoC with in memory list normaly we would use something like Redis to store and listen to updates
    return Response(event_stream(), content_type="text/event-stream")


if __name__ == "__main__":
    notification_thread = NotificationConsumer()

    notification_thread.start()

    def sigint_handler(signum, frame):  # stop the notification thread on signal
        original_handler = signal.getsignal(signal.SIGINT)
        notification_thread.stop()

        if notification_thread.is_alive():
            notification_thread.join()  # kill thread when done with task

        original_handler(signum, frame)

    try:
        signal.signal(signal.SIGINT, sigint_handler)  # register the signal handler
    except ValueError as e:
        print(f"{e}. Continuing execution...")

    app.run(debug=True)
