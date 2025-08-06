"""
Proper MCP Server Implementation using Official MCP Python SDK
Hospital Appointment Scheduler with Multi-Agent Architecture
"""
import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Sequence
from datetime import datetime, timedelta
import logging
from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, Tool, Prompt, TextContent, ImageContent, EmbeddedResource
from mcp.server.models import InitializationOptions
import sqlite3
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastMCP server
mcp_server = FastMCP("Hospital Appointment Scheduler")

# Database connection
DATABASE_PATH = os.getenv('DATABASE_PATH', 'hospital_scheduler.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================================
# APPOINTMENT MANAGEMENT TOOLS
# ============================================================================

@mcp_server.tool()
def schedule_appointment(
    patient_name: str,
    patient_phone: str,
    patient_email: str,
    doctor_name: str,
    department: str,
    appointment_date: str,
    appointment_time: str,
    notes: str = ""
) -> str:
    """
    Schedule a new appointment for a patient.
    
    Args:
        patient_name: Full name of the patient
        patient_phone: Patient's phone number
        patient_email: Patient's email address
        doctor_name: Name of the doctor
        department: Medical department
        appointment_date: Date in YYYY-MM-DD format
        appointment_time: Time in HH:MM format
        notes: Additional notes for the appointment
    
    Returns:
        JSON string with appointment details and confirmation
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if doctor exists
        cursor.execute("SELECT id FROM doctors WHERE name = ?", (doctor_name,))
        doctor = cursor.fetchone()
        
        if not doctor:
            return json.dumps({
                "success": False,
                "error": f"Doctor {doctor_name} not found"
            })
        
        # Check for conflicts
        cursor.execute("""
            SELECT id FROM appointments 
            WHERE doctor_name = ? AND appointment_date = ? AND appointment_time = ?
        """, (doctor_name, appointment_date, appointment_time))
        
        if cursor.fetchone():
            return json.dumps({
                "success": False,
                "error": "Time slot already booked"
            })
        
        # Create appointment
        appointment_id = f"APT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        cursor.execute("""
            INSERT INTO appointments 
            (appointment_id, patient_name, patient_phone, patient_email, 
             doctor_name, department, appointment_date, appointment_time, 
             notes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?)
        """, (appointment_id, patient_name, patient_phone, patient_email,
              doctor_name, department, appointment_date, appointment_time,
              notes, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Appointment scheduled: {appointment_id}")
        
        return json.dumps({
            "success": True,
            "appointment_id": appointment_id,
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "department": department,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "message": "Appointment scheduled successfully"
        })
        
    except Exception as e:
        logger.error(f"Error scheduling appointment: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@mcp_server.tool()
def get_doctor_availability(doctor_name: str, date: str) -> str:
    """
    Get available time slots for a doctor on a specific date.
    
    Args:
        doctor_name: Name of the doctor
        date: Date in YYYY-MM-DD format
    
    Returns:
        JSON string with available time slots
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get doctor info
        cursor.execute("""
            SELECT * FROM doctors WHERE name = ?
        """, (doctor_name,))
        doctor = cursor.fetchone()
        
        if not doctor:
            return json.dumps({
                "success": False,
                "error": f"Doctor {doctor_name} not found"
            })
        
        # Get existing appointments
        cursor.execute("""
            SELECT appointment_time FROM appointments 
            WHERE doctor_name = ? AND appointment_date = ? AND status != 'cancelled'
        """, (doctor_name, date))
        
        booked_times = [row[0] for row in cursor.fetchall()]
        
        # Generate available slots
        available_slots = []
        start_time = datetime.strptime(doctor['start_time'], '%H:%M:%S').time()
        end_time = datetime.strptime(doctor['end_time'], '%H:%M:%S').time()
        duration = doctor['consultation_duration']
        
        current_time = datetime.combine(datetime.today(), start_time)
        end_datetime = datetime.combine(datetime.today(), end_time)
        
        while current_time < end_datetime:
            time_str = current_time.strftime('%H:%M')
            if time_str not in booked_times:
                available_slots.append(time_str)
            current_time += timedelta(minutes=duration)
        
        conn.close()
        
        return json.dumps({
            "success": True,
            "doctor_name": doctor_name,
            "date": date,
            "available_slots": available_slots,
            "consultation_duration": duration
        })
        
    except Exception as e:
        logger.error(f"Error getting doctor availability: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@mcp_server.tool()
def get_patient_appointments(patient_phone: str) -> str:
    """
    Get all appointments for a patient.
    
    Args:
        patient_phone: Patient's phone number
    
    Returns:
        JSON string with patient's appointments
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM appointments 
            WHERE patient_phone = ? 
            ORDER BY appointment_date, appointment_time
        """, (patient_phone,))
        
        appointments = []
        for row in cursor.fetchall():
            appointments.append({
                "appointment_id": row['appointment_id'],
                "patient_name": row['patient_name'],
                "doctor_name": row['doctor_name'],
                "department": row['department'],
                "appointment_date": row['appointment_date'],
                "appointment_time": row['appointment_time'],
                "status": row['status'],
                "notes": row['notes']
            })
        
        conn.close()
        
        return json.dumps({
            "success": True,
            "patient_phone": patient_phone,
            "appointments": appointments,
            "count": len(appointments)
        })
        
    except Exception as e:
        logger.error(f"Error getting patient appointments: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

# ============================================================================
# COMMUNICATION TOOLS
# ============================================================================

@mcp_server.tool()
def send_email_notification(
    recipient_email: str,
    subject: str,
    message: str,
    appointment_details: str = ""
) -> str:
    """
    Send email notification to patient or doctor.
    
    Args:
        recipient_email: Email address of recipient
        subject: Email subject
        message: Email message content
        appointment_details: JSON string with appointment details
    
    Returns:
        JSON string with send status
    """
    try:
        # In a real implementation, this would integrate with Gmail API
        # For now, we'll simulate the email sending
        
        logger.info(f"Email sent to {recipient_email}: {subject}")
        
        return json.dumps({
            "success": True,
            "recipient": recipient_email,
            "subject": subject,
            "message": "Email sent successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@mcp_server.tool()
def send_whatsapp_message(
    recipient_phone: str,
    message: str,
    include_voice: bool = False
) -> str:
    """
    Send WhatsApp message to patient.
    
    Args:
        recipient_phone: Phone number of recipient
        message: Message content
        include_voice: Whether to include voice message
    
    Returns:
        JSON string with send status
    """
    try:
        # In a real implementation, this would integrate with WhatsApp Business API
        # For now, we'll simulate the message sending
        
        logger.info(f"WhatsApp message sent to {recipient_phone}: {message}")
        
        return json.dumps({
            "success": True,
            "recipient": recipient_phone,
            "message": "WhatsApp message sent successfully",
            "include_voice": include_voice,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

# ============================================================================
# DYNAMIC ALERTS TOOLS
# ============================================================================

@mcp_server.tool()
def create_dynamic_alert(
    alert_type: str,
    appointment_id: str,
    message: str,
    priority: str = "medium",
    estimated_delay: str = "",
    new_appointment_time: str = ""
) -> str:
    """
    Create a dynamic alert for appointment changes.
    
    Args:
        alert_type: Type of alert (doctor_late, appointment_postponed, etc.)
        appointment_id: ID of the affected appointment
        message: Alert message
        priority: Priority level (low, medium, high, urgent)
        estimated_delay: Estimated delay time
        new_appointment_time: New appointment time if rescheduled
    
    Returns:
        JSON string with alert creation status
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get appointment details
        cursor.execute("""
            SELECT * FROM appointments WHERE appointment_id = ?
        """, (appointment_id,))
        appointment = cursor.fetchone()
        
        if not appointment:
            return json.dumps({
                "success": False,
                "error": f"Appointment {appointment_id} not found"
            })
        
        # Create alert
        alert_id = f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        cursor.execute("""
            INSERT INTO alerts 
            (alert_id, alert_type, appointment_id, patient_phone, 
             message, priority, estimated_delay, new_appointment_time, 
             status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (alert_id, alert_type, appointment_id, appointment['patient_phone'],
              message, priority, estimated_delay, new_appointment_time,
              datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Dynamic alert created: {alert_id}")
        
        return json.dumps({
            "success": True,
            "alert_id": alert_id,
            "alert_type": alert_type,
            "appointment_id": appointment_id,
            "message": "Alert created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating dynamic alert: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@mcp_server.tool()
def get_active_alerts(patient_phone: str = "", priority: str = "") -> str:
    """
    Get active alerts for a patient or all patients.
    
    Args:
        patient_phone: Phone number of patient (optional)
        priority: Filter by priority level (optional)
    
    Returns:
        JSON string with active alerts
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM alerts WHERE status = 'pending'"
        params = []
        
        if patient_phone:
            query += " AND patient_phone = ?"
            params.append(patient_phone)
        
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                "alert_id": row['alert_id'],
                "alert_type": row['alert_type'],
                "appointment_id": row['appointment_id'],
                "patient_phone": row['patient_phone'],
                "message": row['message'],
                "priority": row['priority'],
                "estimated_delay": row['estimated_delay'],
                "new_appointment_time": row['new_appointment_time'],
                "created_at": row['created_at']
            })
        
        conn.close()
        
        return json.dumps({
            "success": True,
            "alerts": alerts,
            "count": len(alerts)
        })
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

# ============================================================================
# SMART SCHEDULING TOOLS
# ============================================================================

@mcp_server.tool()
def get_smart_recommendations(
    department: str,
    preferred_date: str = "",
    preferred_time: str = "",
    patient_history: str = ""
) -> str:
    """
    Get smart appointment recommendations based on various factors.
    
    Args:
        department: Medical department
        preferred_date: Patient's preferred date
        preferred_time: Patient's preferred time
        patient_history: Patient's appointment history
    
    Returns:
        JSON string with smart recommendations
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get doctors in department
        cursor.execute("""
            SELECT * FROM doctors WHERE department = ?
        """, (department,))
        doctors = cursor.fetchall()
        
        if not doctors:
            return json.dumps({
                "success": False,
                "error": f"No doctors found in {department} department"
            })
        
        recommendations = []
        
        for doctor in doctors:
            # Get doctor's availability for next 7 days
            for i in range(7):
                check_date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
                
                # Get available slots
                cursor.execute("""
                    SELECT appointment_time FROM appointments 
                    WHERE doctor_name = ? AND appointment_date = ? AND status != 'cancelled'
                """, (doctor['name'], check_date))
                
                booked_times = [row[0] for row in cursor.fetchall()]
                
                # Generate available slots
                start_time = datetime.strptime(doctor['start_time'], '%H:%M:%S').time()
                end_time = datetime.strptime(doctor['end_time'], '%H:%M:%S').time()
                duration = doctor['consultation_duration']
                
                current_time = datetime.combine(datetime.today(), start_time)
                end_datetime = datetime.combine(datetime.today(), end_time)
                
                available_slots = []
                while current_time < end_datetime:
                    time_str = current_time.strftime('%H:%M')
                    if time_str not in booked_times:
                        available_slots.append(time_str)
                    current_time += timedelta(minutes=duration)
                
                if available_slots:
                    recommendations.append({
                        "doctor_name": doctor['name'],
                        "specialization": doctor['specialization'],
                        "date": check_date,
                        "available_slots": available_slots[:3],  # Top 3 slots
                        "consultation_duration": duration,
                        "recommendation_score": 0.8  # Placeholder scoring
                    })
        
        # Sort by recommendation score
        recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        conn.close()
        
        return json.dumps({
            "success": True,
            "department": department,
            "recommendations": recommendations[:5],  # Top 5 recommendations
            "total_options": len(recommendations)
        })
        
    except Exception as e:
        logger.error(f"Error getting smart recommendations: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

# ============================================================================
# RESOURCES
# ============================================================================

@mcp_server.resource("hospital://doctors")
def get_doctors_resource() -> str:
    """Get list of all doctors and their information."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM doctors")
        doctors = []
        
        for row in cursor.fetchall():
            doctors.append({
                "id": row['id'],
                "name": row['name'],
                "specialization": row['specialization'],
                "department": row['department'],
                "available_days": json.loads(row['available_days']),
                "start_time": row['start_time'],
                "end_time": row['end_time'],
                "consultation_duration": row['consultation_duration']
            })
        
        conn.close()
        
        return json.dumps({
            "doctors": doctors,
            "total_count": len(doctors),
            "last_updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting doctors resource: {str(e)}")
        return json.dumps({"error": str(e)})

@mcp_server.resource("hospital://departments")
def get_departments_resource() -> str:
    """Get list of all medical departments."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT department FROM doctors")
        departments = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return json.dumps({
            "departments": departments,
            "total_count": len(departments),
            "last_updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting departments resource: {str(e)}")
        return json.dumps({"error": str(e)})

@mcp_server.resource("hospital://appointments/{date}")
def get_appointments_by_date(date: str) -> str:
    """Get all appointments for a specific date."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM appointments 
            WHERE appointment_date = ? 
            ORDER BY appointment_time
        """, (date,))
        
        appointments = []
        for row in cursor.fetchall():
            appointments.append({
                "appointment_id": row['appointment_id'],
                "patient_name": row['patient_name'],
                "doctor_name": row['doctor_name'],
                "department": row['department'],
                "appointment_time": row['appointment_time'],
                "status": row['status']
            })
        
        conn.close()
        
        return json.dumps({
            "date": date,
            "appointments": appointments,
            "total_count": len(appointments),
            "last_updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting appointments for date {date}: {str(e)}")
        return json.dumps({"error": str(e)})

# ============================================================================
# PROMPTS
# ============================================================================

@mcp_server.prompt()
def appointment_confirmation_prompt(
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    department: str
) -> str:
    """Generate appointment confirmation message."""
    return f"""
    Generate a professional and friendly appointment confirmation message for:
    
    Patient: {patient_name}
    Doctor: {doctor_name}
    Department: {department}
    Date: {appointment_date}
    Time: {appointment_time}
    
    The message should be warm, professional, and include important reminders like:
    - Arriving 15 minutes early
    - Bringing ID and insurance card
    - Contact information for changes
    
    Format the message for both email and SMS use.
    """

@mcp_server.prompt()
def appointment_reminder_prompt(
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    reminder_type: str = "24_hour"
) -> str:
    """Generate appointment reminder message."""
    reminder_timing = {
        "24_hour": "tomorrow",
        "2_hour": "in 2 hours",
        "1_hour": "in 1 hour"
    }.get(reminder_type, "soon")
    
    return f"""
    Generate a friendly appointment reminder message for:
    
    Patient: {patient_name}
    Doctor: {doctor_name}
    Date: {appointment_date}
    Time: {appointment_time}
    Reminder timing: {reminder_timing}
    
    The message should be concise, friendly, and include:
    - Clear appointment details
    - Reminder to arrive early
    - Contact information for changes
    - Appropriate urgency based on timing
    
    Keep it under 160 characters for SMS compatibility.
    """

@mcp_server.prompt()
def dynamic_alert_prompt(
    alert_type: str,
    patient_name: str,
    doctor_name: str,
    situation_details: str
) -> str:
    """Generate dynamic alert message for appointment changes."""
    return f"""
    Generate an empathetic and professional alert message for:
    
    Alert Type: {alert_type}
    Patient: {patient_name}
    Doctor: {doctor_name}
    Situation: {situation_details}
    
    The message should:
    - Be empathetic and apologetic for any inconvenience
    - Clearly explain the situation
    - Provide next steps or alternatives
    - Maintain professional tone while being understanding
    - Include contact information for assistance
    
    Adapt the tone and content based on the alert type (doctor late, appointment postponed, emergency, etc.).
    """

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def initialize_database():
    """Initialize the database with required tables."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialization TEXT NOT NULL,
                department TEXT NOT NULL,
                available_days TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                consultation_duration INTEGER NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id TEXT UNIQUE NOT NULL,
                patient_name TEXT NOT NULL,
                patient_phone TEXT NOT NULL,
                patient_email TEXT NOT NULL,
                doctor_name TEXT NOT NULL,
                department TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                notes TEXT,
                status TEXT DEFAULT 'scheduled',
                created_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE NOT NULL,
                alert_type TEXT NOT NULL,
                appointment_id TEXT NOT NULL,
                patient_phone TEXT NOT NULL,
                message TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                estimated_delay TEXT,
                new_appointment_time TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")

# Initialize database on module load
initialize_database()

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Run the MCP server
    mcp_server.run()

