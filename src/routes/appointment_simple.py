"""
Simple Flask routes for appointment management
"""
from flask import Blueprint, request, jsonify
import asyncio
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
appointment_bp = Blueprint("appointment", __name__)

@appointment_bp.route("/schedule", methods=["POST"])
def schedule_appointment_route():
    """Schedule a new appointment"""
    try:
        data = request.get_json()
        appointment_data = data.get("appointment_data", {})

        if not appointment_data:
            return jsonify({"success": False, "error": "Missing appointment_data"}), 400

        # Generate appointment ID
        appointment_id = f"APT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create appointment record
        appointment = {
            "appointment_id": appointment_id,
            "patient_name": appointment_data.get("patient_name", ""),
            "patient_phone": appointment_data.get("patient_phone", ""),
            "patient_email": appointment_data.get("patient_email", ""),
            "doctor_name": appointment_data.get("doctor_name", "Dr. Smith"),
            "department": appointment_data.get("department", "General"),
            "appointment_date": appointment_data.get("appointment_date", datetime.now().strftime('%Y-%m-%d')),
            "appointment_time": appointment_data.get("appointment_time", "10:00"),
            "notes": appointment_data.get("notes", ""),
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }

        return jsonify({
            "success": True,
            "appointment": appointment,
            "message": "Appointment scheduled successfully!"
        })

    except Exception as e:
        logger.error(f"Error scheduling appointment: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/parse-request", methods=["POST"])
def parse_appointment_request_route():
    """Parse a natural language request for appointment management"""
    try:
        data = request.get_json()
        user_input = data.get("user_input", "")
        context = data.get("context", {})

        if not user_input:
            return jsonify({"success": False, "error": "Missing user_input"}), 400

        # Use simplified handler (convert async to sync)
        from src.agents.simple_voice_handler import process_appointment_request_sync
        result = process_appointment_request_sync(user_input, context)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error parsing request: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/list", methods=["GET"])
def list_appointments():
    """List appointments for a patient"""
    try:
        patient_phone = request.args.get("patient_phone")
        
        if not patient_phone:
            return jsonify({"success": False, "error": "Missing patient_phone parameter"}), 400

        # Mock appointments for demo
        appointments = [
            {
                "appointment_id": "APT_20250807_100000",
                "patient_name": "John Doe",
                "patient_phone": patient_phone,
                "doctor_name": "Dr. Smith",
                "department": "Cardiology",
                "appointment_date": "2025-08-08",
                "appointment_time": "10:00",
                "status": "scheduled"
            }
        ]

        return jsonify({
            "success": True,
            "appointments": appointments
        })

    except Exception as e:
        logger.error(f"Error listing appointments: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/doctors", methods=["GET"])
def list_doctors():
    """List available doctors"""
    try:
        # Mock doctors data
        doctors = [
            {
                "id": 1,
                "name": "Dr. Sarah Johnson",
                "specialization": "Cardiology",
                "department": "Cardiology",
                "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "start_time": "09:00",
                "end_time": "17:00",
                "consultation_duration": 30
            },
            {
                "id": 2,
                "name": "Dr. Michael Chen",
                "specialization": "Neurology",
                "department": "Neurology",
                "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday"],
                "start_time": "10:00",
                "end_time": "18:00",
                "consultation_duration": 60
            },
            {
                "id": 3,
                "name": "Dr. Emily Davis",
                "specialization": "Pediatrics",
                "department": "Pediatrics",
                "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "start_time": "09:00",
                "end_time": "17:00",
                "consultation_duration": 20
            }
        ]

        return jsonify({
            "success": True,
            "doctors": doctors
        })

    except Exception as e:
        logger.error(f"Error listing doctors: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
