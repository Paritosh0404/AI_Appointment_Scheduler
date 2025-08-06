"""
Enhanced Hospital Appointment Scheduler
Main Flask application with MCP integration, dashboards, and multi-agent architecture
"""
import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import json
from datetime import datetime
import sqlite3
import asyncio
import logging

# Import routes
from src.routes.appointment import appointment_bp
from src.routes.voice import voice_bp

# Import dashboards
from src.dashboard.user_dashboard import user_dashboard, init_socketio_events
from src.dashboard.doctor_dashboard import doctor_dashboard, init_doctor_socketio_events

# Import agents
try:
    from src.agents.langchain_mcp_agent import get_hospital_agent
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MCP agent not available: {e}")
    MCP_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
CORS(app, origins="*")

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hospital-scheduler-secret-key-2025')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'hospital_scheduler.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Register blueprints
app.register_blueprint(appointment_bp, url_prefix='/api/appointments')
app.register_blueprint(voice_bp, url_prefix='/api/voice')
app.register_blueprint(user_dashboard, url_prefix='/')
app.register_blueprint(doctor_dashboard, url_prefix='/')

# Initialize SocketIO events
init_socketio_events(socketio)
init_doctor_socketio_events(socketio)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve static files and main application"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Hospital Appointment Scheduler",
        "version": "2.0.0",
        "features": [
            "Voice Interaction",
            "Smart Scheduling",
            "Dynamic Alerts",
            "Email & WhatsApp Integration",
            "User & Doctor Dashboards",
            "MCP Multi-Agent Architecture" if MCP_AVAILABLE else "Basic Architecture"
        ]
    })

