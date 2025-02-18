## Interview Task Readme

### Asynchronous Notification

Based on a thread safe Queue (Could use Redis here) and NotificationConsumer based on threading python library

```file: notification_consumer.py```

### RxJS Integration (Conceptual)

Using SSE for it's simplicity and reliability in comparison with Websockets and we don't really need the bi-directional communication in this task since we are just listening to updates and other parts are handled by standard http requests. We could also used a separate library for handling SSE like flask_sse.

Added a PoC backend implementation based on thread safe in memory list (that part would usualy be handled by something like Redis along with it's subscription model)

```endpoint: /api/task-updates function: stream```

### Tests

Available by running ```pytest``` for each of the tasks endpoints