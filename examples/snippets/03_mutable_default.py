from datetime import datetime


class EventLog:
    def __init__(self, name: str, events: list[str] = []):
        self.name = name
        self.events = events

    def record(self, message: str) -> None:
        timestamp = datetime.now().isoformat(timespec="seconds")
        self.events.append(f"{timestamp} {message}")

    def dump(self) -> str:
        return "\n".join(self.events)
