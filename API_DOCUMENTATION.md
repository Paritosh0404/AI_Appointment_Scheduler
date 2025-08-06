# 📚 Hospital Appointment Scheduler - API Documentation

## 🌐 **Base URL**
```
http://localhost:5000
```

## 🔐 **Authentication**
Currently using session-based authentication. For production, implement JWT or OAuth2.

---

## 📋 **Core Endpoints**

### **Health & Status**

#### **GET /health**
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-08T12:00:00Z",
  "service": "Hospital Appointment Scheduler",
  "version": "2.0.0",
  "features": [
    "Voice Interaction",
    "Smart Scheduling",
    "Dynamic Alerts",
    "Email & WhatsApp Integration",
    "User & Doctor Dashboards",
    "MCP Multi-Agent Architecture"
  ]
}
```

#### **GET /api/system/status**
Detailed system status and metrics.

**Response:**
```json
{
  "status": "operational",
  "database": "connected",
  "doctors": 8,
  "appointments": 42,
  "mcp_server": "running",
  "agents": {
    "appointment_agent": "active",
    "voice_agent": "active",
    "gmail_agent": "active",
    "whatsapp_agent": "active",
    "alerts_agent": "active"
  },
  "timestamp": "2025-01-08T12:00:00Z"
}
```

#### **GET /api/features**
List of available features and their endpoints.

**Response:**
```json
{
  "features": {
    "voice_interaction": {
      "name": "Voice Interaction",
      "description": "Natural language voice commands for appointment scheduling",
      "status": "active",
      "endpoint": "/api/voice/process"
    },
    "smart_scheduling": {
      "name": "Smart Scheduling",
      "description": "AI-powered appointment recommendations",
      "status": "active",
      "endpoint": "/api/appointments/smart_recommendations"
    }
  }
}
```

---

## 🗓️ **Appointment Management**

### **POST /api/appointments/schedule**
Schedule a new appointment.

**Request Body:**
```json
{
  "patient_name": "John Doe",
  "patient_phone": "+1234567890",
  "patient_email": "john.doe@email.com",
  "doctor_name": "Dr. Sarah Johnson",
  "department": "Cardiology",
  "appointment_date": "2025-01-15",
  "appointment_time": "10:00",
  "notes": "Regular checkup",
  "preferred_language": "en"
}
```

**Response:**
```json
{
  "success": true,
  "appointment": {
    "appointment_id": "APT_20250108_120000_001",
    "patient_name": "John Doe",
    "doctor_name": "Dr. Sarah Johnson",
    "department": "Cardiology",
    "appointment_date": "2025-01-15",
    "appointment_time": "10:00",
    "status": "scheduled",
    "created_at": "2025-01-08T12:00:00Z"
  },
  "notifications_sent": {
    "email": true,
    "whatsapp": true,
    "voice_confirmation": false
  }
}
```

### **GET /api/appointments/search**
Search appointments by various criteria.

**Query Parameters:**
- `patient_phone` (string): Patient phone number
- `doctor_name` (string): Doctor name
- `department` (string): Department name
- `date_from` (string): Start date (YYYY-MM-DD)
- `date_to` (string): End date (YYYY-MM-DD)
- `status` (string): Appointment status

**Example:**
```
GET /api/appointments/search?patient_phone=+1234567890&status=scheduled
```

**Response:**
```json
{
  "success": true,
  "appointments": [
    {
      "appointment_id": "APT_20250108_120000_001",
      "patient_name": "John Doe",
      "patient_phone": "+1234567890",
      "doctor_name": "Dr. Sarah Johnson",
      "department": "Cardiology",
      "appointment_date": "2025-01-15",
      "appointment_time": "10:00",
      "status": "scheduled",
      "notes": "Regular checkup"
    }
  ],
  "total_count": 1
}
```

### **PUT /api/appointments/{appointment_id}/reschedule**
Reschedule an existing appointment.

**Request Body:**
```json
{
  "new_date": "2025-01-16",
  "new_time": "14:00",
  "reason": "Patient request",
  "notify_patient": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Appointment rescheduled successfully",
  "old_appointment": {
    "date": "2025-01-15",
    "time": "10:00"
  },
  "new_appointment": {
    "date": "2025-01-16",
    "time": "14:00"
  },
  "notifications_sent": ["email", "whatsapp"]
}
```

### **DELETE /api/appointments/{appointment_id}/cancel**
Cancel an appointment.

**Request Body:**
```json
{
  "reason": "Patient cancellation",
  "notify_patient": true,
  "refund_required": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Appointment cancelled successfully",
  "appointment_id": "APT_20250108_120000_001",
  "cancellation_time": "2025-01-08T12:00:00Z"
}
```

---

## 🎤 **Voice Interaction**

### **POST /api/voice/process**
Process voice input for appointment scheduling.

**Request Body:**
```json
{
  "audio_data": "base64_encoded_audio",
  "session_id": "voice_session_123",
  "language": "en-US"
}
```

**Response:**
```json
{
  "success": true,
  "transcription": "I need to schedule an appointment with a cardiologist",
  "intent": "schedule_appointment",
  "extracted_info": {
    "department": "Cardiology",
    "urgency": "routine",
    "preferred_timeframe": "next_week"
  },
  "response_text": "I can help you schedule a cardiology appointment. What's your preferred date?",
  "response_audio": "base64_encoded_audio_response",
  "next_step": "collect_date_preference"
}
```

### **POST /api/voice/session/start**
Start a new voice interaction session.

**Request Body:**
```json
{
  "patient_phone": "+1234567890",
  "language": "en-US"
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "voice_session_123",
  "welcome_message": "Hello! I'm your hospital appointment assistant. How can I help you today?",
  "welcome_audio": "base64_encoded_audio"
}
```

### **POST /api/voice/session/{session_id}/end**
End a voice interaction session.

**Response:**
```json
{
  "success": true,
  "session_summary": {
    "duration": "00:03:45",
    "interactions": 8,
    "appointments_scheduled": 1,
    "satisfaction_rating": null
  }
}
```

---

## 👨‍⚕️ **Doctor Management**

### **GET /api/doctors**
Get list of all doctors.

**Query Parameters:**
- `department` (string): Filter by department
- `available_date` (string): Filter by availability on specific date

**Response:**
```json
{
  "success": true,
  "doctors": [
    {
      "id": 1,
      "name": "Dr. Sarah Johnson",
      "specialization": "Cardiology",
      "department": "Cardiology",
      "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "start_time": "09:00:00",
      "end_time": "17:00:00",
      "consultation_duration": 30
    }
  ]
}
```

### **GET /api/doctors/{doctor_name}/availability**
Get doctor's availability for a specific date range.

**Query Parameters:**
- `start_date` (string): Start date (YYYY-MM-DD)
- `end_date` (string): End date (YYYY-MM-DD)

**Response:**
```json
{
  "success": true,
  "doctor_name": "Dr. Sarah Johnson",
  "availability": [
    {
      "date": "2025-01-15",
      "available_slots": [
        "09:00", "09:30", "10:00", "10:30",
        "14:00", "14:30", "15:00", "15:30"
      ],
      "booked_slots": ["11:00", "11:30", "16:00", "16:30"]
    }
  ]
}
```

### **POST /api/doctors/{doctor_name}/schedule**
Get doctor's schedule for a specific date range.

**Request Body:**
```json
{
  "start_date": "2025-01-15",
  "end_date": "2025-01-21"
}
```

**Response:**
```json
{
  "success": true,
  "doctor_name": "Dr. Sarah Johnson",
  "schedule": [
    {
      "appointment_id": "APT_20250108_120000_001",
      "patient_name": "John Doe",
      "appointment_date": "2025-01-15",
      "appointment_time": "10:00",
      "duration": 30,
      "status": "scheduled",
      "notes": "Regular checkup"
    }
  ]
}
```

---

## 🚨 **Alert Management**

### **POST /api/alerts/create**
Create a new alert for appointment changes.

**Request Body:**
```json
{
  "alert_type": "doctor_late",
  "appointment_id": "APT_20250108_120000_001",
  "message": "Dr. Johnson is running 30 minutes late",
  "priority": "high",
  "estimated_delay": "30 minutes",
  "channels": ["email", "whatsapp", "voice"]
}
```

**Response:**
```json
{
  "success": true,
  "alert_id": "ALERT_20250108_120000_001",
  "message": "Alert created and notifications sent",
  "notifications_sent": {
    "email": true,
    "whatsapp": true,
    "voice": false
  }
}
```

### **GET /api/alerts**
Get list of alerts.

**Query Parameters:**
- `appointment_id` (string): Filter by appointment
- `status` (string): Filter by status (pending, sent, failed)
- `priority` (string): Filter by priority (low, medium, high)

**Response:**
```json
{
  "success": true,
  "alerts": [
    {
      "alert_id": "ALERT_20250108_120000_001",
      "alert_type": "doctor_late",
      "appointment_id": "APT_20250108_120000_001",
      "message": "Dr. Johnson is running 30 minutes late",
      "priority": "high",
      "status": "sent",
      "created_at": "2025-01-08T12:00:00Z"
    }
  ]
}
```

### **PUT /api/alerts/{alert_id}/status**
Update alert status.

**Request Body:**
```json
{
  "status": "acknowledged",
  "notes": "Patient notified and confirmed"
}
```

---

## 📧 **Communication**

### **POST /api/notifications/email**
Send email notification.

**Request Body:**
```json
{
  "to_email": "patient@email.com",
  "template": "appointment_confirmation",
  "data": {
    "patient_name": "John Doe",
    "doctor_name": "Dr. Sarah Johnson",
    "appointment_date": "2025-01-15",
    "appointment_time": "10:00",
    "hospital_name": "City General Hospital"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message_id": "email_20250108_120000_001",
  "status": "sent",
  "delivery_time": "2025-01-08T12:00:05Z"
}
```

### **POST /api/notifications/whatsapp**
Send WhatsApp message.

**Request Body:**
```json
{
  "to_phone": "+1234567890",
  "message_type": "text",
  "content": "Your appointment with Dr. Johnson is confirmed for Jan 15 at 10:00 AM",
  "template_name": "appointment_confirmation"
}
```

**Response:**
```json
{
  "success": true,
  "message_id": "whatsapp_20250108_120000_001",
  "status": "sent",
  "delivery_status": "delivered"
}
```

### **POST /api/notifications/voice**
Send voice message/call.

**Request Body:**
```json
{
  "to_phone": "+1234567890",
  "message": "This is a reminder for your appointment with Dr. Johnson tomorrow at 10 AM",
  "voice_type": "female",
  "language": "en-US"
}
```

**Response:**
```json
{
  "success": true,
  "call_id": "voice_20250108_120000_001",
  "status": "initiated",
  "estimated_duration": "30 seconds"
}
```

---

## 📊 **Dashboard APIs**

### **GET /api/dashboard/patient**
Get patient dashboard data.

**Query Parameters:**
- `patient_phone` (string): Patient phone number

**Response:**
```json
{
  "success": true,
  "patient_info": {
    "name": "John Doe",
    "phone": "+1234567890",
    "email": "john.doe@email.com"
  },
  "upcoming_appointments": [
    {
      "appointment_id": "APT_20250108_120000_001",
      "doctor_name": "Dr. Sarah Johnson",
      "department": "Cardiology",
      "date": "2025-01-15",
      "time": "10:00",
      "status": "scheduled"
    }
  ],
  "recent_alerts": [
    {
      "message": "Appointment confirmed",
      "timestamp": "2025-01-08T12:00:00Z",
      "type": "confirmation"
    }
  ]
}
```

### **GET /api/dashboard/doctor**
Get doctor dashboard data.

**Query Parameters:**
- `doctor_name` (string): Doctor name

**Response:**
```json
{
  "success": true,
  "doctor_info": {
    "name": "Dr. Sarah Johnson",
    "department": "Cardiology",
    "specialization": "Cardiology"
  },
  "today_schedule": [
    {
      "appointment_id": "APT_20250108_120000_001",
      "patient_name": "John Doe",
      "time": "10:00",
      "duration": 30,
      "status": "scheduled"
    }
  ],
  "statistics": {
    "total_appointments": 156,
    "today_appointments": 8,
    "week_appointments": 42,
    "recent_alerts": 3
  }
}
```

---

## 🤖 **MCP Agent Integration**

### **POST /api/mcp/tools/list**
Get list of available MCP tools.

**Response:**
```json
{
  "success": true,
  "tools": [
    {
      "name": "schedule_appointment",
      "description": "Schedule a new appointment",
      "parameters": {
        "patient_name": "string",
        "doctor_name": "string",
        "date": "string",
        "time": "string"
      }
    },
    {
      "name": "send_notification",
      "description": "Send notification to patient",
      "parameters": {
        "phone": "string",
        "message": "string",
        "channel": "string"
      }
    }
  ]
}
```

### **POST /api/mcp/tools/execute**
Execute an MCP tool.

**Request Body:**
```json
{
  "tool_name": "schedule_appointment",
  "parameters": {
    "patient_name": "John Doe",
    "doctor_name": "Dr. Sarah Johnson",
    "date": "2025-01-15",
    "time": "10:00"
  }
}
```

**Response:**
```json
{
  "success": true,
  "tool_result": {
    "appointment_id": "APT_20250108_120000_001",
    "status": "scheduled",
    "message": "Appointment scheduled successfully"
  }
}
```

---

## 📈 **Analytics & Reporting**

### **GET /api/analytics/appointments**
Get appointment analytics.

**Query Parameters:**
- `start_date` (string): Start date for analytics
- `end_date` (string): End date for analytics
- `department` (string): Filter by department

**Response:**
```json
{
  "success": true,
  "period": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
  },
  "metrics": {
    "total_appointments": 1250,
    "scheduled": 1100,
    "completed": 950,
    "cancelled": 150,
    "no_shows": 50
  },
  "trends": [
    {
      "date": "2025-01-01",
      "appointments": 42
    }
  ],
  "department_breakdown": {
    "Cardiology": 320,
    "Orthopedics": 280,
    "Pediatrics": 250
  }
}
```

### **GET /api/analytics/voice_usage**
Get voice interaction analytics.

**Response:**
```json
{
  "success": true,
  "voice_metrics": {
    "total_sessions": 450,
    "successful_appointments": 380,
    "average_session_duration": "00:04:32",
    "satisfaction_rating": 4.6,
    "language_breakdown": {
      "en-US": 320,
      "es-ES": 80,
      "fr-FR": 50
    }
  }
}
```

---

## ⚠️ **Error Handling**

### **Standard Error Response**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid appointment date format",
    "details": {
      "field": "appointment_date",
      "expected_format": "YYYY-MM-DD"
    }
  },
  "timestamp": "2025-01-08T12:00:00Z"
}
```

