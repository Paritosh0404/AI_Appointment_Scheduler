"""
Dynamic Alerts Agent for Hospital Appointment Scheduler
Manages real-time alerts and notifications for appointment changes
"""
import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging
import uuid

from src.mcp.mcp_server_proper import mcp_server, get_db_connection # Import mcp_server instance
from src.agents.gmail_agent import send_email_notification
from src.agents.whatsapp_agent import send_whatsapp_message, send_whatsapp_voice_message
from src.voice.voice_service import text_to_speech

logger = logging.getLogger(__name__)

class AlertType(Enum):
    """Types of alerts that can be generated"""
    DOCTOR_LATE = "doctor_late"
    APPOINTMENT_POSTPONED = "appointment_postponed"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    EMERGENCY_RESCHEDULE = "emergency_reschedule"
    DOCTOR_UNAVAILABLE = "doctor_unavailable"
    FACILITY_CLOSURE = "facility_closure"
    WEATHER_ALERT = "weather_alert"
    CUSTOM = "custom"

class AlertPriority(Enum):
    """Priority levels for alerts"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class AlertStatus(Enum):
    """Status of alerts"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"

HOSPITAL_NAME = os.getenv("HOSPITAL_NAME", "City General Hospital")

@mcp_server.tool()
def create_alert(
    alert_type: str,
    appointment_id: str,
    patient_phone: str,
    message: str,
    priority: str = "medium",
    doctor_name: str = "",
    estimated_delay: str = "",
    new_appointment_time: str = "",
    expiry_time: str = "",
    auto_notify: bool = True
) -> str:
    """
    Create a new dynamic alert for appointment changes.
    
    Args:
        alert_type: Type of alert to create (e.g., "doctor_late", "appointment_postponed").
        appointment_id: ID of the affected appointment.
        patient_phone: Phone number of the affected patient.
        message: Alert message content.
        priority: Priority level of the alert (low, medium, high, urgent).
        doctor_name: Name of the affected doctor.
        estimated_delay: Estimated delay time (for late alerts).
        new_appointment_time: New appointment time (for rescheduled alerts).
        expiry_time: When the alert expires (ISO format).
        auto_notify: Whether to automatically send notifications.
    
    Returns:
        JSON string with success status and alert ID.
    """
    try:
        alert_id = str(uuid.uuid4())
        
        # Calculate expiry time if not provided
        if not expiry_time:
            expiry_delta = timedelta(hours=24)  # Default 24 hours
            if priority == "urgent":
                expiry_delta = timedelta(hours=6)
            elif priority == "high":
                expiry_delta = timedelta(hours=12)
            expiry_time = (datetime.now() + expiry_delta).isoformat()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO alerts (
                alert_id, alert_type, priority, status, appointment_id, 
                patient_phone, doctor_name, message, estimated_delay, 
                new_appointment_time, created_at, expiry_time, auto_notify
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert_id, alert_type, priority, AlertStatus.PENDING.value, appointment_id,
            patient_phone, doctor_name, message, estimated_delay,
            new_appointment_time, datetime.now().isoformat(), expiry_time, int(auto_notify)
        ))
        conn.commit()
        conn.close()
        
        logger.info(f"Created alert {alert_id} for appointment {appointment_id}")
        
        # Auto-notify if enabled
        if auto_notify:
            # Fetch patient and doctor details for notification
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT patient_email FROM appointments WHERE appointment_id = ?", (appointment_id,))
            patient_email = cursor.fetchone()[0] if cursor.rowcount > 0 else None
            conn.close()

            # Example notification calls (can be expanded based on channels)
            if patient_email:
                asyncio.create_task(send_email_notification(
                    recipient_email=patient_email,
                    subject=f"Urgent Alert from {HOSPITAL_NAME}",
                    message=message
                ))
            asyncio.create_task(send_whatsapp_message(
                recipient_phone=patient_phone,
                message=message
            ))
            # You might want to generate voice message here too
            # asyncio.create_task(send_whatsapp_voice_message(patient_phone, audio_url_of_message))

        return json.dumps({
            "success": True,
            "alert_id": alert_id,
            "message": "Alert created successfully"
        })
            
    except Exception as e:
        logger.error(f"Failed to create alert: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@mcp_server.tool()
def update_alert(
    alert_id: str,
    status: str = "",
    message: str = "",
    priority: str = ""
) -> str:
    """
    Update an existing alert.
    
    Args:
        alert_id: ID of the alert to update.
        status: New status for the alert (e.g., "acknowledged", "sent").
        message: Updated message content.
        priority: Updated priority level.
    
    Returns:
        JSON string with success status.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if status:
            updates.append("status = ?")
            params.append(status)
        if message:
            updates.append("message = ?")
            params.append(message)
        if priority:
            updates.append("priority = ?")
            params.append(priority)
        
        if not updates:
            return json.dumps({"success": False, "error": "No fields to update"})
            
        params.append(datetime.now().isoformat())
        params.append(alert_id)
        
        cursor.execute(f"UPDATE alerts SET {", ".join(updates)}, updated_at = ? WHERE alert_id = ?", params)
        conn.commit()
        conn.close()
        
        if cursor.rowcount == 0:
            return json.dumps({"success": False, "error": f"Alert {alert_id} not found"})

        logger.info(f"Updated alert {alert_id}")
        
        return json.dumps({
            "success": True,
            "message": "Alert updated successfully"
        })
            
    except Exception as e:
        logger.error(f"Failed to update alert {alert_id}: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@mcp_server.tool()
def get_alerts(
    patient_phone: str = "",
    doctor_name: str = "",
    appointment_id: str = "",
    alert_type: str = "",
    status: str = "",
    priority: str = "",
    active_only: bool = True,
    limit: int = 50
) -> str:
    """
    Retrieve alerts based on criteria.
    
    Args:
        patient_phone: Filter by patient phone number.
        doctor_name: Filter by doctor name.
        appointment_id: Filter by appointment ID.
        alert_type: Filter by alert type.
        status: Filter by alert status.
        priority: Filter by alert priority.
        active_only: If true, only return alerts with status 'pending' or 'sent'.
        limit: Maximum number of alerts to return.
    
    Returns:
        JSON string with list of alerts.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []
        
        if patient_phone:
            query += " AND patient_phone = ?"
            params.append(patient_phone)
        if doctor_name:
            query += " AND doctor_name = ?"
            params.append(doctor_name)
        if appointment_id:
            query += " AND appointment_id = ?"
            params.append(appointment_id)
        if alert_type:
            query += " AND alert_type = ?"
            params.append(alert_type)
        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        if active_only:
            query += " AND status IN (\'pending\', \'sent\')"
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append(dict(row))
        
        conn.close()
        
        return json.dumps({
            "success": True,
            "alerts": alerts,
            "count": len(alerts)
        })
            
    except Exception as e:
        logger.error(f"Failed to retrieve alerts: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@mcp_server.tool()
def notify_patient(
    alert_id: str,
    notification_channels: List[str] = None,
    include_voice: bool = False
) -> str:
    """
    Send notification to patient about an alert.
    
    Args:
        alert_id: ID of the alert to notify about.
        notification_channels: List of channels to use (email, whatsapp, sms, voice).
        include_voice: Whether to include a voice message.
    
    Returns:
        JSON string with notification status.
    """
    if notification_channels is None:
        notification_channels = ["email", "whatsapp"]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert_id,))
        alert = cursor.fetchone()
        conn.close()

        if not alert:
            return json.dumps({"success": False, "error": f"Alert {alert_id} not found"})

        alert_dict = dict(alert)
        patient_phone = alert_dict["patient_phone"]
        message = alert_dict["message"]
        
        # Fetch patient email for email notification
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT patient_email, patient_name FROM appointments WHERE appointment_id = ?", (alert_dict["appointment_id"],))
        appointment_info = cursor.fetchone()
        patient_email = appointment_info["patient_email"] if appointment_info else None
        patient_name = appointment_info["patient_name"] if appointment_info else "Patient"
        conn.close()

        results = {}
        if "email" in notification_channels and patient_email:
            email_result = asyncio.run(send_email_notification(
                recipient_email=patient_email,
                subject=f"Alert from {HOSPITAL_NAME}",
                message=message
            ))
            results["email"] = json.loads(email_result)

        if "whatsapp" in notification_channels:
            whatsapp_result = asyncio.run(send_whatsapp_message(
                recipient_phone=patient_phone,
                message=message
            ))
            results["whatsapp"] = json.loads(whatsapp_result)

        if include_voice:
            voice_message = f"Hello {patient_name}, this is an important alert from {HOSPITAL_NAME}. {message}"
            # Assuming text_to_speech returns a URL or path to the audio file
            audio_path = asyncio.run(text_to_speech(voice_message, "female_voice")) # Assuming a default voice
            if audio_path:
                whatsapp_voice_result = asyncio.run(send_whatsapp_voice_message(
                    recipient_phone=patient_phone,
                    audio_url=audio_path,
                    text_fallback=voice_message
                ))
                results["whatsapp_voice"] = json.loads(whatsapp_voice_result)

        # Update alert status to sent
        asyncio.run(update_alert(alert_id, status=AlertStatus.SENT.value))

        return json.dumps({"success": True, "notifications": results})

    except Exception as e:
        logger.error(f"Failed to notify patient for alert {alert_id}: {str(e)}")
        return json.dumps({"success": False, "error": str(e)})

