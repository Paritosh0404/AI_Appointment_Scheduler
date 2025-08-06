# Hospital Appointment Scheduler - Enhanced with Make.ai and ElevenLabs

## Overview

This is an enhanced version of the Hospital Appointment Scheduler that has been upgraded to use **Make.ai** for workflow automation (replacing n8n) and **ElevenLabs** for advanced voice assistance capabilities.

## Key Enhancements

### 1. Make.ai Integration
- **Replaced n8n** with Make.ai for more robust workflow automation
- Enhanced notification system with better reliability
- Improved webhook handling and API integration
- Support for complex workflow scenarios

### 2. Enhanced ElevenLabs Voice Assistant
- **Advanced voice command processing** with intelligent response generation
- **Multi-scenario voice settings** (appointment confirmation, emergency alerts, friendly conversation)
- **Conversation history tracking** for better user experience
- **Smart voice notifications** for appointment events
- **Make.ai workflow triggers** from voice commands

## New Features

### Voice Assistant Capabilities
- **Appointment Scheduling**: "Schedule an appointment with Dr. Smith"
- **Appointment Cancellation**: "Cancel my appointment"
- **Appointment Rescheduling**: "Reschedule my appointment to next week"
- **Emergency Handling**: "This is an emergency, I need help"
- **Doctor Availability**: "When is Dr. Johnson available?"
- **General Inquiries**: Natural conversation support

### Make.ai Workflow Integration
- **Automated notifications** via SMS, email, and voice
- **Emergency alert workflows** with priority handling
- **Appointment reminder scheduling** with built-in delays
- **Multi-channel communication** support
- **Webhook-based triggers** for real-time processing

## API Endpoints

### Enhanced Voice Routes
- `POST /api/voice/process` - Process voice commands with Make.ai integration
- `POST /api/voice/tts` - Text-to-speech with scenario-based voice settings
- `POST /api/voice/notification` - Create voice notifications for appointments
- `GET /api/voice/conversation-history` - Get conversation history
- `POST /api/voice/smart-response` - Generate intelligent voice responses

### Make.ai Integration Routes
- All existing appointment routes now use Make.ai for notifications
- Enhanced error handling and workflow status tracking
- Support for complex notification scenarios

## Configuration

### Environment Variables
```bash
# ElevenLabs Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_preferred_voice_id

# Make.ai Configuration
MAKE_WEBHOOK_URL=https://hook.make.com/your-webhook-id
MAKE_API_KEY=your_make_api_key
MAKE_BASE_URL=https://api.make.com

# Application Configuration
APP_BASE_URL=http://localhost:5000
```

### Make.ai Webhook Setup
1. Create a new scenario in Make.ai
2. Add a webhook trigger module
3. Configure the webhook URL in your environment variables
4. Set up notification modules (SMS, Email, etc.)
5. Test the webhook integration

### ElevenLabs Setup
1. Sign up for ElevenLabs account
2. Get your API key from the dashboard
3. Choose your preferred voice ID
4. Configure the environment variables

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Run the Application**
   ```bash
   python src/main.py
   ```

## Usage Examples

### Voice Command Processing
```python
# Process voice command
response = requests.post('/api/voice/process', json={
    'text': 'Schedule an appointment with Dr. Smith for tomorrow at 2 PM',
    'conversation_id': 'user123'
})
```

### Create Voice Notification
```python
# Create voice notification for appointment
response = requests.post('/api/voice/notification', json={
    'notification_type': 'confirmation',
    'appointment_data': {
        'patient_name': 'John Doe',
        'doctor_name': 'Dr. Smith',
        'appointment_date': '2024-01-15',
        'appointment_time': '14:00'
    }
})
```

## Architecture Changes

### Before (n8n)
- n8n workflows for notifications
- Basic voice service
- Limited automation capabilities

### After (Make.ai + Enhanced ElevenLabs)
- Make.ai scenarios for complex workflows
- Intelligent voice assistant with context awareness
- Advanced notification system with multiple channels
- Conversation history and smart responses
- Emergency handling with priority workflows

## File Structure

```
src/
├── integrations/
│   ├── make_client.py          # Make.ai integration (NEW)
│   └── n8n_client.py           # Legacy n8n client (DEPRECATED)
├── voice/
│   ├── enhanced_elevenlabs_service.py  # Enhanced voice service (NEW)
│   └── elevenlabs_voice_service.py     # Basic voice service (LEGACY)
├── routes/
│   ├── voice.py                # Enhanced voice routes
│   └── appointment.py          # Updated with Make.ai integration
└── main.py                     # Updated with CORS support
```

## Testing

### Voice Assistant Testing
```bash
# Test voice processing
curl -X POST http://localhost:5000/api/voice/process \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, I need to schedule an appointment"}'
```

### Make.ai Webhook Testing
```bash
# Test notification workflow
curl -X POST http://localhost:5000/api/appointments/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "patient_info": {
      "name": "John Doe",
      "phone": "+1234567890",
      "email": "john@example.com"
    }
  }'
```

## Deployment

The application is ready for deployment with:
- CORS enabled for frontend integration
- Environment-based configuration
- Scalable Make.ai workflow integration
- Production-ready voice processing

## Support

For issues related to:
- **Make.ai Integration**: Check webhook configuration and API keys
- **ElevenLabs Voice**: Verify API key and voice ID settings
- **General Issues**: Check logs and environment configuration

## License

This project is licensed under the MIT License.

