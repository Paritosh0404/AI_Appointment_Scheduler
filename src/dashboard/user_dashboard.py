"""
User Dashboard for Hospital Appointment Scheduler
Real-time dashboard with alerts, appointment management, and notifications
"""
import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import asyncio
from typing import Dict, Any, List

# Import our agents
from src.agents.langchain_mcp_agent import get_hospital_agent, handle_voice_request

user_dashboard = Blueprint("user_dashboard", __name__)

@user_dashboard.route("/dashboard")
def dashboard():
    """Main user dashboard page"""
    return render_template("user_dashboard.html")

@user_dashboard.route("/api/user/appointments")
async def get_user_appointments():
    """Get appointments for the current user using LangChain MCP agent"""
    try:
        user_phone = request.args.get("phone", session.get("user_phone", ""))
        if not user_phone:
            return jsonify({"success": False, "error": "User phone not provided"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Get all appointments for patient with phone number {user_phone}",
            {"action": "get_patient_appointments", "patient_phone": user_phone}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@user_dashboard.route("/api/user/alerts")
async def get_user_alerts():
    """Get active alerts for the current user using LangChain MCP agent"""
    try:
        user_phone = request.args.get("phone", session.get("user_phone", ""))
        if not user_phone:
            return jsonify({"success": False, "error": "User phone not provided"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Get active alerts for patient with phone number {user_phone}",
            {"action": "get_active_alerts", "patient_phone": user_phone}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@user_dashboard.route("/api/user/schedule", methods=["POST"])
async def schedule_appointment_route():
    """Schedule a new appointment using LangChain MCP agent"""
    try:
        data = request.get_json()
        patient_info = data.get("patient_info", {})

        if not patient_info:
            return jsonify({"success": False, "error": "Missing patient_info"}), 400

        agent = await get_hospital_agent()
        result = await agent.schedule_appointment_flow(patient_info)
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@user_dashboard.route("/api/user/voice", methods=["POST"])
async def process_voice_route():
    """Process voice input from user using LangChain MCP agent"""
    try:
        data = request.get_json()
        voice_text = data.get("text", "")
        conversation_id = data.get("conversation_id", "")
        audio_data_b64 = data.get("audio_data")

        if not audio_data_b64 and not voice_text:
            return jsonify({"success": False, "error": "No audio data or user text provided"}), 400

        audio_data = base64.b64decode(audio_data_b64) if audio_data_b64 else None

        result = await handle_voice_request(audio_data=audio_data, user_text=voice_text, conversation_id=conversation_id)
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@user_dashboard.route("/api/user/acknowledge_alert", methods=["POST"])
async def acknowledge_alert_route():
    """Acknowledge an alert using LangChain MCP agent"""
    try:
        data = request.get_json()
        alert_id = data.get("alert_id")

        if not alert_id:
            return jsonify({"success": False, "error": "Missing alert_id"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Acknowledge alert with ID {alert_id}",
            {"action": "acknowledge_alert", "alert_id": alert_id}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@user_dashboard.route("/api/user/cancel_appointment", methods=["POST"])
async def cancel_appointment_route():
    """Cancel an appointment using LangChain MCP agent"""
    try:
        data = request.get_json()
        appointment_id = data.get("appointment_id")
        reason = data.get("reason", "User requested cancellation")

        if not appointment_id:
            return jsonify({"success": False, "error": "Missing appointment_id"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Cancel appointment {appointment_id} due to {reason}",
            {"action": "cancel_appointment", "appointment_id": appointment_id, "reason": reason}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@user_dashboard.route("/api/user/reschedule_appointment", methods=["POST"])
async def reschedule_appointment_route():
    """
    Reschedule an appointment using LangChain MCP agent
    """
    try:
        data = request.get_json()
        appointment_id = data.get("appointment_id")
        new_date = data.get("new_date")
        new_time = data.get("new_time")

        if not all([appointment_id, new_date, new_time]):
            return jsonify({"success": False, "error": "Missing required parameters"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Reschedule appointment {appointment_id} to {new_date} at {new_time}",
            {"action": "reschedule_appointment", "appointment_id": appointment_id, "new_date": new_date, "new_time": new_time}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@user_dashboard.route("/api/user/doctors")
async def get_doctors_route():
    """Get list of available doctors using LangChain MCP agent"""
    try:
        department = request.args.get("department", "")
        filters = {"department": department} if department else {}

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"List doctors with filters: {json.dumps(filters)}",
            {"action": "get_doctors", "filters": filters}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@user_dashboard.route("/api/user/availability")
async def check_availability_route():
    """Check doctor availability for a specific date using LangChain MCP agent"""
    try:
        doctor_name = request.args.get("doctor")
        date = request.args.get("date")

        if not all([doctor_name, date]):
            return jsonify({"success": False, "error": "Doctor name and date are required"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Check availability for {doctor_name} on {date}",
            {"action": "get_doctor_availability", "doctor_name": doctor_name, "date": date}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# WEBSOCKET EVENTS FOR REAL-TIME UPDATES
# ============================================================================

def init_socketio_events(socketio_instance):
    """Initialize SocketIO events for real-time dashboard updates"""
    
    @socketio_instance.on("join_user_room")
    def on_join_user_room(data):
        """Join user-specific room for real-time updates"""
        user_phone = data.get("phone", session.get("user_phone"))
        if user_phone:
            room = f"user_{user_phone}"
            join_room(room)
            emit("joined_room", {"room": room})
    
    @socketio_instance.on("leave_user_room")
    def on_leave_user_room(data):
        """Leave user-specific room"""
        user_phone = data.get("phone", session.get("user_phone"))
        if user_phone:
            room = f"user_{user_phone}"
            leave_room(room)
            emit("left_room", {"room": room})
    
    @socketio_instance.on("request_voice_session")
    async def on_request_voice_session(data):
        """Start a voice interaction session"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        conversation_id = f"voice_{timestamp}"
        emit("voice_session_started", {
            "conversation_id": conversation_id,
            "message": "Voice session started. You can now speak your request."
        })
    
    @socketio_instance.on("voice_input")
    async def on_voice_input(data):
        """Handle voice input from user"""
        try:
            voice_text = data.get("text", "")
            conversation_id = data.get("conversation_id", "")
            audio_data_b64 = data.get("audio_data")

            audio_data = base64.b64decode(audio_data_b64) if audio_data_b64 else None
            
            result = await handle_voice_request(audio_data=audio_data, user_text=voice_text, conversation_id=conversation_id)
            emit("voice_response", result)
                
        except Exception as e:
            emit("voice_error", {
                "error": str(e),
                "message": "Sorry, I encountered an error processing your voice input."
            })

def send_real_time_alert(user_phone: str, alert_data: Dict[str, Any], socketio_instance: SocketIO):
    """Send real-time alert to user dashboard"""
    try:
        room = f"user_{user_phone}"
        socketio_instance.emit("new_alert", alert_data, room=room)
    except Exception as e:
        print(f"Error sending real-time alert: {str(e)}")

def send_appointment_update(user_phone: str, appointment_data: Dict[str, Any], socketio_instance: SocketIO):
    """Send real-time appointment update to user dashboard"""
    try:
        room = f"user_{user_phone}"
        socketio_instance.emit("appointment_update", appointment_data, room=room)
    except Exception as e:
        print(f"Error sending appointment update: {str(e)}")

# ============================================================================
# DASHBOARD ANALYTICS
# ============================================================================

@user_dashboard.route("/api/user/analytics")
async def get_user_analytics_route():
    """Get user dashboard analytics using LangChain MCP agent"""
    try:
        user_phone = request.args.get("phone", session.get("user_phone", ""))
        if not user_phone:
            return jsonify({"success": False, "error": "User phone not provided"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Get analytics for patient with phone number {user_phone}",
            {"action": "get_patient_analytics", "patient_phone": user_phone}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


