"""
Gmail Agent for Hospital Appointment Scheduler
Handles email communication using Gmail API with MCP integration
"""
import os
import json
import base64
import asyncio
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import imaplib
import email
from datetime import datetime
import logging

from src.mcp.mcp_server_proper import mcp_server, get_db_connection # Import mcp_server instance

logger = logging.getLogger(__name__)

# Email configuration (can be moved to a config file or environment variables)
SMTP_SERVER = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.getenv("SMTP_USERNAME", "")
EMAIL_PASSWORD = os.getenv("SMTP_PASSWORD", "")
HOSPITAL_NAME = os.getenv("HOSPITAL_NAME", "City General Hospital")

@mcp_server.tool()
def send_email_notification(
    recipient_email: str,
    subject: str,
    message: str,
    is_html: bool = False,
    attachments: List[Dict] = None
) -> str:
    """
    Send email notification to patient or doctor.
    
    Args:
        recipient_email: Email address of recipient
        subject: Email subject
        message: Email message content
        is_html: Whether the message content is HTML formatted
        attachments: Optional list of attachments, each with filename, content (base64 encoded), and content_type
    
    Returns:
        JSON string with send status
    """
    try:
        if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
            return json.dumps({
                "success": False,
                "error": "Email credentials not configured. Please set SMTP_USERNAME and SMTP_PASSWORD environment variables."
            })
        
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{HOSPITAL_NAME} <{EMAIL_ADDRESS}>"
        msg["To"] = recipient_email
        msg["Subject"] = subject
        
        if is_html:
            msg.attach(MIMEText(message, "html"))
        else:
            msg.attach(MIMEText(message, "plain"))
        
        if attachments:
            for attachment in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(base64.b64decode(attachment["content"]))
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {attachment["filename"]}"
                )
                msg.attach(part)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {recipient_email}")
        return json.dumps({
            "success": True,
            "recipient": recipient_email,
            "subject": subject,
            "message": "Email sent successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@mcp_server.tool()
def send_appointment_confirmation_email(
    patient_email: str,
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    department: str,
    hospital_address: str = "123 Medical Center Dr, City, State 12345",
    special_instructions: str = ""
) -> str:
    """
    Send appointment confirmation email to patient.
    
    Args:
        patient_email: Patient's email address
        patient_name: Full name of the patient
        doctor_name: Name of the doctor
        appointment_date: Date in YYYY-MM-DD format
        appointment_time: Time in HH:MM format
        department: Medical department
        hospital_address: Address of the hospital
        special_instructions: Any special instructions for the patient
    
    Returns:
        JSON string with send status
    """
    subject = f"Appointment Confirmation - {HOSPITAL_NAME}"
    body = f"""
    <html>
    <body>
        <p>Dear {patient_name},</p>
        <p>Your appointment has been successfully confirmed at {HOSPITAL_NAME}.</p>
        <p><strong>Doctor:</strong> {doctor_name}</p>
        <p><strong>Department:</strong> {department}</p>
        <p><strong>Date:</strong> {appointment_date}</p>
        <p><strong>Time:</strong> {appointment_time}</p>
        <p><strong>Location:</strong> {hospital_address}</p>
        <p>{special_instructions}</p>
        <p>Please arrive 15 minutes prior to your appointment time. We look forward to seeing you.</p>
        <p>Sincerely,<br>{HOSPITAL_NAME} Team</p>
    </body>
    </html>
    """
    return send_email_notification(patient_email, subject, body, is_html=True)

@mcp_server.tool()
def send_appointment_reminder_email(
    patient_email: str,
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    department: str,
    reminder_type: str = "24_hour"
) -> str:
    """
    Send appointment reminder email to patient.
    
    Args:
        patient_email: Patient's email address
        patient_name: Full name of the patient
        doctor_name: Name of the doctor
        appointment_date: Date in YYYY-MM-DD format
        appointment_time: Time in HH:MM format
        department: Medical department
        reminder_type: Type of reminder (e.g., "24_hour", "2_hour")
    
    Returns:
        JSON string with send status
    """
    reminder_text = {
        "24_hour": "tomorrow",
        "2_hour": "in 2 hours",
        "custom": "soon"
    }.get(reminder_type, "soon")
    
    subject = f"Appointment Reminder - {reminder_text.title()} - {HOSPITAL_NAME}"
    body = f"""
    <html>
    <body>
        <p>Dear {patient_name},</p>
        <p>This is a friendly reminder about your upcoming appointment at {HOSPITAL_NAME} {reminder_text}.</p>
        <p><strong>Doctor:</strong> {doctor_name}</p>
        <p><strong>Department:</strong> {department}</p>
        <p><strong>Date:</strong> {appointment_date}</p>
        <p><strong>Time:</strong> {appointment_time}</p>
        <p>Please ensure you are ready for your appointment. If you need to reschedule or cancel, please contact us as soon as possible.</p>
        <p>Sincerely,<br>{HOSPITAL_NAME} Team</p>
    </body>
    </html>
    """
    return send_email_notification(patient_email, subject, body, is_html=True)

@mcp_server.tool()
def send_appointment_cancellation_email(
    patient_email: str,
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    reason: str = "",
    reschedule_options: List[str] = None
) -> str:
    """
    Send appointment cancellation email to patient.
    
    Args:
        patient_email: Patient's email address
        patient_name: Full name of the patient
        doctor_name: Name of the doctor
        appointment_date: Date in YYYY-MM-DD format
        appointment_time: Time in HH:MM format
        reason: Reason for cancellation
        reschedule_options: List of suggested reschedule options
    
    Returns:
        JSON string with send status
    """
    subject = f"Appointment Cancellation - {HOSPITAL_NAME}"
    
    reschedule_text = ""
    if reschedule_options:
        reschedule_text = "<p>You can reschedule your appointment using the following options:</p><ul>"
        for option in reschedule_options:
            reschedule_text += f"<li>{option}</li>"
        reschedule_text += "</ul>"

    body = f"""
    <html>
    <body>
        <p>Dear {patient_name},</p>
        <p>We regret to inform you that your appointment with Dr. {doctor_name} in the {department} department on {appointment_date} at {appointment_time} has been cancelled.</p>
        <p><strong>Reason for cancellation:</strong> {reason if reason else 