### **Common Error Codes**
- `VALIDATION_ERROR`: Invalid input data
- `NOT_FOUND`: Resource not found
- `CONFLICT`: Scheduling conflict
- `UNAUTHORIZED`: Authentication required
- `RATE_LIMITED`: Too many requests
- `INTERNAL_ERROR`: Server error
- `SERVICE_UNAVAILABLE`: External service unavailable

---

## 🔄 **WebSocket Events**

### **Connection**
```javascript
const socket = io('http://localhost:5000');

socket.on('connect', () => {
  console.log('Connected to hospital scheduler');
});
```

### **Real-time Events**

#### **appointment_update**
```json
{
  "event": "appointment_update",
  "data": {
    "appointment_id": "APT_20250108_120000_001",
    "status": "confirmed",
    "updated_at": "2025-01-08T12:00:00Z"
  }
}
```

#### **doctor_status_changed**
```json
{
  "event": "doctor_status_changed",
  "data": {
    "doctor": "Dr. Sarah Johnson",
    "status": "running_late",
    "estimated_delay": "30 minutes",
    "affected_appointments": ["APT_001", "APT_002"]
  }
}
```

#### **new_alert**
```json
{
  "event": "new_alert",
  "data": {
    "alert_id": "ALERT_20250108_120000_001",
    "type": "appointment_reminder",
    "priority": "medium",
    "message": "Appointment reminder: Tomorrow at 10:00 AM"
  }
}
```

