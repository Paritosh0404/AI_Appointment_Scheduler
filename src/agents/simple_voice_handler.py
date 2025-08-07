"""
Simple Voice Request Handler
A simplified version that processes voice requests without complex MCP dependencies
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

async def handle_voice_request(transcript: str) -> Dict[str, Any]:
    """
    Handle voice request with simple natural language processing
    """
    try:
        transcript_lower = transcript.lower()
        response = {
            "success": True,
            "response": "",
            "suggestions": [],
            "action_type": "general"
        }
        
        # Check for appointment scheduling requests
        if any(keyword in transcript_lower for keyword in ["appointment", "schedule", "book", "reserve"]):
            response["action_type"] = "schedule_appointment"
            response["response"] = "I can help you schedule an appointment. Please provide the following information:\n1. Doctor's name or specialty\n2. Preferred date\n3. Preferred time\n4. Your contact information"
            response["suggestions"] = [
                "I want to see Dr. Smith next week",
                "Schedule with a cardiologist tomorrow",
                "Book appointment for Friday 2pm"
            ]
        
        # Check for doctor search requests  
        elif any(keyword in transcript_lower for keyword in ["doctor", "physician", "specialist"]):
            response["action_type"] = "find_doctor"
            response["response"] = "I can help you find the right doctor. Here are our available specialists:\n• Dr. Sarah Johnson - Cardiologist\n• Dr. Michael Chen - Neurologist\n• Dr. Emily Davis - Pediatrician\n• Dr. Robert Wilson - Orthopedist"
            response["suggestions"] = [
                "Show me available cardiologists",
                "I need a pediatrician",
                "Find orthopedic specialists"
            ]
        
        # Check for availability requests
        elif any(keyword in transcript_lower for keyword in ["available", "availability", "free", "open"]):
            response["action_type"] = "check_availability"
            response["response"] = "Let me check availability for you. Our doctors typically have openings:\n• Morning slots: 9:00 AM - 12:00 PM\n• Afternoon slots: 2:00 PM - 5:00 PM\n• Evening slots: 6:00 PM - 8:00 PM"
            response["suggestions"] = [
                "Check Dr. Smith's availability",
                "Show morning appointments",
                "What's available next week?"
            ]
        
        # Check for appointment changes/cancellation
        elif any(keyword in transcript_lower for keyword in ["cancel", "reschedule", "change", "modify"]):
            response["action_type"] = "modify_appointment"
            response["response"] = "I can help you modify or cancel an appointment. Please provide your appointment details or patient ID so I can locate your booking."
            response["suggestions"] = [
                "Cancel my appointment with Dr. Smith",
                "Reschedule to next Tuesday",
                "Change appointment time"
            ]
        
        # Check for appointment list/history
        elif any(keyword in transcript_lower for keyword in ["my appointments", "appointment list", "upcoming", "history"]):
            response["action_type"] = "list_appointments"
            response["response"] = "I can show you your appointment history. Please provide your phone number or patient ID to retrieve your appointments."
            response["suggestions"] = [
                "Show my upcoming appointments",
                "List all my appointments",
                "What appointments do I have this week?"
            ]
        
        # Default response for unclear requests
        else:
            response["response"] = "I'm your hospital appointment assistant. I can help you with:\n• Scheduling new appointments\n• Finding doctors and specialists\n• Checking availability\n• Modifying existing appointments\n• Viewing your appointment history\n\nWhat would you like to do today?"
            response["suggestions"] = [
                "Schedule an appointment",
                "Find a doctor",
                "Check my appointments",
                "Cancel an appointment"
            ]
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing voice request: {str(e)}")
        return {
            "success": False,
            "response": "I apologize, but I'm having trouble processing your request right now. Please try again or contact our reception desk for assistance.",
            "error": str(e)
        }

async def process_appointment_request(user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process appointment request with context and return properly formatted response
    """
    if context is None:
        context = {}
    
    try:
        # Get the voice processing response
        voice_response = await handle_voice_request(user_input)
        
        # Extract information from the user input using simple parsing
        parsed_data = extract_appointment_info(user_input)
        
        # Return in the format expected by the frontend
        result = {
            "success": True,
            "parsed_data": parsed_data,
            "response": voice_response.get("response", "I can help you with that request."),
            "suggestions": voice_response.get("suggestions", []),
            "action_type": voice_response.get("action_type", "general")
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing appointment request: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "parsed_data": {}
        }

