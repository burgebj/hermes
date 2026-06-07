"""Base class for gateway background services."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ServiceEvent:
    """Event from a background service."""
    service: str
    notification_id: int
    app: str
    object_type: str
    object_id: str
    subject: str
    message: str
    link: str
    sender: str
    timestamp: str
    action: str  # "react" or "silent"
    raw: dict = field(default_factory=dict)


class BaseService(ABC):
    """Background service that listens for events and routes them."""

    name: str = "base"

    def __init__(self, config: dict):
        self.config = config
        self.gateway_runner = None  # set by GatewayRunner after creation

    @abstractmethod
    async def start(self) -> bool:
        """Start background tasks. Returns True on success."""

    @abstractmethod
    async def stop(self):
        """Clean shutdown — cancel tasks, close connections."""

    @abstractmethod
    async def on_event(self, event: ServiceEvent):
        """Process a single event."""
