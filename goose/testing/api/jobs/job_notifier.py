"""Broadcast job updates to websocket subscribers."""

from __future__ import annotations

import asyncio
import threading

from goose.testing.api.jobs.models import Job


class JobNotifier:
    """Simple pub/sub broker that fans out job updates to websocket clients."""

    def __init__(self) -> None:
        self._subscribers: dict[asyncio.Queue[Job], asyncio.AbstractEventLoop] = {}
        self._lock = threading.Lock()

    def subscribe(self) -> asyncio.Queue[Job]:
        """Register a new subscriber queue tied to the current event loop."""

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Job] = asyncio.Queue()
        with self._lock:
            self._subscribers[queue] = loop
        return queue

    def unsubscribe(self, queue: asyncio.Queue[Job]) -> None:
        """Remove a subscriber queue."""

        with self._lock:
            self._subscribers.pop(queue, None)

    def publish(self, job: Job) -> None:
        """Fan-out a job update to every subscriber."""

        with self._lock:
            subscribers = list(self._subscribers.items())

        for queue, loop in subscribers:
            loop.call_soon_threadsafe(self._enqueue, queue, job)

    @staticmethod
    def _enqueue(queue: asyncio.Queue[Job], job: Job) -> None:
        """Attempt to enqueue *job* for a subscriber, dropping if the loop is gone."""

        try:
            queue.put_nowait(job)
        except (asyncio.QueueFull, RuntimeError):
            # Drop the update if the subscriber is overwhelmed or already disconnected.
            pass


__all__ = ["JobNotifier"]
