# Hospital Appointment Scheduler - Retell AI Version

## Overview

This is the **Retell AI version** of the Hospital Appointment Scheduler with **ElevenLabs completely removed** and replaced with **Retell AI voice assistance** and **Make.ai workflow automation**.

## What's Changed

### ✅ Removed Components
- **ElevenLabs voice synthesis** - Completely removed
- **All ElevenLabs dependencies** - Cleaned from requirements.txt
- **Local audio processing** - Replaced with cloud-based Retell AI

### ✅ Added Components
- **Retell AI voice agents** - Professional phone call automation
- **Advanced call handling** - Outbound calls, webhooks, call analytics
- **Make.ai integration** - Seamless workflow automation
- **Cloud-based voice processing** - No local audio dependencies

## Key Features

### 📞 Retell AI Voice Agents
- **Outbound phone calls** for appointment confirmations and reminders
- **Professional voice agents** with natural conversation capabilities
- **Real-time call handling** with webhook integration
- **Call analytics and monitoring** for quality assurance
- **Emergency alert calls** with priority routing

### 🔄 Make.ai Workflow Integration
- **Automated call triggers** from appointment events
- **Multi-channel notifications** (Voice + Email + SMS)
- **Workflow status tracking** and execution monitoring
- **Emergency escalation** with priority handling

### 🏥 Enhanced Hospital Features
- **Voice-first appointment system** with professional phone interactions
- **Automated reminder calls** 24 hours before appointments
- **Emergency alert system** with immediate voice notifications
- **Call history and analytics** for operational insights
- **Webhook-based real-time updates**

## Quick Start

### 1. Environment Setup

Copy the `.env.example` file to `.env` and configure:

```bash
cp .env.example .env
```

### 2. Required API Keys and Configuration

Update your `.env` file with:

```ini
# Retell AI Configuration
RETELL_API_KEY=your_retell_api_key_here
RETELL_AGENT_ID=your_retell_agent_id_here
RETELL_FROM_NUMBER=+1234567890

# Make.ai Workflow Automation
MAKE_WEBHOOK_URL=https://hook.make.com/your-webhook-id-here
MAKE_API_KEY=your_make_api_key_here
MAKE_BASE_URL=https://api.make.com

# Google Gemini AI (for LangChain agent)
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Application Settings
SECRET_KEY=your-secret-key-here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python src/main.py
```

The application will start on `http://localhost:5000`

## Retell AI Setup

