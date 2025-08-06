"""
Appointment Management Agent with LangChain and Gemini Integration
"""
import os
import json
from datetime import datetime, date, time, timedelta
from typing import Dict, Any, Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from src.agents.mcp_protocol import MCPAgent, AgentType, MessageType, MCPMessage
from src.models.appointment import Appointment, Doctor, Patient, db

class AppointmentAgent(MCPAgent):
    """
    Core appointment management agent that handles scheduling, modification, and cancellation
    """
    
    def __init__(self):
        super().__init__("appointment_manager", AgentType.APPOINTMENT_MANAGER)
        
        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY", "your-api-key-here"),
            temperature=0.3
        )
        
        # Register message handlers
        self.register_handler("request_schedule_appointment", self.handle_schedule_appointment)
        self.register_handler("request_modify_appointment", self.handle_modify_appointment)
        self.register_handler("request_cancel_appointment", self.handle_cancel_appointment)
        self.register_handler("request_get_appointments", self.handle_get_appointments)
        self.register_handler("request_parse_natural_language", self.handle_parse_natural_language)
        
        # Appointment scheduling prompt template
        self.scheduling_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent appointment scheduling assistant for a hospital.
            Your task is to extract structured information from natural language requests.
            
            Extract the following information:
            - Patient name
            - Contact information (phone/email)
            - Preferred doctor or department
            - Preferred date and time
            - Reason for visit
            - Urgency level (routine, urgent, emergency)
            
            Return the information in JSON format with these exact keys:
            patient_name, patient_phone, patient_email, doctor_preference, department_preference, 
            preferred_date, preferred_time, reason, urgency_level
            
            If information is missing, set the value to null.
            For dates, use YYYY-MM-DD format. For times, use HH:MM format.
            """),
            ("human", "{user_input}")
        ])
    
    def handle_parse_natural_language(self, message: MCPMessage) -> MCPMessage:
        """Parse natural language appointment request using Gemini"""
        try:
            user_input = message.payload.get('user_input', '')
            
            # Use LangChain with Gemini to parse the request
            chain = self.scheduling_prompt | self.llm
            response = chain.invoke({"user_input": user_input})
            
            # Extract JSON from response
            parsed_data = self._extract_json_from_response(response.content)
            
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                payload={
                    'action': 'parse_complete',
                    'parsed_data': parsed_data,
                    'original_input': user_input
                },
                correlation_id=message.message_id
            )
            
        except Exception as e:
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.ERROR,
                payload={
                    'error': 'PARSING_ERROR',
                    'message': str(e)
                },
                correlation_id=message.message_id
            )
    
    def handle_schedule_appointment(self, message: MCPMessage) -> MCPMessage:
        """Handle appointment scheduling request"""
        try:
            appointment_data = message.payload.get('appointment_data', {})
            
            # Validate required fields
            required_fields = ['patient_name', 'patient_phone', 'doctor_name', 'department', 
                             'appointment_date', 'appointment_time']
            
            for field in required_fields:
                if not appointment_data.get(field):
                    return self.create_message(
                        context_id=message.context_id,
                        receiver_id=message.sender_id,
                        message_type=MessageType.ERROR,
                        payload={
                            'error': 'MISSING_REQUIRED_FIELD',
                            'message': f'Missing required field: {field}'
                        },
                        correlation_id=message.message_id
                    )
            
            # Check doctor availability
            availability_check = self._check_doctor_availability(
                appointment_data['doctor_name'],
                appointment_data['appointment_date'],
                appointment_data['appointment_time']
            )
            
            if not availability_check['available']:
                return self.create_message(
                    context_id=message.context_id,
                    receiver_id=message.sender_id,
                    message_type=MessageType.RESPONSE,
                    payload={
                        'action': 'scheduling_failed',
                        'reason': 'doctor_not_available',
                        'message': availability_check['message'],
                        'alternative_slots': availability_check.get('alternatives', [])
                    },
                    correlation_id=message.message_id
                )
            
            # Create appointment
            appointment = Appointment(
                patient_name=appointment_data['patient_name'],
                patient_phone=appointment_data['patient_phone'],
                patient_email=appointment_data.get('patient_email'),
                doctor_name=appointment_data['doctor_name'],
                department=appointment_data['department'],
                appointment_date=datetime.strptime(appointment_data['appointment_date'], '%Y-%m-%d').date(),
                appointment_time=datetime.strptime(appointment_data['appointment_time'], '%H:%M').time(),
                notes=appointment_data.get('notes', ''),
                status='scheduled'
            )
            
            db.session.add(appointment)
            db.session.commit()
            
            # Update context with appointment info
            self.context_manager.update_context(message.context_id, 'last_appointment', appointment.to_dict())
            
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                payload={
                    'action': 'appointment_scheduled',
                    'appointment': appointment.to_dict(),
                    'message': f'Appointment scheduled successfully for {appointment.patient_name} with Dr. {appointment.doctor_name}'
                },
                correlation_id=message.message_id
            )
            
        except Exception as e:
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.ERROR,
                payload={
                    'error': 'SCHEDULING_ERROR',
                    'message': str(e)
                },
                correlation_id=message.message_id
            )
    
    def handle_modify_appointment(self, message: MCPMessage) -> MCPMessage:
        """Handle appointment modification request"""
        try:
            appointment_id = message.payload.get('appointment_id')
            modifications = message.payload.get('modifications', {})
            
            appointment = Appointment.query.get(appointment_id)
            if not appointment:
                return self.create_message(
                    context_id=message.context_id,
                    receiver_id=message.sender_id,
                    message_type=MessageType.ERROR,
                    payload={
                        'error': 'APPOINTMENT_NOT_FOUND',
                        'message': f'Appointment with ID {appointment_id} not found'
                    },
                    correlation_id=message.message_id
                )
            
            # Apply modifications
            for key, value in modifications.items():
                if hasattr(appointment, key):
                    if key in ['appointment_date']:
                        setattr(appointment, key, datetime.strptime(value, '%Y-%m-%d').date())
                    elif key in ['appointment_time']:
                        setattr(appointment, key, datetime.strptime(value, '%H:%M').time())
                    else:
                        setattr(appointment, key, value)
            
            appointment.updated_at = datetime.utcnow()
            db.session.commit()
            
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                payload={
                    'action': 'appointment_modified',
                    'appointment': appointment.to_dict(),
                    'message': 'Appointment modified successfully'
                },
                correlation_id=message.message_id
            )
            
        except Exception as e:
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.ERROR,
                payload={
                    'error': 'MODIFICATION_ERROR',
                    'message': str(e)
                },
                correlation_id=message.message_id
            )
    
    def handle_cancel_appointment(self, message: MCPMessage) -> MCPMessage:
        """Handle appointment cancellation request"""
        try:
            appointment_id = message.payload.get('appointment_id')
            reason = message.payload.get('reason', 'No reason provided')
            
            appointment = Appointment.query.get(appointment_id)
            if not appointment:
                return self.create_message(
                    context_id=message.context_id,
                    receiver_id=message.sender_id,
                    message_type=MessageType.ERROR,
                    payload={
                        'error': 'APPOINTMENT_NOT_FOUND',
                        'message': f'Appointment with ID {appointment_id} not found'
                    },
                    correlation_id=message.message_id
                )
            
            appointment.status = 'cancelled'
            appointment.notes = f"{appointment.notes}\nCancellation reason: {reason}"
            appointment.updated_at = datetime.utcnow()
            db.session.commit()
            
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                payload={
                    'action': 'appointment_cancelled',
                    'appointment': appointment.to_dict(),
                    'message': 'Appointment cancelled successfully'
                },
                correlation_id=message.message_id
            )
            
        except Exception as e:
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.ERROR,
                payload={
                    'error': 'CANCELLATION_ERROR',
                    'message': str(e)
                },
                correlation_id=message.message_id
            )
    
    def handle_get_appointments(self, message: MCPMessage) -> MCPMessage:
        """Handle request to get appointments"""
        try:
            filters = message.payload.get('filters', {})
            
            query = Appointment.query
            
            # Apply filters
            if filters.get('patient_phone'):
                query = query.filter(Appointment.patient_phone == filters['patient_phone'])
            if filters.get('doctor_name'):
                query = query.filter(Appointment.doctor_name == filters['doctor_name'])
            if filters.get('date'):
                query = query.filter(Appointment.appointment_date == datetime.strptime(filters['date'], '%Y-%m-%d').date())
            if filters.get('status'):
                query = query.filter(Appointment.status == filters['status'])
            
            appointments = query.all()
            
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                payload={
                    'action': 'appointments_retrieved',
                    'appointments': [apt.to_dict() for apt in appointments],
                    'count': len(appointments)
                },
                correlation_id=message.message_id
            )
            
        except Exception as e:
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.ERROR,
                payload={
                    'error': 'RETRIEVAL_ERROR',
                    'message': str(e)
                },
                correlation_id=message.message_id
            )
    
    def _check_doctor_availability(self, doctor_name: str, appointment_date: str, appointment_time: str) -> Dict[str, Any]:
        """Check if doctor is available at the requested time"""
        try:
            # Convert strings to datetime objects
            apt_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            apt_time = datetime.strptime(appointment_time, '%H:%M').time()
            
            # Check if doctor exists and is active
            doctor = Doctor.query.filter_by(name=doctor_name, is_active=True).first()
            if not doctor:
                return {
                    'available': False,
                    'message': f'Doctor {doctor_name} not found or not active'
                }
            
            # Check if appointment is on a working day
            day_of_week = apt_date.strftime('%A').lower()
            available_days = json.loads(doctor.available_days)
            if day_of_week not in [day.lower() for day in available_days]:
                return {
                    'available': False,
                    'message': f'Doctor {doctor_name} is not available on {day_of_week.title()}'
                }
            
            # Check if appointment is within working hours
            if apt_time < doctor.start_time or apt_time >= doctor.end_time:
                return {
                    'available': False,
                    'message': f'Appointment time is outside working hours ({doctor.start_time} - {doctor.end_time})'
                }
            
            # Check for existing appointments at the same time
            existing_appointment = Appointment.query.filter_by(
                doctor_name=doctor_name,
                appointment_date=apt_date,
                appointment_time=apt_time,
                status='scheduled'
            ).first()
            
            if existing_appointment:
                return {
                    'available': False,
                    'message': 'Doctor already has an appointment at this time'
                }
            
            return {
                'available': True,
                'message': 'Doctor is available'
            }
            
        except Exception as e:
            return {
                'available': False,
                'message': f'Error checking availability: {str(e)}'
            }
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON data from LLM response"""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # If no JSON found, return empty dict
                return {}
                
        except json.JSONDecodeError:
            # If JSON parsing fails, return empty dict
            return {}
    
    def generate_smart_suggestions(self, user_input: str, context: Dict[str, Any]) -> List[str]:
        """Generate smart suggestions based on user input and context"""
        try:
            suggestion_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful assistant that provides smart suggestions for hospital appointments.
                Based on the user's input and context, provide 3-5 helpful suggestions.
                
                Suggestions can include:
                - Alternative appointment times
                - Relevant doctors or departments
                - Preparation instructions
                - Follow-up actions
                
                Return suggestions as a simple list, one per line.
                """),
                ("human", "User input: {user_input}\nContext: {context}")
            ])
            
            chain = suggestion_prompt | self.llm
            response = chain.invoke({
                "user_input": user_input,
                "context": json.dumps(context, default=str)
            })
            
            # Split response into individual suggestions
            suggestions = [s.strip() for s in response.content.split('\n') if s.strip()]
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            return [f"Error generating suggestions: {str(e)}"]

