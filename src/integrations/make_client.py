"""
Make.ai Integration Client for Hospital Appointment Scheduler
"""
import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime
import os

class MakeClient:
    """Client for integrating with Make.ai workflow automation"""
    
    def __init__(self, make_webhook_url: str = None):
        self.make_webhook_url = make_webhook_url or os.getenv('MAKE_WEBHOOK_URL', 'https://hook.make.com/your-webhook-id')
        self.api_key = os.getenv('MAKE_API_KEY')
        self.base_url = os.getenv('MAKE_BASE_URL', 'https://api.make.com')
        
    def trigger_notification_workflow(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger the appointment notification workflow via Make.ai webhook"""
        try:
            # Prepare notification payload for Make.ai
            payload = {
                'notification_type': notification_data.get('type', 'confirmation'),
                'patient_name': notification_data.get('patient_name'),
                'patient_phone': notification_data.get('patient_phone'),
                'patient_email': notification_data.get('patient_email'),
                'doctor_name': notification_data.get('doctor_name'),
                'appointment_date': notification_data.get('appointment_date'),
                'appointment_time': notification_data.get('appointment_time'),
                'hospital_name': notification_data.get('hospital_name', 'City General Hospital'),
                'callback_url': notification_data.get('callback_url'),
                'timestamp': datetime.now().isoformat(),
                'source': 'hospital_scheduler'
            }
            
            # Send webhook request to Make.ai
            response = requests.post(
                self.make_webhook_url,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'HospitalScheduler/1.0'
                },
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                return {
                    'success': True,
                    'message': 'Make.ai notification workflow triggered successfully',
                    'response': response.json() if response.content else {},
                    'execution_id': response.headers.get('X-Make-Execution-Id')
                }
            else:
                return {
                    'success': False,
                    'error': f'Make.ai webhook request failed with status {response.status_code}',
                    'response': response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def send_appointment_confirmation(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send appointment confirmation notification via Make.ai"""
        notification_data = {
            'type': 'confirmation',
            'patient_name': appointment_data.get('patient_name'),
            'patient_phone': appointment_data.get('patient_phone'),
            'patient_email': appointment_data.get('patient_email'),
            'doctor_name': appointment_data.get('doctor_name'),
            'appointment_date': appointment_data.get('appointment_date'),
            'appointment_time': appointment_data.get('appointment_time'),
            'callback_url': f"{os.getenv('APP_BASE_URL', 'http://localhost:5000')}/api/notifications/callback"
        }
        
        return self.trigger_notification_workflow(notification_data)
    
    def send_appointment_reminder(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send appointment reminder notification via Make.ai"""
        notification_data = {
            'type': 'reminder',
            'patient_name': appointment_data.get('patient_name'),
            'patient_phone': appointment_data.get('patient_phone'),
            'patient_email': appointment_data.get('patient_email'),
            'doctor_name': appointment_data.get('doctor_name'),
            'appointment_date': appointment_data.get('appointment_date'),
            'appointment_time': appointment_data.get('appointment_time'),
            'callback_url': f"{os.getenv('APP_BASE_URL', 'http://localhost:5000')}/api/notifications/callback"
        }
        
        return self.trigger_notification_workflow(notification_data)
    
    def send_appointment_cancellation(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send appointment cancellation notification via Make.ai"""
        notification_data = {
            'type': 'cancellation',
            'patient_name': appointment_data.get('patient_name'),
            'patient_phone': appointment_data.get('patient_phone'),
            'patient_email': appointment_data.get('patient_email'),
            'doctor_name': appointment_data.get('doctor_name'),
            'appointment_date': appointment_data.get('appointment_date'),
            'appointment_time': appointment_data.get('appointment_time'),
            'callback_url': f"{os.getenv('APP_BASE_URL', 'http://localhost:5000')}/api/notifications/callback"
        }
        
        return self.trigger_notification_workflow(notification_data)
    
    def get_scenario_status(self, scenario_id: str) -> Dict[str, Any]:
        """Get the status of a Make.ai scenario execution"""
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'Make.ai API key not configured'
                }
            
            headers = {
                'Authorization': f'Token {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/v2/scenarios/{scenario_id}/executions",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'scenario_status': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to get scenario status: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error getting scenario status: {str(e)}'
            }
    
    def list_active_scenarios(self) -> Dict[str, Any]:
        """List all active Make.ai scenarios"""
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'Make.ai API key not configured'
                }
            
            headers = {
                'Authorization': f'Token {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/v2/scenarios",
                headers=headers,
                params={'filter[active]': 'true'},
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'scenarios': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to list scenarios: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error listing scenarios: {str(e)}'
            }
    
    def send_sms_notification(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS notification via Make.ai SMS integration"""
        notification_data = {
            'type': 'sms',
            'phone_number': phone_number,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.trigger_notification_workflow(notification_data)
    
    def send_email_notification(self, email: str, subject: str, body: str) -> Dict[str, Any]:
        """Send email notification via Make.ai email integration"""
        notification_data = {
            'type': 'email',
            'email': email,
            'subject': subject,
            'body': body,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.trigger_notification_workflow(notification_data)

class NotificationAgent:
    """Agent for handling notifications through Make.ai workflows"""
    
    def __init__(self):
        self.make_client = MakeClient()
        self.notification_history = []
    
    def send_notification(self, notification_type: str, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification based on type using Make.ai"""
        try:
            if notification_type == 'confirmation':
                result = self.make_client.send_appointment_confirmation(appointment_data)
            elif notification_type == 'reminder':
                result = self.make_client.send_appointment_reminder(appointment_data)
            elif notification_type == 'cancellation':
                result = self.make_client.send_appointment_cancellation(appointment_data)
            else:
                return {
                    'success': False,
                    'error': f'Unknown notification type: {notification_type}'
                }
            
            # Log notification attempt
            self.notification_history.append({
                'type': notification_type,
                'appointment_data': appointment_data,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error sending notification: {str(e)}'
            }
    
    def get_notification_history(self, limit: int = 50) -> list:
        """Get recent notification history"""
        return self.notification_history[-limit:]
    
    def schedule_reminder(self, appointment_data: Dict[str, Any], reminder_time: datetime) -> Dict[str, Any]:
        """Schedule a reminder notification via Make.ai"""
        # Make.ai can handle scheduling through its built-in delay/schedule modules
        scheduled_data = {
            **appointment_data,
            'scheduled_time': reminder_time.isoformat(),
            'type': 'scheduled_reminder'
        }
        
        result = self.make_client.trigger_notification_workflow(scheduled_data)
        
        if result.get('success'):
            return {
                'success': True,
                'message': f'Reminder scheduled for {reminder_time.isoformat()} via Make.ai',
                'reminder_id': f"make_reminder_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'execution_id': result.get('execution_id')
            }
        else:
            return result

# Global notification agent instance
notification_agent = NotificationAgent()

