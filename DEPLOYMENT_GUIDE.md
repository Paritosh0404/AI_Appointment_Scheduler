# 🚀 Hospital Appointment Scheduler - Deployment Guide

## 📋 **Prerequisites**

### **System Requirements**
- **Python 3.11+** (recommended)
- **Node.js 18+** (for n8n workflows)
- **SQLite** (included with Python)
- **Git** for version control

### **API Keys & Services** (Optional for Demo)
- **Google API Key** for Gemini LLM (for full AI features)
- **Twilio Account** for WhatsApp integration
- **Gmail API Credentials** for email notifications
- **n8n Instance** for workflow automation

---

## 🛠️ **Installation Steps**

### **1. Clone the Repository**
```bash
git clone <repository-url>
cd hospital_scheduler
```

### **2. Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Set Environment Variables**
Create a `.env` file in the root directory:
```bash
# Core Configuration
SECRET_KEY=your-secret-key-here
DATABASE_PATH=hospital_scheduler.db
HOSPITAL_NAME="City General Hospital"

# AI/LLM Configuration (Optional for demo)
GOOGLE_API_KEY=your-google-api-key
OPENAI_API_KEY=your-openai-key  # Alternative LLM

# Communication APIs (Optional for demo)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890

# Gmail Integration (Optional)
GMAIL_CLIENT_ID=your-gmail-client-id
GMAIL_CLIENT_SECRET=your-gmail-secret

# n8n Integration (Optional)
N8N_WEBHOOK_URL=http://localhost:5678/webhook/hospital
```

### **5. Initialize Database**
```bash
python -c "from src.main_enhanced import init_database; init_database()"
```

### **6. Run the Application**
```bash
# For development
python src/main_enhanced.py

# For production (with gunicorn)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 src.main_enhanced:app
```

---

## 🌐 **Access Points**

### **Main Application**
- **URL**: `http://localhost:5000`
- **Description**: Main landing page with voice interaction

### **Patient Dashboard**
- **URL**: `http://localhost:5000/dashboard`
- **Description**: Real-time patient appointment management

### **Doctor Dashboard**
- **URL**: `http://localhost:5000/doctor/dashboard`
- **Description**: Professional schedule and patient management

### **API Endpoints**
- **Health Check**: `http://localhost:5000/health`
- **System Status**: `http://localhost:5000/api/system/status`
- **Features List**: `http://localhost:5000/api/features`

---

## 🔧 **Configuration Options**

### **Basic Demo Mode**
For a quick demo without external APIs:
```bash
export GOOGLE_API_KEY="demo-key"
python src/main_enhanced.py
```
- All features work in simulation mode
- Sample data is automatically loaded
- Voice features use browser APIs

### **Full Production Mode**
With all integrations enabled:
```bash
# Set all environment variables
export GOOGLE_API_KEY="your-real-key"
export TWILIO_ACCOUNT_SID="your-sid"
# ... other variables

python src/main_enhanced.py
```

### **Docker Deployment**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "src/main_enhanced.py"]
```

```bash
# Build and run
docker build -t hospital-scheduler .
docker run -p 5000:5000 -e GOOGLE_API_KEY="your-key" hospital-scheduler
```

---

## 🧪 **Testing the Application**

### **1. Health Check**
```bash
curl http://localhost:5000/health
```
Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-XX...",
  "service": "Hospital Appointment Scheduler",
  "features": [...]
}
```

### **2. Demo Appointment Scheduling**
```bash
curl -X POST http://localhost:5000/api/demo/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "patient_name": "John Doe",
    "patient_phone": "+1234567890",
    "department": "Cardiology",
    "notes": "Regular checkup"
  }'
```

### **3. Voice Interaction Test**
1. Open browser to `http://localhost:5000`
2. Click "Start Voice Session"
3. Say: "I need to schedule an appointment"
4. Follow the conversation flow

### **4. Dashboard Testing**
1. **Patient Dashboard**: Navigate to `/dashboard`
2. **Doctor Dashboard**: Navigate to `/doctor/dashboard`
3. Test real-time updates by opening both in different tabs

---

## 🔐 **Security Configuration**

### **Production Security**
```python
# In production, set these environment variables:
SECRET_KEY=<strong-random-key>
FLASK_ENV=production
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

### **Database Security**
```bash
# Set proper file permissions
chmod 600 hospital_scheduler.db
chown www-data:www-data hospital_scheduler.db
```

### **API Rate Limiting**
```python
# Add to main_enhanced.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

---

## 📊 **Monitoring & Logging**

