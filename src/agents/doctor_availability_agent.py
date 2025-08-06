"""
Doctor Availability Agent - Manages doctor schedules and availability
"""
import json
from datetime import datetime, date, time, timedelta
from typing import Dict, Any, Optional, List
from src.agents.mcp_protocol import MCPAgent, AgentType, MessageType, MCPMessage
from src.models.appointment import Doctor, Appointment, db

class DoctorAvailabilityAgent(MCPAgent):
    """
    Agent responsible for managing doctor schedules and checking availability
    """
    
    def __init__(self):
        super().__init__("doctor_availability", AgentType.DOCTOR_AVAILABILITY)
        
        # Register message handlers
        self.register_handler("request_check_availability", self.handle_check_availability)
        self.register_handler("request_get_available_slots", self.handle_get_available_slots)
        self.register_handler("request_get_doctors", self.handle_get_doctors)
        self.register_handler("request_add_doctor", self.handle_add_doctor)
        self.register_handler("request_update_doctor_schedule", self.handle_update_doctor_schedule)
        self.register_handler("request_get_doctor_by_department", self.handle_get_doctor_by_department)
    
    def handle_check_availability(self, message: MCPMessage) -> MCPMessage:
        """Check if a specific doctor is available at a given time"""
        try:
            doctor_name = message.payload.get('doctor_name')
            appointment_date = message.payload.get('appointment_date')
            appointment_time = message.payload.get('appointment_time')
            
            if not all([doctor_name, appointment_date, appointment_time]):
                return self.create_message(
                    context_id=message.context_id,
                    receiver_id=message.sender_id,
                    message_type=MessageType.ERROR,
                    payload={
                        'error': 'MISSING_PARAMETERS',
                        'message': 'Missing required parameters: doctor_name, appointment_date, appointment_time'
                    },
                    correlation_id=message.message_id
                )
            
            availability = self._check_doctor_availability(doctor_name, appointment_date, appointment_time)
            
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                payload={
                    'action': 'availability_checked',
                    'doctor_name': doctor_name,
                    'appointment_date': appointment_date,
                    'appointment_time': appointment_time,
                    'available': availability['available'],
                    'message': availability['message'],
                    'alternatives': availability.get('alternatives', [])
                },
                correlation_id=message.message_id
            )
            
        except Exception as e:
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.ERROR,
                payload={
                    'error': 'AVAILABILITY_CHECK_ERROR',
                    'message': str(e)
                },
                correlation_id=message.message_id
            )
    
    def handle_get_available_slots(self, message: MCPMessage) -> MCPMessage:
        """Get all available slots for a doctor on a specific date"""
        try:
            doctor_name = message.payload.get('doctor_name')
            appointment_date = message.payload.get('appointment_date')
            
            if not all([doctor_name, appointment_date]):
                return self.create_message(
                    context_id=message.context_id,
                    receiver_id=message.sender_id,
                    message_type=MessageType.ERROR,
                    payload={
                        'error': 'MISSING_PARAMETERS',
                        'message': 'Missing required parameters: doctor_name, appointment_date'
                    },
                    correlation_id=message.message_id
                )
            
            available_slots = self._get_available_slots(doctor_name, appointment_date)
            
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                payload={
                    'action': 'available_slots_retrieved',
                    'doctor_name': doctor_name,
                    'appointment_date': appointment_date,
                    'available_slots': available_slots,
                    'count': len(available_slots)
                },
                correlation_id=message.message_id
            )
            
        except Exception as e:
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.ERROR,
                payload={
                    'error': 'SLOTS_RETRIEVAL_ERROR',
                    'message': str(e)
                },
                correlation_id=message.message_id
            )
    
    def handle_get_doctors(self, message: MCPMessage) -> MCPMessage:
        """Get list of all active doctors"""
        try:
            filters = message.payload.get('filters', {})
            
            query = Doctor.query.filter_by(is_active=True)
            
            # Apply filters
            if filters.get('department'):
                query = query.filter(Doctor.department == filters['department'])
            if filters.get('specialization'):
                query = query.filter(Doctor.specialization == filters['specialization'])
            
            doctors = query.all()
            
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                payload={
                    'action': 'doctors_retrieved',
                    'doctors': [doctor.to_dict() for doctor in doctors],
                    'count': len(doctors)
                },
                correlation_id=message.message_id
            )
            
        except Exception as e:
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.ERROR,
                payload={
                    'error': 'DOCTORS_RETRIEVAL_ERROR',
                    'message': str(e)
                },
                correlation_id=message.message_id
            )
    
    def handle_add_doctor(self, message: MCPMessage) -> MCPMessage:
        """Add a new doctor to the system"""
        try:
            doctor_data = message.payload.get('doctor_data', {})
            
            required_fields = ['name', 'specialization', 'department', 'available_days', 
                             'start_time', 'end_time']
            
            for field in required_fields:
                if not doctor_data.get(field):
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
            
            # Create new doctor
            doctor = Doctor(
                name=doctor_data['name'],
                specialization=doctor_data['specialization'],
                department=doctor_data['department'],
                available_days=json.dumps(doctor_data['available_days']),
                start_time=datetime.strptime(doctor_data['start_time'], '%H:%M').time(),
                end_time=datetime.strptime(doctor_data['end_time'], '%H:%M').time(),
                consultation_duration=doctor_data.get('consultation_duration', 30),
                is_active=True
            )
            
            db.session.add(doctor)
            db.session.commit()
            
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                payload={
                    'action': 'doctor_added',
                    'doctor': doctor.to_dict(),
                    'message': f'Doctor {doctor.name} added successfully'
                },
                correlation_id=message.message_id
            )
            
        except Exception as e:
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.ERROR,
                payload={
                    'error': 'DOCTOR_ADDITION_ERROR',
                    'message': str(e)
                },
                correlation_id=message.message_id
            )
    
    def handle_update_doctor_schedule(self, message: MCPMessage) -> MCPMessage:
        """Update doctor's schedule"""
        try:
            doctor_id = message.payload.get('doctor_id')
            schedule_updates = message.payload.get('schedule_updates', {})
            
            doctor = Doctor.query.get(doctor_id)
            if not doctor:
                return self.create_message(
                    context_id=message.context_id,
                    receiver_id=message.sender_id,
                    message_type=MessageType.ERROR,
                    payload={
                        'error': 'DOCTOR_NOT_FOUND',
                        'message': f'Doctor with ID {doctor_id} not found'
                    },
                    correlation_id=message.message_id
                )
            
            # Apply schedule updates
            for key, value in schedule_updates.items():
                if hasattr(doctor, key):
                    if key == 'available_days':
                        setattr(doctor, key, json.dumps(value))
                    elif key in ['start_time', 'end_time']:
                        setattr(doctor, key, datetime.strptime(value, '%H:%M').time())
                    else:
                        setattr(doctor, key, value)
            
            db.session.commit()
            
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                payload={
                    'action': 'doctor_schedule_updated',
                    'doctor': doctor.to_dict(),
                    'message': f'Schedule updated for Dr. {doctor.name}'
                },
                correlation_id=message.message_id
            )
            
        except Exception as e:
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.ERROR,
                payload={
                    'error': 'SCHEDULE_UPDATE_ERROR',
                    'message': str(e)
                },
                correlation_id=message.message_id
            )
    
    def handle_get_doctor_by_department(self, message: MCPMessage) -> MCPMessage:
        """Get doctors by department"""
        try:
            department = message.payload.get('department')
            
            if not department:
                return self.create_message(
                    context_id=message.context_id,
                    receiver_id=message.sender_id,
                    message_type=MessageType.ERROR,
                    payload={
                        'error': 'MISSING_PARAMETER',
                        'message': 'Missing required parameter: department'
                    },
                    correlation_id=message.message_id
                )
            
            doctors = Doctor.query.filter_by(department=department, is_active=True).all()
            
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                payload={
                    'action': 'doctors_by_department_retrieved',
                    'department': department,
                    'doctors': [doctor.to_dict() for doctor in doctors],
                    'count': len(doctors)
                },
                correlation_id=message.message_id
            )
            
        except Exception as e:
            return self.create_message(
                context_id=message.context_id,
                receiver_id=message.sender_id,
                message_type=MessageType.ERROR,
                payload={
                    'error': 'DEPARTMENT_DOCTORS_ERROR',
                    'message': str(e)
                },
                correlation_id=message.message_id
            )
    
    def _check_doctor_availability(self, doctor_name: str, appointment_date: str, appointment_time: str) -> Dict[str, Any]:
        """Internal method to check doctor availability"""
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
                    'message': f'Doctor {doctor_name} is not available on {day_of_week.title()}',
                    'alternatives': self._get_alternative_days(doctor, apt_date)
                }
            
            # Check if appointment is within working hours
            if apt_time < doctor.start_time or apt_time >= doctor.end_time:
                return {
                    'available': False,
                    'message': f'Appointment time is outside working hours ({doctor.start_time} - {doctor.end_time})',
                    'alternatives': self._get_alternative_times(doctor, apt_date)
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
                    'message': 'Doctor already has an appointment at this time',
                    'alternatives': self._get_alternative_times(doctor, apt_date)
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
    
    def _get_available_slots(self, doctor_name: str, appointment_date: str) -> List[str]:
        """Get all available time slots for a doctor on a specific date"""
        try:
            apt_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            
            doctor = Doctor.query.filter_by(name=doctor_name, is_active=True).first()
            if not doctor:
                return []
            
            # Check if date is a working day
            day_of_week = apt_date.strftime('%A').lower()
            available_days = json.loads(doctor.available_days)
            if day_of_week not in [day.lower() for day in available_days]:
                return []
            
            # Generate all possible time slots
            current_time = datetime.combine(apt_date, doctor.start_time)
            end_time = datetime.combine(apt_date, doctor.end_time)
            duration = timedelta(minutes=doctor.consultation_duration)
            
            available_slots = []
            
            while current_time + duration <= end_time:
                slot_time = current_time.time()
                
                # Check if this slot is already booked
                existing_appointment = Appointment.query.filter_by(
                    doctor_name=doctor_name,
                    appointment_date=apt_date,
                    appointment_time=slot_time,
                    status='scheduled'
                ).first()
                
                if not existing_appointment:
                    available_slots.append(slot_time.strftime('%H:%M'))
                
                current_time += duration
            
            return available_slots
            
        except Exception as e:
            return []
    
    def _get_alternative_days(self, doctor: Doctor, requested_date: date) -> List[str]:
        """Get alternative available days for the doctor"""
        try:
            available_days = json.loads(doctor.available_days)
            alternatives = []
            
            # Check next 7 days
            for i in range(1, 8):
                check_date = requested_date + timedelta(days=i)
                day_of_week = check_date.strftime('%A').lower()
                
                if day_of_week in [day.lower() for day in available_days]:
                    alternatives.append(check_date.strftime('%Y-%m-%d'))
                
                if len(alternatives) >= 3:  # Limit to 3 alternatives
                    break
            
            return alternatives
            
        except Exception:
            return []
    
    def _get_alternative_times(self, doctor: Doctor, appointment_date: date) -> List[str]:
        """Get alternative available times for the doctor on the same date"""
        try:
            available_slots = self._get_available_slots(doctor.name, appointment_date.strftime('%Y-%m-%d'))
            return available_slots[:5]  # Return first 5 available slots
            
        except Exception:
            return []