def extract_appointment_info(user_input: str) -> Dict[str, Any]:
    """
    Extract appointment information from user input using simple pattern matching
    """
    user_input_lower = user_input.lower()
    info = {}
    
    # Extract patient name (look for patterns like "for John" or "my name is Sarah")
    name_patterns = [
        r"for ([A-Za-z\s]+)",
        r"my name is ([A-Za-z\s]+)",
        r"i am ([A-Za-z\s]+)",
        r"patient ([A-Za-z\s]+)",
        r"appointment for ([A-Za-z\s]+)"  # Added pattern for form-generated text
    ]
    
    import re
    for pattern in name_patterns:
        match = re.search(pattern, user_input_lower)
        if match:
            name = match.group(1).strip()
            # Clean up name by removing "(phone:" part if present
            if "(phone:" in name:
                name = name.split("(phone:")[0].strip()
            info["patient_name"] = name.title()
            break
    
    # Extract phone number
    phone_pattern = r"phone:\s*([+\-\(\)\s\d]+)\)"
    phone_match = re.search(phone_pattern, user_input)
    if phone_match:
        info["patient_phone"] = phone_match.group(1).strip()
    else:
        # Fallback pattern for standalone phone numbers
        phone_pattern = r"(\+?\d{1,3}[-.\s]?)?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})"
        phone_match = re.search(phone_pattern, user_input)
        if phone_match:
            info["patient_phone"] = phone_match.group(0)
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, user_input)
    if email_match:
        info["patient_email"] = email_match.group(0)
        info["patient_email"] = email_match.group(0)
    
    # Extract department/specialization - improved for form-generated text
    departments = {
        "cardiology": ["cardiology", "cardiologist", "heart", "cardiac"],
        "dermatology": ["dermatology", "dermatologist", "skin"],
        "general": ["general", "gp", "family doctor"],
        "orthopedics": ["orthopedics", "orthopedist", "bone", "joint"],
        "pediatrics": ["pediatrics", "pediatrician", "child", "kids"],
        "neurology": ["neurology", "neurologist", "brain", "nerve"]
    }
    
    # First try to find " in [department] department" pattern from form
    dept_pattern = r" in ([a-z]+) department"
    dept_match = re.search(dept_pattern, user_input_lower)
    if dept_match:
        dept_name = dept_match.group(1).strip()
        if dept_name in departments:
            info["department_preference"] = dept_name
    else:
        # Fallback to keyword matching
        for dept, keywords in departments.items():
            if any(keyword in user_input_lower for keyword in keywords):
                info["department_preference"] = dept
                break
    
    # Extract date patterns - improved for form dates
    # First try to match YYYY-MM-DD format from form
    date_pattern = r"on (\d{4}-\d{2}-\d{2})"
    date_match = re.search(date_pattern, user_input)
    if date_match:
        info["preferred_date"] = date_match.group(1)
    else:
        # Fallback to natural language date keywords
        date_keywords = {
            "today": 0,
            "tomorrow": 1,
            "next week": 7,
            "monday": "monday",
            "tuesday": "tuesday", 
            "wednesday": "wednesday",
            "thursday": "thursday",
            "friday": "friday"
        }
        
        for date_word, offset in date_keywords.items():
            if date_word in user_input_lower:
                if isinstance(offset, int):
                    from datetime import datetime, timedelta
                    target_date = datetime.now() + timedelta(days=offset)
                    info["preferred_date"] = target_date.strftime("%Y-%m-%d")
                else:
                    info["preferred_date_text"] = offset
                break
    
    # Extract reason/notes - improved for form text
    # First try to match "Reason: [text]" pattern from form
    reason_pattern = r"reason:\s*(.+?)(?:\s*$|\s*\.|$)"
    reason_match = re.search(reason_pattern, user_input_lower)
    if reason_match:
        reason = reason_match.group(1).strip()
        if len(reason) > 2:  # Only use substantial reasons
            info["reason"] = reason.title()
    else:
        # Fallback to other patterns
        reason_patterns = [
            r"for (.+?)(?:\s+on\s+|\s+at\s+|\s+with\s+|$)",
            r"because (.+?)(?:\s+on\s+|\s+at\s+|\s+with\s+|$)"
        ]
        
        for pattern in reason_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                reason = match.group(1).strip()
                if len(reason) > 5:  # Only use substantial reasons
                    info["reason"] = reason.title()
                    break
    
    return info
    
