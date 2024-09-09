from PyQt5.QtCore import QObject, pyqtSignal
from collections import defaultdict
from typing import Callable


class EventEmitter(QObject):
    signal = pyqtSignal(str, tuple, dict)


class EventBus(QObject):
    def __init__(self):
        super().__init__()
        self._subscribers = defaultdict(list)
        self._emitter = EventEmitter()
        self._emitter.signal.connect(self._process_event)

    def subscribe(self, event_type: str, callback: Callable):
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb != callback
            ]

    def emit(self, event_type: str, *args, **kwargs):
        # Emit the signal, which will be processed on the main thread
        self._emitter.signal.emit(event_type, args, kwargs)

    def _process_event(self, event_type: str, args: tuple, kwargs: dict):
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                callback(*args, **kwargs)