---

## 📝 **Rate Limiting**

### **Default Limits**
- **General API**: 200 requests per day, 50 per hour
- **Voice API**: 100 requests per hour
- **Notification API**: 500 requests per day

### **Headers**
```
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1641648000
```

---

## 🧪 **Testing Examples**

### **cURL Examples**

#### **Schedule Appointment**
```bash
curl -X POST http://localhost:5000/api/appointments/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "patient_name": "John Doe",
    "patient_phone": "+1234567890",
    "department": "Cardiology",
    "appointment_date": "2025-01-15",
    "appointment_time": "10:00"
  }'
```

#### **Get Doctor Availability**
```bash
curl "http://localhost:5000/api/doctors/Dr.%20Sarah%20Johnson/availability?start_date=2025-01-15&end_date=2025-01-21"
```

#### **Create Alert**
```bash
curl -X POST http://localhost:5000/api/alerts/create \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "doctor_late",
    "appointment_id": "APT_20250108_120000_001",
    "message": "Doctor running 30 minutes late",
    "priority": "high"
  }'
```

### **JavaScript Examples**

#### **Voice Session**
```javascript
// Start voice session
const startVoiceSession = async () => {
  const response = await fetch('/api/voice/session/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      patient_phone: '+1234567890',
      language: 'en-US'
    })
  });
  
  const data = await response.json();
  return data.session_id;
};

// Process voice input
const processVoice = async (sessionId, audioData) => {
  const response = await fetch('/api/voice/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      audio_data: audioData,
      language: 'en-US'
    })
  });
  
  return await response.json();
};
```

