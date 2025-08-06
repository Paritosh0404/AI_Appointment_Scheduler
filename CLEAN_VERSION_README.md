# Hospital Appointment Scheduler - Clean Version

## Overview

This is the **clean version** of the Hospital Appointment Scheduler with **n8n and Twilio completely removed** and replaced with **Make.ai and ElevenLabs** integrations.

## What's Changed

### ✅ Removed Components
- **n8n workflow automation** - Completely removed
- **Twilio SMS/WhatsApp integration** - Completely removed
- **All related configuration files and dependencies**

### ✅ Added Components
- **Make.ai workflow automation** - Complete replacement for n8n
- **Enhanced ElevenLabs voice assistance** - Advanced voice features
- **Streamlined notification system** - Using Make.ai webhooks

## Key Features

### 🎤 Enhanced Voice Assistant (ElevenLabs)
- **Natural language processing** for appointment requests
- **Multi-scenario voice settings** (professional, urgent, casual)
- **Conversation history tracking**
- **Emergency situation handling**
- **Direct Make.ai workflow triggers** from voice commands

### 🔄 Make.ai Workflow Automation
- **Reliable webhook-based notifications**
- **Multi-channel communication** (Email, SMS via Make.ai integrations)
- **Workflow status tracking**
- **Emergency priority routing**
- **Automated appointment confirmations and reminders**

### 🏥 Core Hospital Features
- **Appointment scheduling and management**
- **Doctor availability checking**
- **Patient dashboard**
- **Doctor dashboard**
- **Smart appointment recommendations**
- **Dynamic alerts and notifications**

## Quick Start

### 1. Environment Setup

Copy the `.env.example` file to `.env` and configure:

```bash
cp .env.example .env
```

### 2. Required API Keys

Update your `.env` file with:

```ini
# ElevenLabs Voice Service
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

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

## API Endpoints

### Voice Assistant
- `POST /api/voice/process` - Process voice commands
- `POST /api/voice/notification` - Create voice notifications
- `GET /api/voice/conversation-history` - Get conversation history

### Appointments
- `POST /api/appointments/schedule` - Schedule new appointment
- `POST /api/appointments/process-request` - Natural language appointment requests
- `GET /api/appointments/doctors` - Get available doctors
- `POST /api/appointments/doctor-availability` - Check doctor availability

### Notifications (Make.ai)
- `POST /api/appointments/notifications/email` - Send email notifications
- `POST /api/appointments/notifications/voice` - Send voice notifications

## Make.ai Setup

### 1. Create Scenario
1. Log into your Make.ai account
2. Create a new scenario
3. Add a **Webhook** trigger module
4. Configure notification modules (Email, SMS, etc.)

### 2. Configure Webhook
1. Copy the webhook URL from Make.ai
2. Add it to your `.env` file as `MAKE_WEBHOOK_URL`
3. Test the webhook with sample data

### 3. Scenario Structure
```
Webhook Trigger → Router → [Email Module, SMS Module, Voice Module]
```

## ElevenLabs Setup

### 1. Get API Key
1. Sign up at [ElevenLabs](https://elevenlabs.io)
2. Get your API key from the dashboard
3. Add it to your `.env` file

### 2. Choose Voice
1. Browse available voices in ElevenLabs
2. Copy the voice ID you prefer
3. Update `ELEVENLABS_VOICE_ID` in your `.env` file

## Voice Commands Examples

- **"Schedule an appointment with Dr. Smith"**
- **"Cancel my appointment for tomorrow"**
- **"When is Dr. Johnson available?"**
- **"I need urgent medical help"** (triggers emergency workflow)
- **"Reschedule my appointment to next week"**

## Project Structure

```
hospital_scheduler/
├── src/
│   ├── main.py                          # Flask application entry point
│   ├── routes/
│   │   ├── appointment.py               # Appointment management routes
│   │   ├── voice.py                     # Voice assistant routes
│   │   └── user.py                      # User management routes
│   ├── integrations/
│   │   └── make_client.py               # Make.ai integration client
│   ├── voice/
│   │   ├── enhanced_elevenlabs_service.py # Enhanced voice service
│   │   └── elevenlabs_voice_service.py    # Basic voice service
│   ├── agents/
│   │   └── langchain_mcp_agent.py       # LangChain MCP agent
│   └── models/
│       ├── appointment.py               # Appointment data models
│       └── user.py                      # User data models
├── make_workflows/
│   └── appointment_notification_scenario.json # Make.ai scenario template
├── requirements.txt                     # Python dependencies
├── .env.example                         # Environment configuration template
└── README.md                           # This file
```

## Dependencies

### Core Dependencies
- **Flask** - Web framework
- **ElevenLabs** - Voice synthesis and processing
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
3. Configure your Make.ai webhooks for production URLs
4. Ensure ElevenLabs API limits are appropriate for your usage

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **Make.ai Webhook Not Working**
   - Check webhook URL configuration
   - Verify API key permissions
   - Test webhook manually in Make.ai dashboard

3. **ElevenLabs Voice Not Working**
   - Verify API key is valid
   - Check voice ID exists
   - Ensure sufficient API credits

4. **LangChain Agent Errors**
   - Verify Google API key is set
   - Check MCP server configuration
   - Ensure all langchain dependencies are installed

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify environment configuration
3. Test individual components separately
4. Consult the API documentation for Make.ai and ElevenLabs

## License

This project is part of the AI Agents Hackathon submission.

