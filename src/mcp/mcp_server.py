"""
Model Context Protocol (MCP) Server Implementation
Provides the communication backbone for multi-agent hospital appointment system
"""
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPMessageType(Enum):
    """MCP message types following JSON-RPC 2.0 specification"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"

class MCPResourceType(Enum):
    """Types of resources that can be exposed via MCP"""
    TOOL = "tool"
    PROMPT = "prompt"
    RESOURCE = "resource"

@dataclass
class MCPMessage:
    """Standard MCP message structure"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class MCPTool:
    """MCP tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable

@dataclass
class MCPResource:
    """MCP resource definition"""
    uri: str
    name: str
    description: str
    mime_type: str
    content: Any

@dataclass
class MCPPrompt:
    """MCP prompt definition"""
    name: str
    description: str
    arguments: List[Dict[str, Any]]
    template: str

class MCPAgent:
    """Base class for MCP agents"""
    
    def __init__(self, agent_id: str, name: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.prompts: Dict[str, MCPPrompt] = {}
        self.context: Dict[str, Any] = {}
        
    def register_tool(self, tool: MCPTool):
        """Register a tool with this agent"""
        self.tools[tool.name] = tool
        logger.info(f"Agent {self.agent_id} registered tool: {tool.name}")
        
    def register_resource(self, resource: MCPResource):
        """Register a resource with this agent"""
        self.resources[resource.uri] = resource
        logger.info(f"Agent {self.agent_id} registered resource: {resource.uri}")
        
    def register_prompt(self, prompt: MCPPrompt):
        """Register a prompt with this agent"""
        self.prompts[prompt.name] = prompt
        logger.info(f"Agent {self.agent_id} registered prompt: {prompt.name}")
        
    async def handle_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Handle tool invocation"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found in agent {self.agent_id}")
        
        tool = self.tools[tool_name]
        try:
            result = await tool.handler(**params)
            logger.info(f"Tool {tool_name} executed successfully by agent {self.agent_id}")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name} in agent {self.agent_id}: {str(e)}")
            raise

class MCPServer:
    """Central MCP server for managing agent communication"""
    
    def __init__(self):
        self.agents: Dict[str, MCPAgent] = {}
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.setup_core_handlers()
        
    def setup_core_handlers(self):
        """Setup core MCP message handlers"""
        self.message_handlers.update({
            "initialize": self.handle_initialize,
            "list_tools": self.handle_list_tools,
            "list_resources": self.handle_list_resources,
            "list_prompts": self.handle_list_prompts,
            "call_tool": self.handle_call_tool,
            "get_resource": self.handle_get_resource,
            "get_prompt": self.handle_get_prompt,
            "register_agent": self.handle_register_agent,
            "send_message": self.handle_send_message,
            "get_context": self.handle_get_context,
            "update_context": self.handle_update_context
        })
        
    def register_agent(self, agent: MCPAgent):
        """Register an agent with the MCP server"""
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_id} ({agent.name})")
        
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP message"""
        try:
            mcp_message = MCPMessage(**message)
            
            if mcp_message.method in self.message_handlers:
                handler = self.message_handlers[mcp_message.method]
                result = await handler(mcp_message.params or {})
                
                response = MCPMessage(
                    id=mcp_message.id,
                    result=result
                )
                return response.to_dict()
            else:
                error_response = MCPMessage(
                    id=mcp_message.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {mcp_message.method}"
                    }
                )
                return error_response.to_dict()
                
        except Exception as e:
            logger.error(f"Error handling MCP message: {str(e)}")
            error_response = MCPMessage(
                id=message.get("id"),
                error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            )
            return error_response.to_dict()
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialization"""
        return {
            "protocol_version": "2024-11-05",
            "capabilities": {
                "tools": {"list_changed": True},
                "resources": {"subscribe": True, "list_changed": True},
                "prompts": {"list_changed": True},
                "logging": {}
            },
            "server_info": {
                "name": "Hospital Appointment Scheduler MCP Server",
                "version": "1.0.0"
            }
        }
    
    async def handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all available tools across agents"""
        tools = []
        for agent in self.agents.values():
            for tool_name, tool in agent.tools.items():
                tools.append({
                    "name": f"{agent.agent_id}.{tool_name}",
                    "description": tool.description,
                    "inputSchema": tool.input_schema
                })
        
        return {"tools": tools}
    
    async def handle_list_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all available resources across agents"""
        resources = []
        for agent in self.agents.values():
            for resource_uri, resource in agent.resources.items():
                resources.append({
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mimeType": resource.mime_type
                })
        
        return {"resources": resources}
    
    async def handle_list_prompts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all available prompts across agents"""
        prompts = []
        for agent in self.agents.values():
            for prompt_name, prompt in agent.prompts.items():
                prompts.append({
                    "name": f"{agent.agent_id}.{prompt_name}",
                    "description": prompt.description,
                    "arguments": prompt.arguments
                })
        
        return {"prompts": prompts}
    
    async def handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool invocation"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise ValueError("Tool name is required")
        
        # Parse agent_id and tool_name
        if "." in tool_name:
            agent_id, actual_tool_name = tool_name.split(".", 1)
        else:
            raise ValueError("Tool name must be in format 'agent_id.tool_name'")
        
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent = self.agents[agent_id]
        result = await agent.handle_tool_call(actual_tool_name, arguments)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result) if not isinstance(result, str) else result
                }
            ]
        }
    
    async def handle_get_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get resource content"""
        uri = params.get("uri")
        
        if not uri:
            raise ValueError("Resource URI is required")
        
        for agent in self.agents.values():
            if uri in agent.resources:
                resource = agent.resources[uri]
                return {
                    "contents": [
                        {
                            "uri": resource.uri,
                            "mimeType": resource.mime_type,
                            "text": resource.content if isinstance(resource.content, str) else json.dumps(resource.content)
                        }
                    ]
                }
        
        raise ValueError(f"Resource {uri} not found")
    
    async def handle_get_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get prompt template"""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not prompt_name:
            raise ValueError("Prompt name is required")
        
        # Parse agent_id and prompt_name
        if "." in prompt_name:
            agent_id, actual_prompt_name = prompt_name.split(".", 1)
        else:
            raise ValueError("Prompt name must be in format 'agent_id.prompt_name'")
        
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent = self.agents[agent_id]
        if actual_prompt_name not in agent.prompts:
            raise ValueError(f"Prompt {actual_prompt_name} not found in agent {agent_id}")
        
        prompt = agent.prompts[actual_prompt_name]
        
        # Simple template substitution
        template = prompt.template
        for key, value in arguments.items():
            template = template.replace(f"{{{key}}}", str(value))
        
        return {
            "description": prompt.description,
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": template
                    }
                }
            ]
        }
    
    async def handle_register_agent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent registration"""
        agent_id = params.get("agent_id")
        name = params.get("name")
        description = params.get("description")
        
        if not all([agent_id, name, description]):
            raise ValueError("agent_id, name, and description are required")
        
        agent = MCPAgent(agent_id, name, description)
        self.register_agent(agent)
        
        return {"status": "registered", "agent_id": agent_id}
    
    async def handle_send_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle inter-agent messaging"""
        from_agent = params.get("from_agent")
        to_agent = params.get("to_agent")
        message = params.get("message")
        conversation_id = params.get("conversation_id", str(uuid.uuid4()))
        
        if not all([from_agent, to_agent, message]):
            raise ValueError("from_agent, to_agent, and message are required")
        
        # Store message in conversation history
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "id": conversation_id,
                "participants": [from_agent, to_agent],
                "messages": [],
                "created_at": datetime.now().isoformat()
            }
        
        self.conversations[conversation_id]["messages"].append({
            "from": from_agent,
            "to": to_agent,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "status": "sent",
            "conversation_id": conversation_id,
            "message_id": str(uuid.uuid4())
        }
    
    async def handle_get_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get conversation context"""
        conversation_id = params.get("conversation_id")
        
        if not conversation_id:
            raise ValueError("conversation_id is required")
        
        if conversation_id not in self.conversations:
            return {"context": None}
        
        return {"context": self.conversations[conversation_id]}
    
    async def handle_update_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update conversation context"""
        conversation_id = params.get("conversation_id")
        context_update = params.get("context_update", {})
        
        if not conversation_id:
            raise ValueError("conversation_id is required")
        
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "id": conversation_id,
                "participants": [],
                "messages": [],
                "created_at": datetime.now().isoformat()
            }
        
        # Update context with new information
        self.conversations[conversation_id].update(context_update)
        self.conversations[conversation_id]["updated_at"] = datetime.now().isoformat()
        
        return {"status": "updated", "conversation_id": conversation_id}

# Global MCP server instance
mcp_server = MCPServer()

def get_mcp_server() -> MCPServer:
    """Get the global MCP server instance"""
    return mcp_server

