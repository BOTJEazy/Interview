import threading
import time

from queue import Queue, Empty

from notifications import send_notification

NOTIFICATION_QUEUE = (
    Queue()
)  # Would normaly use a db like redis to not lose tasks every restart


class NotificationConsumer(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()
        self.processing_task = False

    def stop(self) -> None:
        self._stop_event.set()

    def _stopped(self) -> bool:
        return self._stop_event.is_set()

    def startup(self) -> None:
        print("NotificationConsumer started")

    def shutdown(self) -> None:
        print("NotificationConsumer stopped")

    def handle(self) -> None:
        try:
            self.processing_task = True
            task = NOTIFICATION_QUEUE.get(block=False)
            send_notification(task)
        except Empty:
            self.processing_task = False
            time.sleep(1)

    def run(self) -> None:
        self.startup()
        while not self._stopped():
            self.handle()
        self.shutdown()
