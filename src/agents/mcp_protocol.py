"""
Model Context Protocol (MCP) Implementation for Multi-Agent Communication
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"

class AgentType(Enum):
    APPOINTMENT_MANAGER = "appointment_manager"
    DOCTOR_AVAILABILITY = "doctor_availability"
    PATIENT_INFO = "patient_info"
    NOTIFICATION = "notification"
    UI_VOICE = "ui_voice"
    COORDINATOR = "coordinator"

@dataclass
class MCPMessage:
    """Standard MCP message format for inter-agent communication"""
    message_id: str
    context_id: str
    sender_id: str
    receiver_id: str
    message_type: MessageType
    timestamp: str
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)

class MCPContext:
    """Manages conversation context across agents"""
    
    def __init__(self):
        self.contexts: Dict[str, Dict[str, Any]] = {}
    
    def create_context(self, user_id: str, initial_data: Dict[str, Any] = None) -> str:
        context_id = str(uuid.uuid4())
        self.contexts[context_id] = {
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'data': initial_data or {},
            'conversation_history': []
        }
        return context_id
    
    def update_context(self, context_id: str, key: str, value: Any):
        if context_id in self.contexts:
            self.contexts[context_id]['data'][key] = value
    
    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        return self.contexts.get(context_id)
    
    def add_to_history(self, context_id: str, message: MCPMessage):
        if context_id in self.contexts:
            self.contexts[context_id]['conversation_history'].append(message.to_dict())

class MCPAgent:
    """Base class for all MCP-enabled agents"""
    
    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.context_manager = MCPContext()
        self.message_handlers = {}
    
    def create_message(self, 
                      context_id: str,
                      receiver_id: str,
                      message_type: MessageType,
                      payload: Dict[str, Any],
                      correlation_id: Optional[str] = None) -> MCPMessage:
        """Create a standardized MCP message"""
        return MCPMessage(
            message_id=str(uuid.uuid4()),
            context_id=context_id,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            timestamp=datetime.utcnow().isoformat(),
            payload=payload,
            correlation_id=correlation_id
        )
    
    def register_handler(self, message_type: str, handler_func):
        """Register a handler function for specific message types"""
        self.message_handlers[message_type] = handler_func
    
    def process_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Process incoming message and return response if needed"""
        # Add to conversation history
        self.context_manager.add_to_history(message.context_id, message)
        
        # Find appropriate handler
        handler_key = f"{message.message_type.value}_{message.payload.get('action', 'default')}"
        handler = self.message_handlers.get(handler_key)
        
        if handler:
            return handler(message)
        else:
            # Return error message for unhandled requests
            if message.message_type == MessageType.REQUEST:
                return self.create_message(
                    context_id=message.context_id,
                    receiver_id=message.sender_id,
                    message_type=MessageType.ERROR,
                    payload={
                        'error': 'UNHANDLED_REQUEST',
                        'message': f'No handler found for action: {message.payload.get("action")}'
                    },
                    correlation_id=message.message_id
                )
        return None

class MCPMessageBus:
    """Central message bus for routing messages between agents"""
    
    def __init__(self):
        self.agents: Dict[str, MCPAgent] = {}
        self.message_queue: List[MCPMessage] = []
    
    def register_agent(self, agent: MCPAgent):
        """Register an agent with the message bus"""
        self.agents[agent.agent_id] = agent
    
    def send_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Send message to target agent and return response if any"""
        target_agent = self.agents.get(message.receiver_id)
        if target_agent:
            return target_agent.process_message(message)
        else:
            # Return error for unknown receiver
            return MCPMessage(
                message_id=str(uuid.uuid4()),
                context_id=message.context_id,
                sender_id="message_bus",
                receiver_id=message.sender_id,
                message_type=MessageType.ERROR,
                timestamp=datetime.utcnow().isoformat(),
                payload={
                    'error': 'UNKNOWN_RECEIVER',
                    'message': f'Agent {message.receiver_id} not found'
                },
                correlation_id=message.message_id
            )
    
    def broadcast_message(self, message: MCPMessage, exclude_sender: bool = True):
        """Broadcast message to all registered agents"""
        responses = []
        for agent_id, agent in self.agents.items():
            if exclude_sender and agent_id == message.sender_id:
                continue
            response = agent.process_message(message)
            if response:
                responses.append(response)
        return responses

# Global message bus instance
message_bus = MCPMessageBus()

