"""
Retell AI Voice Service Integration with Make.ai
Hospital Appointment Scheduler with Advanced Voice Features using Retell AI
"""
import os
import json
import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.integrations.make_client import notification_agent

logger = logging.getLogger(__name__)

class RetellVoiceService:
    """
    Retell AI voice service integration for comprehensive voice assistance
    """
    
    def __init__(self):
        self.api_key = os.getenv("RETELL_API_KEY", "")
        self.agent_id = os.getenv("RETELL_AGENT_ID", "")
        self.base_url = "https://api.retellai.com/v2"
        self.conversation_history = []
        
        # Validate configuration
        if not self.api_key:
            logger.warning("RETELL_API_KEY not configured")
        if not self.agent_id:
            logger.warning("RETELL_AGENT_ID not configured")
    
    def create_phone_call(self, phone_number: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create an outbound phone call using Retell AI
        
        Args:
            phone_number: Phone number to call (E.164 format)
            metadata: Additional metadata for the call
            
        Returns:
            Call creation result
        """
        try:
            if not self.api_key or not self.agent_id:
                return {
                    "success": False,
                    "error": "Retell AI not properly configured. Please set RETELL_API_KEY and RETELL_AGENT_ID."
                }
            
            url = f"{self.base_url}/create-phone-call"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "from_number": os.getenv("RETELL_FROM_NUMBER", "+1234567890"),
                "to_number": phone_number,
                "agent_id": self.agent_id,
                "metadata": metadata or {}
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"Retell AI call created successfully: {result.get('call_id')}")
                return {
                    "success": True,
                    "call_id": result.get("call_id"),
                    "call_status": result.get("call_status"),
                    "message": "Phone call initiated successfully"
                }
            else:
                logger.error(f"Retell AI call creation failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Failed to create call: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error creating Retell AI call: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_call_details(self, call_id: str) -> Dict[str, Any]:
        """
        Get details of a specific call
        
        Args:
            call_id: ID of the call to retrieve
            
        Returns:
            Call details
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "Retell API key not configured"
                }
            
            url = f"{self.base_url}/get-call/{call_id}"
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "call_details": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get call details: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error getting call details: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_calls(self, limit: int = 50) -> Dict[str, Any]:
        """
        List recent calls
        
        Args:
            limit: Maximum number of calls to retrieve
            
        Returns:
            List of calls
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "Retell API key not configured"
                }
            
            url = f"{self.base_url}/list-calls"
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            params = {"limit": limit}
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "calls": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to list calls: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error listing calls: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new Retell AI agent
        
        Args:
            agent_config: Configuration for the agent
            
        Returns:
            Agent creation result
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "Retell API key not configured"
                }
            
            url = f"{self.base_url}/create-agent"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=agent_config, headers=headers)
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"Retell AI agent created: {result.get('agent_id')}")
                return {
                    "success": True,
                    "agent_id": result.get("agent_id"),
                    "agent_details": result
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create agent: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_appointment_confirmation_call(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send appointment confirmation via Retell AI voice call
        
        Args:
            appointment_data: Appointment information
            
        Returns:
            Call result
        """
        try:
            phone_number = appointment_data.get("patient_phone")
            if not phone_number:
                return {
                    "success": False,
                    "error": "Patient phone number is required"
                }
            
            # Prepare metadata for the call
            metadata = {
                "call_type": "appointment_confirmation",
                "patient_name": appointment_data.get("patient_name"),
                "doctor_name": appointment_data.get("doctor_name"),
                "appointment_date": appointment_data.get("appointment_date"),
                "appointment_time": appointment_data.get("appointment_time"),
                "hospital_name": appointment_data.get("hospital_name", "City General Hospital")
            }
            
            # Create the call
            result = self.create_phone_call(phone_number, metadata)
            
            # Trigger Make.ai workflow for additional notifications
            if result.get("success"):
                make_result = self._trigger_make_workflow({
                    "type": "voice_confirmation_sent",
                    "call_id": result.get("call_id"),
                    **appointment_data
                })
                result["make_workflow_result"] = make_result
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending appointment confirmation call: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_appointment_reminder_call(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send appointment reminder via Retell AI voice call
        
        Args:
            appointment_data: Appointment information
            
        Returns:
            Call result
        """
        try:
            phone_number = appointment_data.get("patient_phone")
            if not phone_number:
                return {
                    "success": False,
                    "error": "Patient phone number is required"
                }
            
            # Prepare metadata for the call
            metadata = {
                "call_type": "appointment_reminder",
                "patient_name": appointment_data.get("patient_name"),
                "doctor_name": appointment_data.get("doctor_name"),
                "appointment_date": appointment_data.get("appointment_date"),
                "appointment_time": appointment_data.get("appointment_time"),
                "hospital_name": appointment_data.get("hospital_name", "City General Hospital")
            }
            
            # Create the call
            result = self.create_phone_call(phone_number, metadata)
            
            # Trigger Make.ai workflow
            if result.get("success"):
                make_result = self._trigger_make_workflow({
                    "type": "voice_reminder_sent",
                    "call_id": result.get("call_id"),
                    **appointment_data
                })
                result["make_workflow_result"] = make_result
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending appointment reminder call: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_emergency_alert_call(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send emergency alert via Retell AI voice call
        
        Args:
            alert_data: Emergency alert information
            
        Returns:
            Call result
        """
        try:
            phone_number = alert_data.get("contact_phone")
            if not phone_number:
                return {
                    "success": False,
                    "error": "Contact phone number is required"
                }
            
            # Prepare metadata for the emergency call
            metadata = {
                "call_type": "emergency_alert",
                "alert_message": alert_data.get("message"),
                "priority": "high",
                "patient_name": alert_data.get("patient_name"),
                "emergency_type": alert_data.get("emergency_type"),
                "hospital_name": alert_data.get("hospital_name", "City General Hospital")
            }
            
            # Create the emergency call
            result = self.create_phone_call(phone_number, metadata)
            
            # Trigger Make.ai workflow for emergency handling
            if result.get("success"):
                make_result = self._trigger_make_workflow({
                    "type": "emergency_voice_alert_sent",
                    "call_id": result.get("call_id"),
                    "priority": "high",
                    **alert_data
                })
                result["make_workflow_result"] = make_result
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending emergency alert call: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming webhook from Retell AI
        
        Args:
            webhook_data: Webhook payload from Retell AI
            
        Returns:
            Processing result
        """
        try:
            event_type = webhook_data.get("event")
            call_id = webhook_data.get("call_id")
            
            logger.info(f"Received Retell AI webhook: {event_type} for call {call_id}")
            
            # Add to conversation history
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "call_id": call_id,
                "data": webhook_data
            })
            
            # Process different event types
            if event_type == "call_started":
                return self._handle_call_started(webhook_data)
            elif event_type == "call_ended":
                return self._handle_call_ended(webhook_data)
            elif event_type == "call_analyzed":
                return self._handle_call_analyzed(webhook_data)
            else:
                return {
                    "success": True,
                    "message": f"Webhook event {event_type} processed"
                }
                
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_call_started(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call started event"""
        call_id = webhook_data.get("call_id")
        logger.info(f"Call started: {call_id}")
        
        # Trigger Make.ai workflow for call started
        make_result = self._trigger_make_workflow({
            "type": "retell_call_started",
            "call_id": call_id,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "message": "Call started event processed",
            "make_workflow_result": make_result
        }
    
    def _handle_call_ended(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call ended event"""
        call_id = webhook_data.get("call_id")
        call_length = webhook_data.get("call_length_seconds", 0)
        
        logger.info(f"Call ended: {call_id}, Duration: {call_length}s")
        
        # Trigger Make.ai workflow for call ended
        make_result = self._trigger_make_workflow({
            "type": "retell_call_ended",
            "call_id": call_id,
            "call_length_seconds": call_length,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "message": "Call ended event processed",
            "make_workflow_result": make_result
        }
    
    def _handle_call_analyzed(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call analyzed event"""
        call_id = webhook_data.get("call_id")
        analysis = webhook_data.get("call_analysis", {})
        
        logger.info(f"Call analyzed: {call_id}")
        
        # Trigger Make.ai workflow for call analysis
        make_result = self._trigger_make_workflow({
            "type": "retell_call_analyzed",
            "call_id": call_id,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "message": "Call analysis processed",
            "analysis": analysis,
            "make_workflow_result": make_result
        }
    
    def _trigger_make_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger Make.ai workflow with Retell AI data"""
        try:
            # Send to Make.ai via notification agent
            result = notification_agent.make_client.trigger_notification_workflow(workflow_data)
            logger.info(f"Make.ai workflow triggered for Retell AI event: {workflow_data.get('type')}")
            return result
        except Exception as e:
            logger.error(f"Error triggering Make.ai workflow: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        return self.conversation_history[-limit:]
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_agent_details(self, agent_id: str = None) -> Dict[str, Any]:
        """
        Get details of a specific agent
        
        Args:
            agent_id: ID of the agent (defaults to configured agent)
            
        Returns:
            Agent details
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "Retell API key not configured"
                }
            
            target_agent_id = agent_id or self.agent_id
            if not target_agent_id:
                return {
                    "success": False,
                    "error": "No agent ID provided"
                }
            
            url = f"{self.base_url}/get-agent/{target_agent_id}"
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "agent_details": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get agent details: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error getting agent details: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Global Retell voice service instance
retell_voice_service = RetellVoiceService()

