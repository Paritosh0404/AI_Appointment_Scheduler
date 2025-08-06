# 🚀 Deployment Guide - Smart Hospital Appointment Scheduler

## Quick Deployment Options

### Option 1: Local Development Setup

1. **Clone and Setup**
```bash
git clone <repository-url>
cd hospital_scheduler
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Install System Dependencies**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y espeak espeak-data portaudio19-dev python3-dev

# macOS
brew install espeak portaudio

# Windows
# Download and install espeak from http://espeak.sourceforge.net/download.html
```

3. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Initialize Database**
```bash
python -c "from src.main import app; from src.models.appointment import db; app.app_context().push(); db.create_all()"
```

5. **Start Application**
```bash
python src/main.py
```

### Option 2: Docker Deployment

1. **Build Docker Image**
```bash
docker build -t hospital-scheduler .
```

2. **Run Container**
```bash
docker run -p 5000:5000 \
  -e GOOGLE_API_KEY=your_api_key \
  -e N8N_WEBHOOK_URL=your_webhook_url \
  hospital-scheduler
```

### Option 3: Cloud Deployment

#### Heroku Deployment
```bash
# Install Heroku CLI
heroku create hospital-scheduler-app
heroku config:set GOOGLE_API_KEY=your_api_key
heroku config:set N8N_WEBHOOK_URL=your_webhook_url
git push heroku main
```

#### AWS ECS Deployment
```bash
# Build and push to ECR
aws ecr create-repository --repository-name hospital-scheduler
docker tag hospital-scheduler:latest <account-id>.dkr.ecr.<region>.amazonaws.com/hospital-scheduler:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/hospital-scheduler:latest

# Deploy using ECS task definition
aws ecs create-service --cluster default --service-name hospital-scheduler --task-definition hospital-scheduler:1
```

## n8n Workflow Setup

### 1. Install n8n
```bash
npm install -g n8n
```

### 2. Start n8n
```bash
n8n start
```

### 3. Import Workflow
1. Open n8n at `http://localhost:5678`
2. Go to Workflows → Import
3. Upload `n8n_workflows/appointment_notification.json`
4. Configure your notification channels

### 4. Configure Webhooks
1. Set webhook URL in your `.env` file
2. Test webhook connectivity
3. Configure notification channels (SMS, Email, Voice)

## Production Configuration

### Environment Variables
```bash
# Production settings
FLASK_ENV=production
FLASK_DEBUG=False

# Database (use PostgreSQL for production)
DATABASE_URL=postgresql://user:password@localhost/hospital_scheduler

# Security
SECRET_KEY=your_secure_secret_key

# Voice Service (use cloud providers for production)
VOICE_PROVIDER=google
GOOGLE_CLOUD_TTS_API_KEY=your_google_cloud_api_key

# Monitoring
LOG_LEVEL=WARNING
SENTRY_DSN=your_sentry_dsn
```

### Database Migration (PostgreSQL)
```bash
# Install PostgreSQL adapter
pip install psycopg2-binary

# Update database URL in .env
DATABASE_URL=postgresql://user:password@localhost/hospital_scheduler

# Run migrations
python -c "from src.main import app; from src.models.appointment import db; app.app_context().push(); db.create_all()"
```

### SSL/HTTPS Setup
```bash
# Using Let's Encrypt with nginx
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com

# Update nginx configuration
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Scaling and Performance

### Load Balancing
```bash
# Using nginx for load balancing
upstream hospital_scheduler {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

server {
    location / {
        proxy_pass http://hospital_scheduler;
    }
}
```

### Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_doctor ON appointments(doctor_name);
CREATE INDEX idx_appointments_patient ON appointments(patient_phone);
CREATE INDEX idx_doctors_department ON doctors(department);
```

### Caching Setup
```python
# Redis caching for better performance
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379'
})
```

## Monitoring and Logging

### Application Monitoring
```python
# Sentry for error tracking
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your_sentry_dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

### Health Check Endpoint
```python
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }
```

### Log Configuration
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/hospital_scheduler.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
```

## Security Considerations

### API Security
```python
# Rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# CORS configuration
from flask_cors import CORS
CORS(app, origins=['https://yourdomain.com'])
```

### Data Encryption
```python
# Encrypt sensitive data
from cryptography.fernet import Fernet

def encrypt_data(data):
    key = os.environ.get('ENCRYPTION_KEY')
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()
```

### HIPAA Compliance
- Enable audit logging for all patient data access
- Implement role-based access control
- Encrypt all data in transit and at rest
- Regular security audits and penetration testing

## Backup and Recovery

### Database Backup
```bash
# PostgreSQL backup
pg_dump hospital_scheduler > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump hospital_scheduler > $BACKUP_DIR/backup_$DATE.sql
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
```

### Application Backup
```bash
# Backup application files
tar -czf hospital_scheduler_backup_$(date +%Y%m%d).tar.gz \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  hospital_scheduler/
```

## Testing in Production

### Smoke Tests
```bash
# Test basic functionality
curl -f http://localhost:5000/health || exit 1
curl -f http://localhost:5000/api/appointments/doctors || exit 1
```

### Load Testing
```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:5000/api/appointments/doctors

# Using wrk
wrk -t12 -c400 -d30s http://localhost:5000/api/appointments/doctors
```

## Troubleshooting

### Common Issues

1. **Voice Service Not Working**
```bash
# Check espeak installation
espeak "test"

# Check audio system
aplay /usr/share/sounds/alsa/Front_Left.wav
```

2. **Database Connection Issues**
```bash
# Check database connectivity
python -c "from src.models.appointment import db; print('Database connected')"
```

3. **n8n Webhook Issues**
```bash
# Test webhook connectivity
curl -X POST http://localhost:5678/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### Log Analysis
```bash
# Monitor application logs
tail -f logs/hospital_scheduler.log

# Check for errors
grep ERROR logs/hospital_scheduler.log

# Monitor system resources
htop
iostat -x 1
```

## Performance Optimization

### Database Optimization
- Use connection pooling
- Implement query optimization
- Regular database maintenance
- Monitor slow queries

### Application Optimization
- Enable gzip compression
- Use CDN for static assets
- Implement caching strategies
- Optimize AI model calls

### Infrastructure Optimization
- Use load balancers
- Implement auto-scaling
- Monitor resource usage
- Regular performance testing

---

## Support and Maintenance

### Regular Maintenance Tasks
- Database backups (daily)
- Log rotation (weekly)
- Security updates (monthly)
- Performance monitoring (continuous)

### Monitoring Checklist
- [ ] Application health checks
- [ ] Database performance
- [ ] Voice service availability
- [ ] n8n workflow status
- [ ] API response times
- [ ] Error rates
- [ ] Resource utilization

### Emergency Procedures
1. **Service Outage**
   - Check application logs
   - Verify database connectivity
   - Restart services if needed
   - Notify stakeholders

2. **Data Issues**
   - Stop write operations
   - Assess data integrity
   - Restore from backup if needed
   - Validate data consistency

3. **Security Incident**
   - Isolate affected systems
   - Assess breach scope
   - Implement containment
   - Notify relevant authorities

---

For additional support, please refer to the main README.md or contact the development team.

