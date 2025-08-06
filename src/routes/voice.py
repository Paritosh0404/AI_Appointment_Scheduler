"""
Voice Routes for Hospital Appointment Scheduler
Enhanced with Retell AI voice technology and Make.ai integration
"""
import base64
import json
import asyncio
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from src.voice.retell_voice_service import retell_voice_service
from src.agents.langchain_mcp_agent import handle_voice_request
import logging

logger = logging.getLogger(__name__)

voice_bp = Blueprint("voice", __name__)

@voice_bp.route("/api/voice/create-call", methods=["POST"])
def create_voice_call():
    """Create outbound voice call using Retell AI"""
    try:
        data = request.get_json()
        phone_number = data.get("phone_number")
        metadata = data.get("metadata", {})
        
        if not phone_number:
            return jsonify({"success": False, "error": "Phone number is required"}), 400
        
        result = retell_voice_service.create_phone_call(phone_number, metadata)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating voice call: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@voice_bp.route("/api/voice/call-details/<call_id>", methods=["GET"])
def get_call_details(call_id):
    """Get details of a specific call"""
    try:
        result = retell_voice_service.get_call_details(call_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting call details: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@voice_bp.route("/api/voice/calls", methods=["GET"])
def list_calls():
    """List recent calls"""
    try:
        limit = request.args.get("limit", 50, type=int)
        result = retell_voice_service.list_calls(limit)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error listing calls: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@voice_bp.route("/api/voice/webhook", methods=["POST"])
def retell_webhook():
    """Handle webhooks from Retell AI"""
    try:
        webhook_data = request.get_json()
        result = retell_voice_service.handle_webhook(webhook_data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@voice_bp.route("/api/voice/appointment-confirmation", methods=["POST"])
def send_appointment_confirmation_call():
    """Send appointment confirmation via Retell AI voice call"""
    try:
        data = request.get_json()
        appointment_data = data.get("appointment_data", {})
        
        if not appointment_data:
            return jsonify({"success": False, "error": "Missing appointment_data"}), 400
        
        result = retell_voice_service.send_appointment_confirmation_call(appointment_data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error sending appointment confirmation call: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@voice_bp.route("/api/voice/appointment-reminder", methods=["POST"])
def send_appointment_reminder_call():
    """Send appointment reminder via Retell AI voice call"""
    try:
        data = request.get_json()
        appointment_data = data.get("appointment_data", {})
        
        if not appointment_data:
            return jsonify({"success": False, "error": "Missing appointment_data"}), 400
        
        result = retell_voice_service.send_appointment_reminder_call(appointment_data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error sending appointment reminder call: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@voice_bp.route("/api/voice/emergency-alert", methods=["POST"])
def send_emergency_alert_call():
    """Send emergency alert via Retell AI voice call"""
    try:
        data = request.get_json()
        alert_data = data.get("alert_data", {})
        
        if not alert_data:
            return jsonify({"success": False, "error": "Missing alert_data"}), 400
        
        result = retell_voice_service.send_emergency_alert_call(alert_data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error sending emergency alert call: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@voice_bp.route("/api/voice/health", methods=["GET"])
def voice_health_check():
    """Health check for Retell AI voice service"""
    try:
        # Test basic functionality by getting agent details
        result = retell_voice_service.get_agent_details()
        
        return jsonify({
            "success": True,
            "service": "Retell AI Voice Service",
            "status": "healthy" if result.get("success") else "degraded",
            "features": {
                "outbound_calls": True,
                "webhook_handling": True,
                "appointment_notifications": True,
                "emergency_alerts": True
            },
            "agent_configured": bool(retell_voice_service.agent_id),
            "api_key_configured": bool(retell_voice_service.api_key)
        })
        
    except Exception as e:
        logger.error(f"Retell AI health check failed: {str(e)}")
        return jsonify({
            "success": False,
            "service": "Retell AI Voice Service",
            "status": "unhealthy",
            "error": str(e)
        }), 500

@voice_bp.route("/api/voice/agent-details", methods=["GET"])
def get_agent_details():
    """Get Retell AI agent details"""
    try:
        agent_id = request.args.get("agent_id")
        result = retell_voice_service.get_agent_details(agent_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting agent details: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@voice_bp.route("/api/voice/conversation-history", methods=["GET"])
def get_conversation_history_route():
    """Get conversation history from Retell AI"""
    try:
        limit = request.args.get("limit", 10, type=int)
        history = retell_voice_service.get_conversation_history(limit)
        
        return jsonify({
            "success": True,
            "conversation_history": history,
            "count": len(history)
        })
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@voice_bp.route("/api/voice/conversation-history", methods=["DELETE"])
def clear_conversation_history_route():
    """Clear conversation history"""
    try:
        retell_voice_service.clear_conversation_history()
        
        return jsonify({
            "success": True,
            "message": "Conversation history cleared"
        })
        
    except Exception as e:
        logger.error(f"Error clearing conversation history: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Legacy routes for backward compatibility
@voice_bp.route("/process-voice", methods=["POST"])
async def process_voice_legacy():
    """Process voice input for local speech recognition"""
    try:
        data = request.get_json()
        logger.info(f"Received voice processing request")
        
        # Handle audio data (base64 encoded)
        audio_data = data.get("audio_data")
        conversation_id = data.get("conversation_id")
        
        if not audio_data:
            return jsonify({
                "success": False, 
                "error": "audio_data is required"
            }), 400
        
        # Simulate speech-to-text (in real implementation, you'd use Google Speech-to-Text, etc.)
        # For demo purposes, let's simulate different responses based on audio length
        audio_length = len(audio_data)
        
        if audio_length < 10000:
            transcript = "I need to schedule an appointment"
        elif audio_length < 20000:
            transcript = "I want to see a cardiologist next week"
        else:
            transcript = "Can you help me book an appointment with Dr. Smith for tomorrow?"
        
        # Use the simplified voice handler for AI processing
        try:
            from src.agents.simple_voice_handler import handle_voice_request
            
            # Process with AI agent
            response = await handle_voice_request(transcript)
            
            result = {
                "success": True,
                "user_text": transcript,  # The frontend expects this field
                "response_text": response.get("response", "I understand your request. Let me help you with that."),
                "conversation_id": conversation_id or f"conv_{datetime.now().timestamp()}",
                "response_audio": None,  # Could generate TTS audio here
                "suggestions": response.get("suggestions", []),
                "action_type": response.get("action_type", "general")
            }
            
            logger.info(f"Voice processing successful")
            return jsonify(result)
            
        except Exception as ai_error:
            logger.warning(f"AI agent failed, using fallback: {ai_error}")
            # Fallback response
            result = {
                "success": True,
                "user_text": transcript,
                "response_text": "I understand you want to schedule an appointment. Please provide more details like doctor name, date, and time preference.",
                "conversation_id": conversation_id or f"conv_{datetime.now().timestamp()}",
                "response_audio": None
            }
            
            return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing voice: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@voice_bp.route("/test-voice", methods=["POST"])
def test_voice_route():
    """Test voice service with Retell AI"""
    try:
        data = request.get_json() or {}
        test_phone = data.get("phone_number", "+1234567890")
        
        # Create a test call
        result = retell_voice_service.create_phone_call(
            phone_number=test_phone,
            metadata={
                "call_type": "test",
                "message": "This is a test call from the hospital appointment system."
            }
        )
        
        return jsonify({
            "success": result.get("success", False),
            "test_phone": test_phone,
            "call_id": result.get("call_id"),
            "provider": "Retell AI",
            "message": "Test call initiated" if result.get("success") else "Test call failed",
            "details": result
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