### 1. Create Retell AI Account
1. Sign up at [Retell AI](https://www.retellai.com)
2. Get your API key from the dashboard
3. Create a voice agent for hospital appointments

### 2. Configure Voice Agent
1. In Retell AI dashboard, create a new agent
2. Configure the agent for appointment-related conversations
3. Set up response templates for:
   - Appointment confirmations
   - Appointment reminders
   - Emergency alerts
4. Copy the Agent ID to your `.env` file

### 3. Set Up Phone Number
1. Purchase or configure a phone number in Retell AI
2. Add the number to your `.env` file as `RETELL_FROM_NUMBER`

### 4. Configure Webhooks
1. Set up webhook endpoints in Retell AI dashboard
2. Point to your application's webhook URL: `https://your-domain.com/api/voice/webhook`
3. Enable events: call_started, call_ended, call_analyzed

## API Endpoints

### Voice Calls (Retell AI)
- `POST /api/voice/create-call` - Create outbound voice call
- `GET /api/voice/call-details/<call_id>` - Get call details
- `GET /api/voice/calls` - List recent calls
- `POST /api/voice/webhook` - Handle Retell AI webhooks

### Appointment Voice Notifications
- `POST /api/voice/appointment-confirmation` - Send confirmation call
- `POST /api/voice/appointment-reminder` - Send reminder call
- `POST /api/voice/emergency-alert` - Send emergency alert call

### Service Management
- `GET /api/voice/health` - Health check for Retell AI service
- `GET /api/voice/agent-details` - Get agent configuration
- `GET /api/voice/conversation-history` - Get call history

### Appointments (with Voice Integration)
- `POST /api/appointments/schedule` - Schedule appointment (triggers voice confirmation)
- `POST /api/appointments/process-request` - Natural language appointment requests
- `GET /api/appointments/doctors` - Get available doctors
- `POST /api/appointments/doctor-availability` - Check doctor availability

## Voice Call Examples

### Appointment Confirmation Call
```bash
curl -X POST http://localhost:5000/api/voice/appointment-confirmation \
  -H "Content-Type: application/json" \
  -d '{
    "appointment_data": {
      "patient_name": "John Doe",
      "patient_phone": "+1234567890",
      "doctor_name": "Dr. Smith",
      "appointment_date": "2024-01-15",
      "appointment_time": "10:00 AM",
      "hospital_name": "City General Hospital"
    }
  }'
```

### Emergency Alert Call
```bash
curl -X POST http://localhost:5000/api/voice/emergency-alert \
  -H "Content-Type: application/json" \
  -d '{
    "alert_data": {
      "contact_phone": "+1234567890",
      "patient_name": "Jane Doe",
      "emergency_type": "cardiac",
      "message": "Emergency situation requires immediate attention"
    }
  }'
```

## Make.ai Integration

### 1. Create Make.ai Scenario
1. Log into your Make.ai account
2. Create a new scenario with webhook trigger
3. Add modules for:
   - Email notifications
   - SMS notifications (via Twilio/other providers)
   - Database logging
   - CRM integration

### 2. Configure Webhook
1. Copy the webhook URL from Make.ai
2. Add it to your `.env` file as `MAKE_WEBHOOK_URL`
3. Test the webhook with sample data

### 3. Workflow Structure
```
Webhook Trigger → Router → [Email Module, SMS Module, Database Module, CRM Module]
```

## Project Structure

```
hospital_scheduler/
├── src/
│   ├── main.py                          # Flask application entry point
│   ├── routes/
│   │   ├── appointment.py               # Appointment management routes
│   │   ├── voice.py                     # Retell AI voice routes
│   │   └── user.py                      # User management routes
│   ├── integrations/
│   │   └── make_client.py               # Make.ai integration client
│   ├── voice/
│   │   ├── retell_voice_service.py      # Retell AI voice service
│   │   └── voice_service.py             # Basic voice service (fallback)
│   ├── agents/
│   │   └── langchain_mcp_agent.py       # LangChain MCP agent
│   └── models/
│       ├── appointment.py               # Appointment data models
│       └── user.py                      # User data models
├── make_workflows/
│   └── appointment_notification_scenario.json # Make.ai scenario template
├── requirements.txt                     # Python dependencies
├── .env.example                         # Environment configuration template
└── RETELL_AI_README.md                 # This file
```

## Dependencies

### Core Dependencies
- **Flask** - Web framework
- **retell-sdk** - Retell AI Python SDK
- **LangChain** - AI agent framework
- **Requests** - HTTP client for Make.ai integration

### AI/ML Dependencies
- **langchain-google-genai** - Google Gemini integration
- **langchain-community** - LangChain community tools
- **langchain-mcp-adapters** - MCP protocol adapters

## Deployment

### Local Development
```bash
python src/main.py
```

### Production Deployment
1. Set `FLASK_ENV=production` in your `.env`
2. Use a production WSGI server like Gunicorn
3. Configure your Retell AI webhooks for production URLs
4. Set up Make.ai workflows for production environment
5. Ensure phone number is properly configured for outbound calls

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **Retell AI API Errors**
   - Verify API key is valid and has proper permissions
   - Check agent ID exists and is active
   - Ensure phone number is in E.164 format (+1234567890)
   - Verify webhook URLs are accessible from internet

3. **Make.ai Webhook Not Working**
   - Check webhook URL configuration
   - Verify API key permissions
   - Test webhook manually in Make.ai dashboard

4. **Call Creation Failures**
   - Verify phone number format (E.164: +1234567890)
   - Check Retell AI account balance and limits
   - Ensure agent is properly configured and active

5. **LangChain Agent Errors**
   - Verify Google API key is set
   - Check MCP server configuration
   - Ensure all langchain dependencies are installed

## Voice Agent Configuration

### Recommended Agent Settings
- **Response Engine**: Use OpenAI GPT-4 for natural conversations
- **Voice**: Choose professional, clear voice for medical context
- **Language**: Configure for your target language/region
- **Interruption Handling**: Enable for natural conversation flow
- **Call Recording**: Enable for quality assurance and compliance

### Conversation Templates
The agent should be configured with templates for:
- Appointment confirmation scripts
- Reminder call scripts
- Emergency alert protocols
- Rescheduling assistance
- General hospital information

## Compliance and Security

### HIPAA Considerations
- Ensure Retell AI configuration meets HIPAA requirements
- Configure call recording and data retention policies
- Implement proper access controls for call data
- Review Retell AI's BAA (Business Associate Agreement)

### Data Protection
- All call data is processed through Retell AI's secure infrastructure
- Webhook data should be transmitted over HTTPS only
- Implement proper authentication for webhook endpoints
- Regular security audits of API keys and access permissions

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify environment configuration
3. Test individual components separately
4. Consult Retell AI documentation: https://docs.retellai.com
5. Check Make.ai documentation for workflow issues

## License

This project is part of the AI Agents Hackathon submission.

## Changelog

### v2.0.0 - Retell AI Integration
- **BREAKING**: Removed ElevenLabs integration
- **NEW**: Added Retell AI voice agents
- **NEW**: Professional outbound call capabilities
- **NEW**: Advanced webhook handling
- **NEW**: Call analytics and monitoring
- **IMPROVED**: Better error handling and logging
- **IMPROVED**: Streamlined configuration