#### **Real-time Updates**
```javascript
// Connect to WebSocket
const socket = io();

// Listen for appointment updates
socket.on('appointment_update', (data) => {
  console.log('Appointment updated:', data);
  updateAppointmentUI(data);
});

// Listen for doctor status changes
socket.on('doctor_status_changed', (data) => {
  console.log('Doctor status changed:', data);
  showDoctorAlert(data);
});
```

---

## 📚 **SDK Examples**

### **Python SDK**
```python
import requests

class HospitalSchedulerAPI:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def schedule_appointment(self, patient_data):
        response = requests.post(
            f"{self.base_url}/api/appointments/schedule",
            json=patient_data
        )
        return response.json()
    
    def get_doctor_availability(self, doctor_name, start_date, end_date):
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        response = requests.get(
            f"{self.base_url}/api/doctors/{doctor_name}/availability",
            params=params
        )
        return response.json()

# Usage
api = HospitalSchedulerAPI()
result = api.schedule_appointment({
    "patient_name": "John Doe",
    "patient_phone": "+1234567890",
    "department": "Cardiology",
    "appointment_date": "2025-01-15",
    "appointment_time": "10:00"
})
```

---

## 🔧 **Configuration**

### **Environment Variables**
```bash
# API Configuration
API_VERSION=v1
API_RATE_LIMIT=50
API_TIMEOUT=30

# Database Configuration
DATABASE_URL=sqlite:///hospital_scheduler.db
DATABASE_POOL_SIZE=10

# External Services
GOOGLE_API_KEY=your-google-api-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token

# Feature Flags
ENABLE_VOICE_FEATURES=true
ENABLE_MCP_AGENTS=true
ENABLE_REAL_TIME_ALERTS=true
```

---

**📞 For additional API support or custom integrations, please contact the development team.**

