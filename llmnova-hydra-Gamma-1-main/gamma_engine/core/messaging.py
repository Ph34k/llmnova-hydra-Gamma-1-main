"""Event-based messaging system for the Gamma Engine.

This module implements a Publish/Subscribe pattern to decouple components
within the engine, allowing for loose integration between agents, tools,
and the UI.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Enumeration of standard message types in the system."""
    TEXT = "text"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SYSTEM = "system"
    ERROR = "error"
    STATUS = "status"  # e.g. "thinking", "ready"
    PLAN = "plan"      # Plan updates

class Message(BaseModel):
    """Represents a standard message envelope in the event bus.
    
    Attributes:
        type: The type of the message (from MessageType).
        content: The primary payload of the message.
        sender: Information about who sent the message.
        metadata: Arbitrary additional data.
        timestamp: When the message was created.
    """
    type: MessageType
    content: Any
    sender: str = "system"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

class MessageBus:
    """Central event bus for the application.
    
    Manages subscriptions and publishes messages to interested listeners.
    Supports topic-based filtering via simple string matching or type checking.
    
    Attributes:
        subscribers: Dictionary mapping message types to callback functions.
        
    Examples:
        >>> bus = MessageBus()
        >>> def on_message(msg):
        ...     print(f"Received: {msg.content}")
        >>> bus.subscribe(MessageType.TEXT, on_message)
        >>> bus.publish(Message(type=MessageType.TEXT, content="Hello"))
    """
    
    def __init__(self):
        """Initialize the MessageBus."""
        self.subscribers: Dict[MessageType, List[Callable[[Message], None]]] = {}
        self.all_listeners: List[Callable[[Message], None]] = []

    def subscribe(self, msg_type: Optional[MessageType], callback: Callable[[Message], None]) -> None:
        """Subscribe to messages of a specific type.
        
        Args:
            msg_type: The MessageType to listen for. If None, listens to ALL messages.
            callback: The function to call when a message arrives.
        """
        if msg_type is None:
            self.all_listeners.append(callback)
        else:
            if msg_type not in self.subscribers:
                self.subscribers[msg_type] = []
            self.subscribers[msg_type].append(callback)

    def publish(self, message: Message) -> None:
        """Publish a message to all subscribers.
        
        Args:
            message: The Message object to distribute.
        """
        # Notify specific listeners
        if message.type in self.subscribers:
            for callback in self.subscribers[message.type]:
                try:
                    callback(message)
                except Exception as e:
                    print(f"Error in subscriber callback: {e}")

        # Notify global listeners
        for callback in self.all_listeners:
            try:
                callback(message)
            except Exception as e:
                print(f"Error in global listener callback: {e}")