@mcp_server.tool()
def notify_doctor(
    alert_id: str,
    notification_channels: List[str] = None
) -> str:
    """
    Send notification to doctor about an alert.
    
    Args:
        alert_id: ID of the alert to notify about.
        notification_channels: List of channels to use (email, whatsapp, sms).
    
    Returns:
        JSON string with notification status.
    """
    if notification_channels is None:
        notification_channels = ["email"]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert_id,))
        alert = cursor.fetchone()
        conn.close()

        if not alert:
            return json.dumps({"success": False, "error": f"Alert {alert_id} not found"})

        alert_dict = dict(alert)
        doctor_name = alert_dict["doctor_name"]
        message = alert_dict["message"]

        # Fetch doctor email/phone for notification
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email, phone FROM doctors WHERE name = ?", (doctor_name,))
        doctor_info = cursor.fetchone()
        doctor_email = doctor_info["email"] if doctor_info else None
        doctor_phone = doctor_info["phone"] if doctor_info else None
        conn.close()

        results = {}
        if "email" in notification_channels and doctor_email:
            email_result = asyncio.run(send_email_notification(
                recipient_email=doctor_email,
                subject=f"Alert for Dr. {doctor_name} from {HOSPITAL_NAME}",
                message=message
            ))
            results["email"] = json.loads(email_result)

        if "whatsapp" in notification_channels and doctor_phone:
            whatsapp_result = asyncio.run(send_whatsapp_message(
                recipient_phone=doctor_phone,
                message=message
            ))
            results["whatsapp"] = json.loads(whatsapp_result)

        # Update alert status to sent
        asyncio.run(update_alert(alert_id, status=AlertStatus.SENT.value))

        return json.dumps({"success": True, "notifications": results})

    except Exception as e:
        logger.error(f"Failed to notify doctor for alert {alert_id}: {str(e)}")
        return json.dumps({"success": False, "error": str(e)})

