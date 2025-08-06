"""
Flask routes for appointment management with LangChain MCP agent integration and Make.ai notifications
"""
from flask import Blueprint, request, jsonify
import asyncio
import json
from src.agents.langchain_mcp_agent import get_hospital_agent, schedule_appointment, process_appointment_request
from src.integrations.make_client import notification_agent

appointment_bp = Blueprint("appointment", __name__)

@appointment_bp.route("/schedule", methods=["POST"])
async def schedule_appointment_route():
    """Schedule a new appointment using the LangChain MCP agent"""
    try:
        data = request.get_json()
        patient_info = data.get("patient_info", {})

        if not patient_info:
            return jsonify({"success": False, "error": "Missing patient_info"}), 400

        result = await schedule_appointment(patient_info)
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/process-request", methods=["POST"])
async def process_appointment_request_route():
    """Process a natural language request for appointment management"""
    try:
        data = request.get_json()
        user_input = data.get("user_input", "")
        context = data.get("context", {})

        if not user_input:
            return jsonify({"success": False, "error": "Missing user_input"}), 400

        # Use simplified handler instead of complex MCP agent
        from src.agents.simple_voice_handler import process_appointment_request
        result = await process_appointment_request(user_input, context)
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/parse-request", methods=["POST"])
async def parse_appointment_request_route():
    """Legacy route - same as process-request"""
    return await process_appointment_request_route()

@appointment_bp.route("/smart-recommendations", methods=["POST"])
async def smart_recommendations_route():
    """
    Get smart appointment recommendations using the LangChain MCP agent
    """
    try:
        data = request.get_json()
        preferences = data.get("preferences", {})

        if not preferences:
            return jsonify({"success": False, "error": "Missing preferences"}), 400

        agent = await get_hospital_agent()
        result = await agent.get_smart_recommendations(preferences)
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/handle-change", methods=["POST"])
async def handle_appointment_change_route():
    """
    Handle appointment changes and send dynamic alerts using the LangChain MCP agent
    """
    try:
        data = request.get_json()
        change_info = data.get("change_info", {})

        if not change_info:
            return jsonify({"success": False, "error": "Missing change_info"}), 400

        agent = await get_hospital_agent()
        result = await agent.handle_appointment_change(change_info)
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/doctors", methods=["GET"])
async def get_doctors_route():
    """Get list of doctors using the LangChain MCP agent"""
    try:
        filters = {
            "department": request.args.get("department"),
            "specialization": request.args.get("specialization"),
            "available_date": request.args.get("available_date")
        }
        filters = {k: v for k, v in filters.items() if v is not None}

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"List doctors with filters: {json.dumps(filters)}",
            {"action": "get_doctors", "filters": filters}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/doctor-availability", methods=["POST"])