@app.route('/api/system/status')
def system_status():
    """System status endpoint"""
    try:
        # Check database connection
        db_path = os.path.join(os.path.dirname(__file__), 'database', 'hospital_scheduler.db')
        
        if not os.path.exists(db_path):
            # Initialize database if it doesn't exist
            init_database()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM doctors")
            doctor_count = cursor.fetchone()[0]
        except:
            doctor_count = 0
            
        try:
            cursor.execute("SELECT COUNT(*) FROM appointments")
            appointment_count = cursor.fetchone()[0]
        except:
            appointment_count = 0
            
        conn.close()
        
        return jsonify({
            "status": "operational",
            "database": "connected",
            "doctors": doctor_count,
            "appointments": appointment_count,
            "mcp_server": "running" if MCP_AVAILABLE else "not_available",
            "agents": {
                "appointment_agent": "active" if MCP_AVAILABLE else "basic",
                "voice_agent": "active",
                "gmail_agent": "active" if MCP_AVAILABLE else "simulated",
                "whatsapp_agent": "active" if MCP_AVAILABLE else "simulated",
                "alerts_agent": "active"
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"System status error: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/features')
def get_features():
    """Get list of available features"""
    return jsonify({
        "features": {
            "voice_interaction": {
                "name": "Voice Interaction",
                "description": "Natural language voice commands for appointment scheduling",
                "status": "active",
                "endpoint": "/api/voice/process"
            },
            "smart_scheduling": {
                "name": "Smart Scheduling",
                "description": "AI-powered appointment recommendations and conflict resolution",
                "status": "active" if MCP_AVAILABLE else "basic",
                "endpoint": "/api/appointments/smart_recommendations"
            },
            "dynamic_alerts": {
                "name": "Dynamic Alerts",
                "description": "Real-time notifications for appointment changes",
                "status": "active",
                "endpoint": "/api/alerts"
            },
            "multi_channel_communication": {
                "name": "Multi-Channel Communication",
                "description": "Email, WhatsApp, and voice notifications",
                "status": "active" if MCP_AVAILABLE else "simulated",
                "endpoints": ["/api/notifications/email", "/api/notifications/whatsapp"]
            },
            "user_dashboard": {
                "name": "Patient Dashboard",
                "description": "Real-time dashboard for patients to manage appointments",
                "status": "active",
                "endpoint": "/dashboard"
            },
            "doctor_dashboard": {
                "name": "Doctor Dashboard",
                "description": "Professional dashboard for doctors to manage schedules",
                "status": "active",
                "endpoint": "/doctor/dashboard"
            },
            "mcp_integration": {
                "name": "MCP Multi-Agent Architecture",
                "description": "Model Context Protocol for seamless agent communication",
                "status": "active" if MCP_AVAILABLE else "not_available"
            }
        }
    })

@app.route('/api/demo/schedule', methods=['POST'])
def demo_schedule():
    """Demo endpoint for quick appointment scheduling"""
    try:
        data = request.get_json()
        
        # Basic validation
        required_fields = ['patient_name', 'patient_phone', 'department']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Generate appointment ID
        appointment_id = f"DEMO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Simulate appointment creation
        appointment_data = {
            "appointment_id": appointment_id,
            "patient_name": data['patient_name'],
            "patient_phone": data['patient_phone'],
            "patient_email": data.get('patient_email', ''),
            "doctor_name": data.get('doctor_name', 'Dr. Demo'),
            "department": data['department'],
            "appointment_date": data.get('appointment_date', datetime.now().strftime('%Y-%m-%d')),
            "appointment_time": data.get('appointment_time', '10:00'),
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }
        
        # Store in database if available
        try:
            db_path = os.path.join(os.path.dirname(__file__), 'database', 'hospital_scheduler.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO appointments 
                (appointment_id, patient_name, patient_phone, patient_email, 
                 doctor_name, department, appointment_date, appointment_time, 
                 notes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                appointment_data['appointment_id'],
                appointment_data['patient_name'],
                appointment_data['patient_phone'],
                appointment_data['patient_email'],
                appointment_data['doctor_name'],
                appointment_data['department'],
                appointment_data['appointment_date'],
                appointment_data['appointment_time'],
                data.get('notes', ''),
                appointment_data['status'],
                appointment_data['created_at']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.warning(f"Could not store in database: {str(e)}")
        
        return jsonify({
            "success": True,
            "appointment": appointment_data,
            "message": "Demo appointment scheduled successfully!"
        })
        
    except Exception as e:
        logger.error(f"Demo schedule error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Initialize database and sample data
def init_database():
    """Initialize database with sample data"""
    try:
        # Ensure database directory exists
        db_dir = os.path.join(os.path.dirname(__file__), 'database')
        os.makedirs(db_dir, exist_ok=True)
        
        db_path = os.path.join(db_dir, 'hospital_scheduler.db')
        conn = sqlite3.connect(db_path)
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
        
        # Check if sample data exists
        cursor.execute("SELECT COUNT(*) FROM doctors")
        if cursor.fetchone()[0] == 0:
            # Insert sample doctors
            sample_doctors = [
                ("Dr. Sarah Johnson", "Cardiology", "Cardiology", '["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]', "09:00:00", "17:00:00", 30),
                ("Dr. Michael Chen", "Orthopedics", "Orthopedics", '["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]', "08:00:00", "16:00:00", 45),
                ("Dr. Emily Rodriguez", "Pediatrics", "Pediatrics", '["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]', "09:00:00", "17:00:00", 20),
                ("Dr. David Wilson", "Neurology", "Neurology", '["Monday", "Tuesday", "Wednesday", "Thursday"]', "10:00:00", "18:00:00", 60),
                ("Dr. Lisa Thompson", "Dermatology", "Dermatology", '["Tuesday", "Wednesday", "Thursday", "Friday"]', "09:00:00", "16:00:00", 30),
                ("Dr. James Anderson", "Internal Medicine", "Internal Medicine", '["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]', "08:00:00", "17:00:00", 30),
                ("Dr. Maria Garcia", "Gynecology", "Gynecology", '["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]', "09:00:00", "17:00:00", 30),
                ("Dr. Robert Kim", "Psychiatry", "Psychiatry", '["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]', "10:00:00", "18:00:00", 50)
            ]
            
            cursor.executemany("""
                INSERT INTO doctors (name, specialization, department, available_days, start_time, end_time, consultation_duration)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, sample_doctors)
            
            logger.info("Sample doctors inserted into database")
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")

# SocketIO events for real-time features
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("Client connected to SocketIO")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected from SocketIO")

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Initialize MCP agent (async) if available
    if MCP_AVAILABLE:
        async def init_agent():
            try:
                agent = await get_hospital_agent()
                logger.info("Hospital Scheduler Agent initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize MCP agent: {str(e)}")
        
        # Run agent initialization in background
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(init_agent())
            loop.close()
        except Exception as e:
            logger.warning(f"Agent initialization failed: {str(e)}")
    
    # Print startup information
    print("\n" + "="*60)
    print("🏥 HOSPITAL APPOINTMENT SCHEDULER")
    print("="*60)
    print("🤖 Multi-Agent Architecture:", "MCP Enabled" if MCP_AVAILABLE else "Basic Mode")
    print("🎤 Voice Interaction: Enabled")
    print("📱 Real-time Dashboards: Active")
    print("📧 Communication: Email & WhatsApp Integration")
    print("🚨 Dynamic Alerts: Real-time Notifications")
    print("🌐 Server: http://0.0.0.0:5000")
    print("📊 User Dashboard: http://0.0.0.0:5000/dashboard")
    print("👨‍⚕️ Doctor Dashboard: http://0.0.0.0:5000/doctor/dashboard")
    print("🔍 Health Check: http://0.0.0.0:5000/health")
    print("="*60)
    print("Ready for AI Agents Hackathon! 🚀")
    print("="*60 + "\n")
    
    # Run the app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)

