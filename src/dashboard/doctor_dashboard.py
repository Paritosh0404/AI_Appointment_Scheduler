"""
Doctor Dashboard for Hospital Appointment Scheduler
Dashboard for doctors to manage appointments, view schedules, and handle alerts
"""
import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import asyncio
from typing import Dict, Any, List

# Import our agents
from src.agents.langchain_mcp_agent import get_hospital_agent

doctor_dashboard = Blueprint("doctor_dashboard", __name__)

@doctor_dashboard.route("/doctor/dashboard")
def dashboard():
    """Main doctor dashboard page"""
    return render_template("doctor_dashboard.html")

@doctor_dashboard.route("/api/doctor/schedule")
async def get_doctor_schedule_route():
    """Get doctor's schedule for a specific date range using LangChain MCP agent"""
    try:
        doctor_name = request.args.get("doctor", session.get("doctor_name", ""))
        start_date = request.args.get("start_date", datetime.now().strftime("%Y-%m-%d"))
        end_date = request.args.get("end_date", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))

        if not doctor_name:
            return jsonify({"success": False, "error": "Doctor name not provided"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Get schedule for doctor {doctor_name} from {start_date} to {end_date}",
            {"action": "get_doctor_schedule", "doctor_name": doctor_name, "start_date": start_date, "end_date": end_date}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@doctor_dashboard.route("/api/doctor/today_schedule")
async def get_today_schedule_route():
    """Get doctor's schedule for today using LangChain MCP agent"""
    try:
        doctor_name = request.args.get("doctor", session.get("doctor_name", ""))
        today = datetime.now().strftime("%Y-%m-%d")

        if not doctor_name:
            return jsonify({"success": False, "error": "Doctor name not provided"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Get today's schedule for doctor {doctor_name} on {today}",
            {"action": "get_doctor_today_schedule", "doctor_name": doctor_name, "date": today}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@doctor_dashboard.route("/api/doctor/create_alert", methods=["POST"])
async def create_alert_route():
    """Create an alert for appointment changes using LangChain MCP agent"""
    try:
        data = request.get_json()
        alert_info = data.get("alert_info", {})

        if not alert_info:
            return jsonify({"success": False, "error": "Missing alert_info"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Create a new alert with details: {json.dumps(alert_info)}",
            {"action": "create_dynamic_alert", "alert_info": alert_info}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@doctor_dashboard.route("/api/doctor/update_appointment_status", methods=["POST"])
async def update_appointment_status_route():
    """Update appointment status (completed, no-show, etc.) using LangChain MCP agent"""
    try:
        data = request.get_json()
        status_info = data.get("status_info", {})

        if not status_info:
            return jsonify({"success": False, "error": "Missing status_info"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Update appointment status with details: {json.dumps(status_info)}",
            {"action": "update_appointment_status", "status_info": status_info}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@doctor_dashboard.route("/api/doctor/running_late", methods=["POST"])
async def report_running_late_route():
    """Report that doctor is running late using LangChain MCP agent"""
    try:
        data = request.get_json()
        late_info = data.get("late_info", {})

        if not late_info:
            return jsonify({"success": False, "error": "Missing late_info"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Report doctor running late with details: {json.dumps(late_info)}",
            {"action": "report_doctor_running_late", "late_info": late_info}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@doctor_dashboard.route("/api/doctor/emergency_reschedule", methods=["POST"])
async def emergency_reschedule_route():
    """
    Handle emergency rescheduling of appointments using LangChain MCP agent
    """
    try:
        data = request.get_json()
        reschedule_info = data.get("reschedule_info", {})

        if not reschedule_info:
            return jsonify({"success": False, "error": "Missing reschedule_info"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Handle emergency reschedule with details: {json.dumps(reschedule_info)}",
            {"action": "emergency_reschedule", "reschedule_info": reschedule_info}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@doctor_dashboard.route("/api/doctor/patient_history")
async def get_patient_history_route():
    """Get patient's appointment history using LangChain MCP agent"""
    try:
        patient_phone = request.args.get("patient_phone")

        if not patient_phone:
            return jsonify({"success": False, "error": "Patient phone number is required"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Get patient history for phone number {patient_phone}",
            {"action": "get_patient_history", "patient_phone": patient_phone}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@doctor_dashboard.route("/api/doctor/analytics")
async def get_doctor_analytics_route():
    """
    Get doctor dashboard analytics using LangChain MCP agent
    """
    try:
        doctor_name = request.args.get("doctor", session.get("doctor_name", ""))

        if not doctor_name:
            return jsonify({"success": False, "error": "Doctor name not provided"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Get analytics for doctor {doctor_name}",
            {"action": "get_doctor_analytics", "doctor_name": doctor_name}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@doctor_dashboard.route("/api/doctor/availability", methods=["POST"])
async def update_availability_route():
    """
    Update doctor's availability using LangChain MCP agent
    """
    try:
        data = request.get_json()
        availability_info = data.get("availability_info", {})

        if not availability_info:
            return jsonify({"success": False, "error": "Missing availability_info"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Update doctor availability with details: {json.dumps(availability_info)}",
            {"action": "update_doctor_availability", "availability_info": availability_info}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def init_doctor_socketio_events(socketio_instance):
    """
    Initialize SocketIO events for real-time doctor dashboard updates
    """
    @socketio_instance.on("join_doctor_room")
    def on_join_doctor_room(data):
        """Join doctor-specific room for real-time updates"""
        doctor_name = data.get("doctor_name", session.get("doctor_name"))
        if doctor_name:
            room = f"doctor_{doctor_name}"
            join_room(room)
            emit("joined_room", {"room": room})

    @socketio_instance.on("leave_doctor_room")
    def on_leave_doctor_room(data):
        """Leave doctor-specific room"""
        doctor_name = data.get("doctor_name", session.get("doctor_name"))
        if doctor_name:
            room = f"doctor_{doctor_name}"
            leave_room(room)
            emit("left_room", {"room": room})

def send_doctor_real_time_alert(doctor_name: str, alert_data: Dict[str, Any], socketio_instance: SocketIO):
    """
    Send real-time alert to doctor dashboard
    """
    try:
        room = f"doctor_{doctor_name}"
        socketio_instance.emit("new_doctor_alert", alert_data, room=room)
    except Exception as e:
        print(f"Error sending real-time doctor alert: {str(e)}")

def send_doctor_schedule_update(doctor_name: str, schedule_data: Dict[str, Any], socketio_instance: SocketIO):
    """
    Send real-time schedule update to doctor dashboard
    """
    try:
        room = f"doctor_{doctor_name}"
        socketio_instance.emit("doctor_schedule_update", schedule_data, room=room)
    except Exception as e:
        print(f"Error sending doctor schedule update: {str(e)}")