async def doctor_availability_route():
    """
    Check doctor availability for specific date and time using the LangChain MCP agent
    """
    try:
        data = request.get_json()
        doctor_name = data.get("doctor_name")
        appointment_date = data.get("appointment_date")
        appointment_time = data.get("appointment_time")

        if not all([doctor_name, appointment_date, appointment_time]):
            return jsonify({"success": False, "error": "Missing required parameters"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Check availability for {doctor_name} on {appointment_date} at {appointment_time}",
            {
                "action": "check_doctor_availability",
                "doctor_name": doctor_name,
                "date": appointment_date,
                "time": appointment_time
            }
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/patient-appointments", methods=["GET"])
async def patient_appointments_route():
    """
    Get all appointments for a patient using the LangChain MCP agent
    """
    try:
        patient_phone = request.args.get("patient_phone")

        if not patient_phone:
            return jsonify({"success": False, "error": "Missing patient_phone"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Get all appointments for patient with phone number {patient_phone}",
            {"action": "get_patient_appointments", "patient_phone": patient_phone}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/alerts", methods=["GET"])
async def get_alerts_route():
    """
    Get active alerts using the LangChain MCP agent
    """
    try:
        patient_phone = request.args.get("patient_phone")
        priority = request.args.get("priority")

        filters = {k: v for k, v in {"patient_phone": patient_phone, "priority": priority}.items() if v is not None}

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Get active alerts with filters: {json.dumps(filters)}",
            {"action": "get_active_alerts", "filters": filters}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/alerts/create", methods=["POST"])
async def create_alert_route():
    """
    Create a new alert using the LangChain MCP agent
    """
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

@appointment_bp.route("/notifications/email", methods=["POST"])
async def send_email_route():
    """
    Send email notification using Make.ai integration
    """
    try:
        data = request.get_json()
        email_info = data.get("email_info", {})

        if not email_info:
            return jsonify({"success": False, "error": "Missing email_info"}), 400

        # Use Make.ai notification agent for email notifications
        result = notification_agent.make_client.send_email_notification(
            email=email_info.get("email"),
            subject=email_info.get("subject", "Hospital Notification"),
            body=email_info.get("body", "")
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/notifications/voice", methods=["POST"])
async def send_voice_route():
    """
    Send voice message using the LangChain MCP agent
    """
    try:
        data = request.get_json()
        voice_info = data.get("voice_info", {})

        if not voice_info:
            return jsonify({"success": False, "error": "Missing voice_info"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Send voice message with details: {json.dumps(voice_info)}",
            {"action": "send_voice_message", "voice_info": voice_info}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/patient-history", methods=["GET"])
async def patient_history_route():
    """
    Get patient history using the LangChain MCP agent
    """
    try:
        patient_phone = request.args.get("patient_phone")

        if not patient_phone:
            return jsonify({"success": False, "error": "Missing patient_phone"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Get patient history for phone number {patient_phone}",
            {"action": "get_patient_history", "patient_phone": patient_phone}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/doctor-analytics", methods=["GET"])
async def doctor_analytics_route():
    """
    Get doctor analytics using the LangChain MCP agent
    """
    try:
        doctor_name = request.args.get("doctor_name")

        if not doctor_name:
            return jsonify({"success": False, "error": "Missing doctor_name"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Get analytics for doctor {doctor_name}",
            {"action": "get_doctor_analytics", "doctor_name": doctor_name}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/update-availability", methods=["POST"])
async def update_availability_route():
    """
    Update doctor availability using the LangChain MCP agent
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

@appointment_bp.route("/running-late", methods=["POST"])
async def running_late_route():
    """
    Report doctor running late using the LangChain MCP agent
    """
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

@appointment_bp.route("/emergency-reschedule", methods=["POST"])
async def emergency_reschedule_route():
    """
    Handle emergency rescheduling using the LangChain MCP agent
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

@appointment_bp.route("/update-appointment-status", methods=["POST"])
async def update_appointment_status_route():
    """
    Update appointment status using the LangChain MCP agent
    """
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

@appointment_bp.route("/available-slots", methods=["POST"])
async def get_available_slots_route():
    """
    Get available slots for a doctor on a specific date using the LangChain MCP agent
    """
    try:
        data = request.get_json()
        doctor_name = data.get("doctor_name")
        appointment_date = data.get("appointment_date")

        if not all([doctor_name, appointment_date]):
            return jsonify({"success": False, "error": "Missing required parameters"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Get available slots for {doctor_name} on {appointment_date}",
            {"action": "get_available_slots", "doctor_name": doctor_name, "date": appointment_date}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/patient-dashboard-data", methods=["GET"])
async def patient_dashboard_data_route():
    """
    Get patient dashboard data using the LangChain MCP agent
    """
    try:
        patient_phone = request.args.get("patient_phone")

        if not patient_phone:
            return jsonify({"success": False, "error": "Missing patient_phone"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Get patient dashboard data for phone number {patient_phone}",
            {"action": "get_patient_dashboard_data", "patient_phone": patient_phone}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/doctor-dashboard-data", methods=["GET"])
async def doctor_dashboard_data_route():
    """
    Get doctor dashboard data using the LangChain MCP agent
    """
    try:
        doctor_name = request.args.get("doctor_name")

        if not doctor_name:
            return jsonify({"success": False, "error": "Missing doctor_name"}), 400

        agent = await get_hospital_agent()
        result = await agent.process_request(
            f"Get doctor dashboard data for doctor {doctor_name}",
            {"action": "get_doctor_dashboard_data", "doctor_name": doctor_name}
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/mcp/tools/list", methods=["GET"])
async def mcp_tools_list_route():
    """
    Get list of available MCP tools from the LangChain MCP agent
    """
    try:
        agent = await get_hospital_agent()
        tools = [{
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.args
        } for tool in agent.tools]
        return jsonify({"success": True, "tools": tools})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@appointment_bp.route("/mcp/tools/execute", methods=["POST"])
async def mcp_tools_execute_route():
    """
    Execute an MCP tool via the LangChain MCP agent
    """
    try:
        data = request.get_json()
        tool_name = data.get("tool_name")
        parameters = data.get("parameters", {})

        if not all([tool_name, parameters]):
            return jsonify({"success": False, "error": "Missing tool_name or parameters"}), 400

        agent = await get_hospital_agent()
        # Find the tool by name
        tool_to_execute = next((tool for tool in agent.tools if tool.name == tool_name), None)

        if not tool_to_execute:
            return jsonify({"success": False, "error": f"Tool \'{tool_name}\' not found"}), 404

        # Execute the tool directly (this bypasses the LLM for direct tool calls)
        # In a real scenario, you might want to route this through the agent.process_request
        # for LLM-driven tool selection and execution.
        result = tool_to_execute.run(parameters)
        return jsonify({"success": True, "tool_result": result})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