### **Application Logs**
```python
# Configure logging in main_enhanced.py
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hospital_scheduler.log'),
        logging.StreamHandler()
    ]
)
```

### **Health Monitoring**
```bash
# Simple health check script
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
if [ $response -eq 200 ]; then
    echo "Application is healthy"
else
    echo "Application is down - HTTP $response"
fi
```

### **Database Monitoring**
```python
# Add to system status endpoint
def get_db_stats():
    conn = sqlite3.connect('hospital_scheduler.db')
    cursor = conn.cursor()
    
    stats = {}
    stats['total_appointments'] = cursor.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    stats['active_alerts'] = cursor.execute("SELECT COUNT(*) FROM alerts WHERE status='pending'").fetchone()[0]
    stats['total_doctors'] = cursor.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
    
    conn.close()
    return stats
```

---

## 🚀 **Production Deployment**

### **Using Gunicorn + Nginx**

#### **1. Install Gunicorn**
```bash
pip install gunicorn
```

#### **2. Create Gunicorn Configuration**
```python
# gunicorn.conf.py
bind = "127.0.0.1:5000"
workers = 4
worker_class = "eventlet"  # For SocketIO support
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
```

#### **3. Nginx Configuration**
```nginx
# /etc/nginx/sites-available/hospital-scheduler
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support for real-time features
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### **4. Start Services**
```bash
# Start Gunicorn
gunicorn -c gunicorn.conf.py src.main_enhanced:app

# Enable and start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### **Using Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'

services:
  hospital-scheduler:
    build: .
    ports:
      - "5000:5000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - hospital-scheduler
    restart: unless-stopped
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. MCP Agent Initialization Fails**
```bash
# Check if Google API key is set
echo $GOOGLE_API_KEY

# Run in demo mode
export GOOGLE_API_KEY="demo-key"
python src/main_enhanced.py
```

#### **2. Voice Features Not Working**
- Ensure browser has microphone permissions
- Check if running on HTTPS (required for some browsers)
- Verify audio device availability

#### **3. Database Connection Issues**
```bash
# Check database file permissions
ls -la hospital_scheduler.db

# Recreate database
rm hospital_scheduler.db
python -c "from src.main_enhanced import init_database; init_database()"
```

#### **4. SocketIO Connection Problems**
- Check firewall settings for port 5000
- Verify WebSocket support in proxy configuration
- Test with different browsers

### **Debug Mode**
```bash
# Run with debug logging
export FLASK_DEBUG=1
export PYTHONPATH=/path/to/hospital_scheduler
python src/main_enhanced.py
```

### **Performance Optimization**
```python
# Add to main_enhanced.py for production
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Enable gzip compression
from flask_compress import Compress
Compress(app)
```

---

## 📈 **Scaling Considerations**

### **Database Scaling**
- **SQLite**: Good for up to 100,000 appointments
- **PostgreSQL**: Recommended for production with >1M records
- **Redis**: Add for session storage and caching

### **Application Scaling**
- **Load Balancer**: Nginx or HAProxy for multiple instances
- **Container Orchestration**: Kubernetes for enterprise deployment
- **CDN**: CloudFlare or AWS CloudFront for static assets

### **Monitoring & Analytics**
- **Application Performance**: New Relic, DataDog
- **Error Tracking**: Sentry, Rollbar
- **Usage Analytics**: Custom dashboard with appointment metrics

---

## 🎯 **Next Steps**

### **Immediate Enhancements**
1. **SSL/TLS Configuration** for production security
2. **Database Migration** to PostgreSQL for scalability
3. **API Rate Limiting** for abuse prevention
4. **Comprehensive Testing** suite with pytest

### **Advanced Features**
1. **Multi-tenant Support** for multiple hospitals
2. **Advanced Analytics** dashboard for administrators
3. **Mobile App** with React Native
4. **Integration APIs** for existing hospital systems

### **Enterprise Features**
1. **HIPAA Compliance** audit and certification
2. **Single Sign-On** integration
3. **Advanced Reporting** and business intelligence
4. **Disaster Recovery** and backup systems

---

## 📞 **Support**

### **Documentation**
- **API Documentation**: Available at `/api/docs` (when enabled)
- **User Guides**: In the `/docs` directory
- **Video Tutorials**: Available upon request

### **Community**
- **GitHub Issues**: For bug reports and feature requests
- **Discussion Forum**: For community support
- **Professional Support**: Available for enterprise deployments

---

**🎉 Your Hospital Appointment Scheduler is now ready for deployment!**

*For additional support or custom deployment assistance, please contact the development team.*

