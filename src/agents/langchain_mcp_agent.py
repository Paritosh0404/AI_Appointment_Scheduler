
"""
LangChain Agent with MCP Integration
Hospital Appointment Scheduler using LangChain and MCP tools
"""
import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# LangChain imports
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage

# MCP imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)

class HospitalSchedulerAgent:
    """
    LangChain agent that uses MCP tools for hospital appointment scheduling
    """
    
    def __init__(self):
        self.llm = None
        self.agent = None
        self.mcp_client = None
        self.tools = []
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Configuration
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.mcp_server_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "mcp", "mcp_server_proper.py")
        )
        
        # Initialize components
        asyncio.create_task(self.initialize())
    
    async def initialize(self):
        """Initialize the LangChain agent with MCP tools"""
        try:
            # Initialize LLM
            if not self.google_api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")
            
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=self.google_api_key,
                temperature=0.3,
                max_tokens=1000
            )
            
            # Initialize MCP client and load tools
            await self.setup_mcp_tools()
            
            # Create the agent
            self.create_agent()
            
            logger.info("Hospital Scheduler Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            raise
    
    async def setup_mcp_tools(self):
        """Setup MCP client and load tools from the hospital scheduler MCP server"""
        try:
            # Create MCP client for the hospital scheduler server
            self.mcp_client = MultiServerMCPClient({
                "hospital_scheduler": {
                    "command": "python",
                    "args": [self.mcp_server_path],
                    "transport": "stdio"
                }
            })
            
            # Load tools from MCP server
            self.tools = await self.mcp_client.get_tools()
            
            logger.info(f"Loaded {len(self.tools)} MCP tools")
            
            # Log available tools
            for tool in self.tools:
                logger.info(f"Available tool: {tool.name} - {tool.description}")
                
        except Exception as e:
            logger.error(f"Failed to setup MCP tools: {str(e)}")
            # Fallback to empty tools list
            self.tools = []
    
    def create_agent(self):
        """Create the LangChain ReAct agent with MCP tools"""
        try:
            # Create custom prompt for hospital scheduling
            prompt_template = """
            You are a helpful hospital appointment scheduling assistant. You have access to various tools 
            to help patients schedule, modify, and manage their medical appointments.
            
            Your capabilities include:
            - Scheduling new appointments
            - Checking doctor availability
            - Getting patient appointment history
            - Sending email and WhatsApp notifications
            - Creating dynamic alerts for appointment changes
            - Providing smart appointment recommendations
            
            Always be professional, empathetic, and helpful. When scheduling appointments, make sure to:
            1. Collect all necessary patient information
            2. Check doctor availability before confirming
            3. Send appropriate confirmations
            4. Handle any conflicts gracefully
            
            Use the following format:
            
            Question: the input question you must answer
            Thought: you should always think about what to do
            Action: the action to take, should be one of [{tool_names}]
            Action Input: the input to the action
            Observation: the result of the action
            ... (this Thought/Action/Action Input/Observation can repeat N times)
            Thought: I now know the final answer
            Final Answer: the final answer to the original input question
            
            These are the tools you can use:
            {tools}
            
            Begin!
            
            Question: {input}
            Thought: {agent_scratchpad}
            """
            
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["input", "agent_scratchpad", "tools"],
                partial_variables={
                    "tool_names": ", ".join([tool.name for tool in self.tools])
                }
            )
            
            # Create the ReAct agent
            self.agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # Create agent executor
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                max_iterations=10,
                handle_parsing_errors=True
            )
            logger.info("LangChain agent created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create agent: {str(e)}")
            raise
    
    async def process_request(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user request using the LangChain agent with MCP tools
        
        Args:
            user_input: User's natural language input
            context: Additional context information
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            if not self.agent_executor:
                await self.initialize()
            
            # Add context to the input if provided
            if context:
                enhanced_input = f"Context: {json.dumps(context)}\n\nUser Request: {user_input}"
            else:
                enhanced_input = user_input
            
            # Execute the agent
            result = await self.agent_executor.ainvoke({
                "input": enhanced_input,
                "tools": self.tools # Pass tools explicitly
            })
            
            return {
                "success": True,
                "response": result["output"],
                "intermediate_steps": result.get("intermediate_steps", []),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error while processing your request. Please try again or contact support.",
                "timestamp": datetime.now().isoformat()
            }
    
    async def schedule_appointment_flow(self, patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specialized flow for appointment scheduling
        
        Args:
            patient_info: Dictionary with patient information
            
        Returns:
            Appointment scheduling result
        """
        try:
            # Construct natural language request
            request = f"""
            Please schedule an appointment for the following patient:
            
            Patient Name: {patient_info.get("name", "")}
            Phone: {patient_info.get("phone", "")}
            Email: {patient_info.get("email", "")}
            Preferred Department: {patient_info.get("department", "")}
            Preferred Doctor: {patient_info.get("doctor", "any available")}
            Preferred Date: {patient_info.get("date", "any available")}
            Preferred Time: {patient_info.get("time", "any available")}
            Notes: {patient_info.get("notes", "")}
            
            Please check availability, schedule the appointment, and send appropriate confirmations.
            """
            
            return await self.process_request(request)
            
        except Exception as e:
            logger.error(f"Error in appointment scheduling flow: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def handle_appointment_change(self, change_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle appointment changes and send dynamic alerts
        
        Args:
            change_info: Dictionary with change information
            
        Returns:
            Change handling result
        """
        try:
            change_type = change_info.get("type", "unknown")
            appointment_id = change_info.get("appointment_id", "")
            
            if change_type == "doctor_late":
                request = f"""
                Create a dynamic alert for appointment {appointment_id}. 
                The doctor is running {change_info.get("delay", "30 minutes")} late.
                Send appropriate notifications to the patient via email and WhatsApp.
                """
            elif change_type == "postponed":
                request = f"""
                Create a dynamic alert for appointment {appointment_id}.
                The appointment has been postponed to {change_info.get("new_time", "TBD")}.
                Send appropriate notifications to the patient and provide rescheduling options.
                """
            elif change_type == "cancelled":
                request = f"""
                Create a dynamic alert for appointment {appointment_id}.
                The appointment has been cancelled due to {change_info.get("reason", "unforeseen circumstances")}.
                Send appropriate notifications and help the patient reschedule.
                """
            else:
                request = f"""
                Handle appointment change for {appointment_id}: {change_info.get("message", "")}
                Send appropriate notifications to the patient.
                """
            
            return await self.process_request(request)
            
        except Exception as e:
            logger.error(f"Error handling appointment change: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_smart_recommendations(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get smart appointment recommendations
        
        Args:
            preferences: Patient preferences and requirements
            
        Returns:
            Smart recommendations
        """
        try:
            request = f"""
            Please provide smart appointment recommendations based on:
            
            Department: {preferences.get("department", "")}
            Preferred Date: {preferences.get("preferred_date", "")}
            Preferred Time: {preferences.get("preferred_time", "")}
            Patient History: {preferences.get("patient_history", "")}
            Special Requirements: {preferences.get("special_requirements", "")}
            
            Consider doctor availability, patient preferences, and optimal scheduling.
            """
            
            return await self.process_request(request)
            
        except Exception as e:
            logger.error(f"Error getting smart recommendations: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_voice_input(self, voice_text: str, conversation_id: str = None) -> Dict[str, Any]:
        """
        Process voice input with conversation context
        
        Args:
            voice_text: Transcribed voice input
            conversation_id: ID for conversation continuity
            
        Returns:
            Voice processing result
        """
        try:
            # Add conversation context
            context = {
                "input_type": "voice",
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Process with enhanced context for voice interaction
            enhanced_input = f"""
            Voice Input: {voice_text}
            
            Please respond in a conversational manner suitable for voice interaction.
            Keep responses concise and clear for text-to-speech conversion.
            If you need additional information, ask one question at a time.
            """
            
            result = await self.process_request(enhanced_input, context)
            
            # Enhance result for voice response
            if result["success"]:
                result["voice_response"] = self.format_for_voice(result["response"])
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing voice input: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "voice_response": "I'm sorry, I couldn't process your request. Please try again."
            }
    
    def format_for_voice(self, text: str) -> str:
        """
        Format text response for voice output
        
        Args:
            text: Original text response
            
        Returns:
            Voice-optimized text
        """
        # Remove markdown formatting
        voice_text = text.replace("**", "").replace("*", "")
        
        # Replace abbreviations with full words
        replacements = {
            "Dr.": "Doctor",
            "Mr.": "Mister",
            "Mrs.": "Missus",
            "Ms.": "Miss",
            "&": "and",
            "@": "at"
        }
        
        for abbrev, full in replacements.items():
            voice_text = voice_text.replace(abbrev, full)
        
        # Ensure proper pauses
        voice_text = voice_text.replace(". ", ". ... ")
        voice_text = voice_text.replace("? ", "? ... ")
        voice_text = voice_text.replace("! ", "! ... ")
        
        return voice_text
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.mcp_client:
                await self.mcp_client.close()
            logger.info("Agent cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

# Global agent instance
_agent_instance = None

async def get_hospital_agent() -> HospitalSchedulerAgent:
    """Get or create the global hospital scheduler agent instance"""
    global _agent_instance
    
    if _agent_instance is None:
        _agent_instance = HospitalSchedulerAgent()
        await _agent_instance.initialize()
    
    return _agent_instance

# Convenience functions for Flask integration
async def process_appointment_request(user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Process appointment request using the hospital agent"""
    agent = await get_hospital_agent()
    return await agent.process_request(user_input, context)

async def schedule_appointment(patient_info: Dict[str, Any]) -> Dict[str, Any]:
    """Schedule appointment using the hospital agent"""
    agent = await get_hospital_agent()
    return await agent.schedule_appointment_flow(patient_info)

async def handle_voice_request(audio_data: Optional[bytes] = None, user_text: Optional[str] = None, conversation_id: str = None) -> Dict[str, Any]:
    """Handle voice request"""
    agent = await get_hospital_agent()
    return await agent.process_voice_input(user_text, conversation_id)


