"""
Real-time event streaming for agent graph visualization.

Emits events during agent execution to enable real-time visualization
of the agent's thinking process, tool execution, and results.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Optional, List


class EventType(str, Enum):
    """Types of events that can be streamed"""

    AGENT_START = "agent_start"
    AGENT_END = "agent_end"

    NODE_START = "node_start"
    NODE_END = "node_end"
    NODE_ERROR = "node_error"

    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    TOOL_ERROR = "tool_error"

    THINKING = "thinking"
    REASONING = "reasoning"

    STATE_UPDATE = "state_update"
    VALIDATION_RESULT = "validation_result"

    ANALYSIS_COMPLETE = "analysis_complete"


@dataclass
class AgentEvent:
    """Represents a single event in the agent execution"""

    type: EventType
    timestamp: str
    node_name: Optional[str] = None
    tool_name: Optional[str] = None
    status: Optional[str] = None
    data: Optional[dict] = None
    error: Optional[str] = None
    progress: Optional[float] = None  # 0-1

    def to_dict(self) -> dict:
        """Convert event to dictionary for JSON serialization"""
        return {
            "type": self.type.value,
            "timestamp": self.timestamp,
            "node_name": self.node_name,
            "tool_name": self.tool_name,
            "status": self.status,
            "data": self.data,
            "error": self.error,
            "progress": self.progress,
        }

    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps(self.to_dict())


class AgentEventEmitter:
    """Manages event emission and subscription for agent execution"""

    def __init__(self):
        """Initialize the event emitter"""
        self.subscribers: List[Callable[[AgentEvent], None]] = []
        self.events_history: List[AgentEvent] = []
        self.max_history_size = 1000
        self.session_id: Optional[str] = None

    def set_session_id(self, session_id: str):
        """Set session ID for tracking"""
        self.session_id = session_id

    def subscribe(self, callback: Callable[[AgentEvent], None]):
        """Subscribe to events"""
        self.subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[AgentEvent], None]):
        """Unsubscribe from events"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    def emit(self, event: AgentEvent):
        """Emit an event to all subscribers"""
        # Add to history
        self.events_history.append(event)
        if len(self.events_history) > self.max_history_size:
            self.events_history.pop(0)

        # Notify all subscribers
        for subscriber in self.subscribers:
            try:
                subscriber(event)
            except Exception as e:
                print(f"Error in event subscriber: {e}")

    def emit_event(
        self,
        event_type: EventType,
        node_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        status: Optional[str] = None,
        data: Optional[dict] = None,
        error: Optional[str] = None,
        progress: Optional[float] = None,
    ):
        """Convenience method to emit an event"""
        event = AgentEvent(
            type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            node_name=node_name,
            tool_name=tool_name,
            status=status,
            data=data,
            error=error,
            progress=progress,
        )
        self.emit(event)

    def get_graph_visualization(self) -> dict:
        """Get visualization data for the agent graph"""
        nodes = [
            {"id": "extract_skills", "label": "Extract Skills", "status": "pending"},
            {"id": "think", "label": "Agent Think", "status": "pending"},
            {"id": "execute_tools", "label": "Execute Tools", "status": "pending"},
            {"id": "reflect", "label": "Reflect", "status": "pending"},
            {"id": "generate_plan", "label": "Generate Plan", "status": "pending"},
            {"id": "validate", "label": "Validate", "status": "pending"},
        ]

        edges = [
            {"from": "extract_skills", "to": "think"},
            {"from": "think", "to": "execute_tools"},
            {"from": "execute_tools", "to": "reflect"},
            {"from": "reflect", "to": "generate_plan"},
            {"from": "generate_plan", "to": "validate"},
        ]

        # Update node status based on events
        for event in self.events_history:
            if event.type == EventType.NODE_START:
                for node in nodes:
                    if node["id"] == event.node_name:
                        node["status"] = "processing"
            elif event.type == EventType.NODE_END:
                for node in nodes:
                    if node["id"] == event.node_name:
                        node["status"] = "completed"
            elif event.type == EventType.NODE_ERROR:
                for node in nodes:
                    if node["id"] == event.node_name:
                        node["status"] = "error"

        return {
            "nodes": nodes,
            "edges": edges,
            "session_id": self.session_id,
            "total_events": len(self.events_history),
        }

    def get_execution_timeline(self) -> List[dict]:
        """Get timeline of execution for visualization"""
        timeline = []
        for event in self.events_history:
            timeline.append(
                {
                    "timestamp": event.timestamp,
                    "type": event.type.value,
                    "node": event.node_name,
                    "tool": event.tool_name,
                    "status": event.status,
                    "data": event.data,
                }
            )
        return timeline

    def clear_history(self):
        """Clear event history"""
        self.events_history.clear()
        self.subscribers.clear()


# Global event emitter instance
event_emitter = AgentEventEmitter()


def get_event_emitter() -> AgentEventEmitter:
    """Get the global event emitter instance"""
    return event_emitter