def process_appointment_request_sync(user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Synchronous version of process_appointment_request for Flask compatibility
    """
    if context is None:
        context = {}
    
    try:
        # Get the voice processing response (sync version)
        voice_response = handle_voice_request_sync(user_input)
        
        # Extract information from the user input using simple parsing
        parsed_data = extract_appointment_info(user_input)
        
        # Return in the format expected by the frontend
        result = {
            "success": True,
            "parsed_data": parsed_data,
            "response": voice_response.get("response", "I can help you with that request."),
            "suggestions": voice_response.get("suggestions", []),
            "action_type": voice_response.get("action_type", "general")
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing appointment request: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "parsed_data": {}
        }

def handle_voice_request_sync(transcript: str) -> Dict[str, Any]:
    """
    Synchronous version of handle_voice_request for Flask compatibility
    """
    try:
        transcript_lower = transcript.lower()
        response = {
            "success": True,
            "response": "",
            "suggestions": [],
            "action_type": "general"
        }
        
        # Check for appointment scheduling requests
        if any(keyword in transcript_lower for keyword in ["appointment", "schedule", "book", "reserve"]):
            response["action_type"] = "schedule_appointment"
            response["response"] = "I can help you schedule an appointment. Please provide the following information:\n1. Doctor's name or specialty\n2. Preferred date\n3. Preferred time\n4. Your contact information"
            response["suggestions"] = [
                "I want to see Dr. Smith next week",
                "Schedule with a cardiologist tomorrow",
                "Book appointment for Friday 2pm"
            ]
        
        # Check for doctor search requests  
        elif any(keyword in transcript_lower for keyword in ["doctor", "physician", "specialist"]):
            response["action_type"] = "find_doctor"
            response["response"] = "I can help you find the right doctor. Here are our available specialists:\n• Dr. Sarah Johnson - Cardiologist\n• Dr. Michael Chen - Neurologist\n• Dr. Emily Davis - Pediatrician\n• Dr. Robert Wilson - Orthopedist"
            response["suggestions"] = [
                "Show me available cardiologists",
                "I need a pediatrician",
                "Find orthopedic specialists"
            ]
        
        # Check for availability requests
        elif any(keyword in transcript_lower for keyword in ["available", "availability", "free", "open"]):
            response["action_type"] = "check_availability"
            response["response"] = "Let me check availability for you. Our doctors typically have openings:\n• Morning slots: 9:00 AM - 12:00 PM\n• Afternoon slots: 2:00 PM - 5:00 PM\n• Evening slots: 6:00 PM - 8:00 PM"
            response["suggestions"] = [
                "Check Dr. Smith's availability",
                "Show morning appointments",
                "What's available next week?"
            ]
        
        # Check for appointment changes/cancellation
        elif any(keyword in transcript_lower for keyword in ["cancel", "reschedule", "change", "modify"]):
            response["action_type"] = "modify_appointment"
            response["response"] = "I can help you modify or cancel an appointment. Please provide your appointment details or patient ID so I can locate your booking."
            response["suggestions"] = [
                "Cancel my appointment with Dr. Smith",
                "Reschedule to next Tuesday",
                "Change appointment time"
            ]
        
        # Check for appointment list/history
        elif any(keyword in transcript_lower for keyword in ["my appointments", "appointment list", "upcoming", "history"]):
            response["action_type"] = "list_appointments"
            response["response"] = "I can show you your appointment history. Please provide your phone number or patient ID to retrieve your appointments."
            response["suggestions"] = [
                "Show my upcoming appointments",
                "List all my appointments",
                "What appointments do I have this week?"
            ]
        
        # Default response for unclear requests
        else:
            response["response"] = "I'm your hospital appointment assistant. I can help you with:\n• Scheduling new appointments\n• Finding doctors and specialists\n• Checking availability\n• Modifying existing appointments\n• Viewing your appointment history\n\nWhat would you like to do today?"
            response["suggestions"] = [
                "Schedule an appointment",
                "Find a doctor",
                "Check my appointments",
                "Cancel an appointment"
            ]
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing voice request: {str(e)}")
        return {
            "success": False,
            "response": "I apologize, but I'm having trouble processing your request right now. Please try again or contact our reception desk for assistance.",
            "error": str(e)
        }

    return info