@mcp_server.tool()
def acknowledge_alert(
    alert_id: str,
    acknowledged_by: str,
    acknowledgment_note: str = ""
) -> str:
    """
    Mark an alert as acknowledged by patient or doctor.
    
    Args:
        alert_id: ID of the alert to acknowledge.
        acknowledged_by: Who acknowledged the alert (patient, doctor, staff).
        acknowledgment_note: Optional note about acknowledgment.
    
    Returns:
        JSON string with success status.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE alerts 
            SET status = ?, acknowledged_by = ?, acknowledgment_note = ?, acknowledged_at = ? 
            WHERE alert_id = ?
        """, (AlertStatus.ACKNOWLEDGED.value, acknowledged_by, acknowledgment_note, datetime.now().isoformat(), alert_id))
        conn.commit()
        conn.close()
        
        if cursor.rowcount == 0:
            return json.dumps({"success": False, "error": f"Alert {alert_id} not found"})

        logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
        
        return json.dumps({
            "success": True,
            "message": "Alert acknowledged successfully"
        })
            
    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@mcp_server.tool()
def create_bulk_alerts(
    alert_type: str,
    appointment_ids: List[str],
    message: str,
    priority: str = "high",
    auto_notify: bool = True
) -> str:
    """
    Create alerts for multiple appointments (e.g., facility closure).
    
    Args:
        alert_type: Type of alert.
        appointment_ids: List of appointment IDs to create alerts for.
        message: Alert message.
        priority: Priority level.
        auto_notify: Whether to automatically send notifications.
    
    Returns:
        JSON string with success status and list of created alert IDs.
    """
    try:
        created_alert_ids = []
        for appt_id in appointment_ids:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT patient_phone, doctor_name FROM appointments WHERE appointment_id = ?", (appt_id,))
            appointment_info = cursor.fetchone()
            conn.close()

            if appointment_info:
                patient_phone = appointment_info["patient_phone"]
                doctor_name = appointment_info["doctor_name"]
                
                result = json.loads(create_alert(
                    alert_type=alert_type,
                    appointment_id=appt_id,
                    patient_phone=patient_phone,
                    message=message,
                    priority=priority,
                    doctor_name=doctor_name,
                    auto_notify=auto_notify
                ))
                if result["success"]:
                    created_alert_ids.append(result["alert_id"])
        
        return json.dumps({
            "success": True,
            "message": f"Created {len(created_alert_ids)} alerts",
            "alert_ids": created_alert_ids
        })
            
    except Exception as e:
        logger.error(f"Failed to create bulk alerts: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@mcp_server.resource("alerts://statistics")
def get_alert_statistics() -> Dict[str, Any]:
    """
    Get real-time statistics about alerts.
    
    Returns:
        Dictionary with alert statistics.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM alerts")
    total_alerts = cursor.fetchone()[0]

    cursor.execute("SELECT status, COUNT(*) FROM alerts GROUP BY status")
    alerts_by_status = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT alert_type, COUNT(*) FROM alerts GROUP BY alert_type")
    alerts_by_type = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()

    return {
        "total_alerts": total_alerts,
        "alerts_by_status": alerts_by_status,
        "alerts_by_type": alerts_by_type,
        "timestamp": datetime.now().isoformat()
    }

@mcp_server.resource("alerts://templates")
def get_alert_templates() -> Dict[str, Any]:
    """
    Get alert message templates.
    
    Returns:
        Dictionary with alert templates.
    """
    return {
        "doctor_late": "Dr. {doctor_name} is running {estimated_delay} late for your appointment on {appointment_date} at {appointment_time}. We apologize for the inconvenience.",
        "appointment_postponed": "Your appointment with Dr. {doctor_name} on {appointment_date} at {appointment_time} has been postponed. New time: {new_appointment_time}.",
        "appointment_cancelled": "Your appointment with Dr. {doctor_name} on {appointment_date} at {appointment_time} has been cancelled. Reason: {reason}.",
        "emergency_reschedule": "Your appointment with Dr. {doctor_name} on {appointment_date} at {appointment_time} has been rescheduled due to an emergency. We will contact you with new available times.",
        "doctor_unavailable": "Dr. {doctor_name} is unavailable on {date}. Your appointment needs to be rescheduled. Reason: {reason}.",
        "facility_closure": "{hospital_name} will be closed on {date} due to {reason}. All appointments on this day are affected.",
        "weather_alert": "Important weather alert: {message}. Your appointment on {appointment_date} at {appointment_time} may be affected. Please check local news for updates.",
        "custom": "{message}"
    }

@mcp_server.prompt("compose_alert_message")
def compose_alert_message(
    alert_type: str,
    patient_name: str,
    doctor_name: str,
    situation_details: str
) -> str:
    """
    Generate appropriate alert message based on situation.
    
    Args:
        alert_type: Type of alert.
        patient_name: Patient's name.
        doctor_name: Doctor's name.
        situation_details: Details about the situation.
    
    Returns:
        Composed alert message.
    """
    return f"Compose a professional and empathetic {alert_type} alert message for {patient_name} regarding their appointment with {doctor_name}. Situation: {situation_details}"


