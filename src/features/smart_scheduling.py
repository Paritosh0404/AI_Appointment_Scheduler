"""
Smart Scheduling Features for Hospital Appointment Scheduler
Innovative features to enhance the appointment scheduling experience
"""
import json
from datetime import datetime, date, time, timedelta
from typing import Dict, Any, Optional, List, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from src.models.appointment import Appointment, Doctor, Patient, db
import os

class SmartSchedulingEngine:
    """Advanced scheduling engine with AI-powered features"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY", "your-api-key-here"),
            temperature=0.3
        )
        
        # Prompt for intelligent scheduling suggestions
        self.scheduling_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent hospital scheduling assistant. 
            Based on the patient's request, medical history, and current availability, 
            provide smart scheduling recommendations.
            
            Consider:
            - Urgency of the medical condition
            - Doctor specialization match
            - Patient preferences
            - Optimal appointment timing
            - Follow-up requirements
            
            Return recommendations in JSON format with:
            - recommended_doctor: best doctor match
            - recommended_time: optimal time slot
            - urgency_level: low/medium/high
            - reasoning: explanation for the recommendation
            - alternative_options: list of alternatives
            """),
            ("human", """
            Patient Request: {patient_request}
            Available Doctors: {available_doctors}
            Available Slots: {available_slots}
            Patient History: {patient_history}
            """)
        ])
    
    def get_smart_recommendations(self, patient_request: str, patient_phone: str = None) -> Dict[str, Any]:
        """Get AI-powered scheduling recommendations"""
        try:
            # Get available doctors and slots
            available_doctors = self._get_available_doctors()
            available_slots = self._get_available_slots_summary()
            
            # Get patient history if phone provided
            patient_history = {}
            if patient_phone:
                patient_history = self._get_patient_history(patient_phone)
            
            # Generate recommendations using AI
            chain = self.scheduling_prompt | self.llm
            response = chain.invoke({
                "patient_request": patient_request,
                "available_doctors": json.dumps(available_doctors, default=str),
                "available_slots": json.dumps(available_slots, default=str),
                "patient_history": json.dumps(patient_history, default=str)
            })
            
            # Parse AI response
            recommendations = self._parse_ai_response(response.content)
            
            # Enhance with additional smart features
            recommendations['smart_features'] = self._add_smart_features(patient_request, recommendations)
            
            return {
                'success': True,
                'recommendations': recommendations,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def predict_optimal_time(self, doctor_name: str, patient_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Predict optimal appointment times based on various factors"""
        try:
            doctor = Doctor.query.filter_by(name=doctor_name, is_active=True).first()
            if not doctor:
                return []
            
            # Get next 14 days of availability
            optimal_slots = []
            start_date = datetime.now().date() + timedelta(days=1)
            
            for i in range(14):
                check_date = start_date + timedelta(days=i)
                day_slots = self._get_available_slots_for_date(doctor_name, check_date.strftime('%Y-%m-%d'))
                
                for slot_time in day_slots:
                    score = self._calculate_time_score(check_date, slot_time, patient_preferences)
                    optimal_slots.append({
                        'date': check_date.strftime('%Y-%m-%d'),
                        'time': slot_time,
                        'score': score,
                        'day_of_week': check_date.strftime('%A'),
                        'reasons': self._get_score_reasons(check_date, slot_time, score)
                    })
            
            # Sort by score and return top recommendations
            optimal_slots.sort(key=lambda x: x['score'], reverse=True)
            return optimal_slots[:10]
            
        except Exception as e:
            return []
    
    def intelligent_rescheduling(self, appointment_id: int, reason: str) -> Dict[str, Any]:
        """Intelligently reschedule appointments with minimal disruption"""
        try:
            appointment = Appointment.query.get(appointment_id)
            if not appointment:
                return {'success': False, 'error': 'Appointment not found'}
            
            # Analyze rescheduling reason
            urgency = self._analyze_rescheduling_urgency(reason)
            
            # Find alternative slots
            alternatives = self.predict_optimal_time(
                appointment.doctor_name,
                {'urgency': urgency, 'original_date': appointment.appointment_date}
            )
            
            # Check for cascade effects
            cascade_analysis = self._analyze_cascade_effects(appointment)
            
            return {
                'success': True,
                'original_appointment': appointment.to_dict(),
                'alternatives': alternatives,
                'urgency': urgency,
                'cascade_analysis': cascade_analysis,
                'recommendations': self._generate_rescheduling_recommendations(alternatives, urgency)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def conflict_resolution(self, conflicting_appointments: List[int]) -> Dict[str, Any]:
        """Resolve scheduling conflicts intelligently"""
        try:
            appointments = [Appointment.query.get(apt_id) for apt_id in conflicting_appointments]
            appointments = [apt for apt in appointments if apt]
            
            if len(appointments) < 2:
                return {'success': False, 'error': 'Need at least 2 appointments for conflict resolution'}
            
            # Analyze priority of each appointment
            priorities = []
            for apt in appointments:
                priority_score = self._calculate_appointment_priority(apt)
                priorities.append({
                    'appointment': apt.to_dict(),
                    'priority_score': priority_score,
                    'priority_factors': self._get_priority_factors(apt)
                })
            
            # Sort by priority
            priorities.sort(key=lambda x: x['priority_score'], reverse=True)
            
            # Generate resolution strategy
            resolution_strategy = self._generate_conflict_resolution_strategy(priorities)
            
            return {
                'success': True,
                'conflict_analysis': priorities,
                'resolution_strategy': resolution_strategy,
                'recommended_actions': self._get_conflict_resolution_actions(priorities)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def predictive_scheduling(self, patient_phone: str) -> Dict[str, Any]:
        """Predict future scheduling needs based on patient history"""
        try:
            patient_history = self._get_patient_history(patient_phone)
            
            if not patient_history.get('appointments'):
                return {
                    'success': False,
                    'message': 'Insufficient history for predictions'
                }
            
            # Analyze patterns
            patterns = self._analyze_appointment_patterns(patient_history['appointments'])
            
            # Predict next appointment needs
            predictions = self._predict_future_appointments(patterns, patient_history)
            
            # Generate proactive recommendations
            proactive_recommendations = self._generate_proactive_recommendations(predictions)
            
            return {
                'success': True,
                'patterns': patterns,
                'predictions': predictions,
                'proactive_recommendations': proactive_recommendations,
                'confidence_score': self._calculate_prediction_confidence(patterns)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_available_doctors(self) -> List[Dict[str, Any]]:
        """Get list of available doctors with their specializations"""
        doctors = Doctor.query.filter_by(is_active=True).all()
        return [doctor.to_dict() for doctor in doctors]
    
    def _get_available_slots_summary(self) -> Dict[str, Any]:
        """Get summary of available slots for next 7 days"""
        summary = {}
        start_date = datetime.now().date() + timedelta(days=1)
        
        for i in range(7):
            check_date = start_date + timedelta(days=i)
            date_str = check_date.strftime('%Y-%m-%d')
            summary[date_str] = {}
            
            doctors = Doctor.query.filter_by(is_active=True).all()
            for doctor in doctors:
                slots = self._get_available_slots_for_date(doctor.name, date_str)
                summary[date_str][doctor.name] = len(slots)
        
        return summary
    
    def _get_available_slots_for_date(self, doctor_name: str, date_str: str) -> List[str]:
        """Get available slots for a specific doctor and date"""
        try:
            apt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
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
            
        except Exception:
            return []
    
    def _get_patient_history(self, patient_phone: str) -> Dict[str, Any]:
        """Get patient's appointment history"""
        try:
            patient = Patient.query.filter_by(phone=patient_phone).first()
            appointments = Appointment.query.filter_by(patient_phone=patient_phone).all()
            
            return {
                'patient': patient.to_dict() if patient else None,
                'appointments': [apt.to_dict() for apt in appointments],
                'total_appointments': len(appointments),
                'last_appointment': appointments[-1].to_dict() if appointments else None
            }
            
        except Exception:
            return {}
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response and extract recommendations"""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback to basic parsing
                return {
                    'recommended_doctor': 'General Practitioner',
                    'recommended_time': 'Next available',
                    'urgency_level': 'medium',
                    'reasoning': 'Standard recommendation',
                    'alternative_options': []
                }
                
        except json.JSONDecodeError:
            return {
                'recommended_doctor': 'General Practitioner',
                'recommended_time': 'Next available',
                'urgency_level': 'medium',
                'reasoning': 'Standard recommendation',
                'alternative_options': []
            }
    
    def _add_smart_features(self, patient_request: str, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Add additional smart features to recommendations"""
        return {
            'wait_time_prediction': self._predict_wait_time(recommendations.get('recommended_doctor')),
            'preparation_instructions': self._get_preparation_instructions(patient_request),
            'follow_up_suggestions': self._suggest_follow_ups(patient_request),
            'health_tips': self._get_relevant_health_tips(patient_request)
        }
    
    def _calculate_time_score(self, date: date, time_str: str, preferences: Dict[str, Any]) -> float:
        """Calculate a score for how optimal a time slot is"""
        score = 50.0  # Base score
        
        # Day of week preferences
        day_of_week = date.weekday()  # 0 = Monday, 6 = Sunday
        if day_of_week < 5:  # Weekday
            score += 10
        
        # Time of day preferences
        hour = int(time_str.split(':')[0])
        if 9 <= hour <= 11:  # Morning preferred
            score += 15
        elif 14 <= hour <= 16:  # Afternoon
            score += 10
        
        # Urgency factor
        urgency = preferences.get('urgency', 'medium')
        if urgency == 'high':
            # Prefer earlier dates
            days_from_now = (date - datetime.now().date()).days
            score += max(0, 20 - days_from_now)
        
        # Avoid Mondays and Fridays if possible (typically busier)
        if day_of_week in [0, 4]:
            score -= 5
        
        return score
    
    def _get_score_reasons(self, date: date, time_str: str, score: float) -> List[str]:
        """Get reasons for the time slot score"""
        reasons = []
        
        if score >= 70:
            reasons.append("Optimal time slot")
        elif score >= 60:
            reasons.append("Good time slot")
        else:
            reasons.append("Available time slot")
        
        day_of_week = date.weekday()
        if day_of_week < 5:
            reasons.append("Weekday appointment")
        else:
            reasons.append("Weekend appointment")
        
        hour = int(time_str.split(':')[0])
        if 9 <= hour <= 11:
            reasons.append("Morning slot - typically less crowded")
        elif 14 <= hour <= 16:
            reasons.append("Afternoon slot - good availability")
        
        return reasons
    
    def _analyze_rescheduling_urgency(self, reason: str) -> str:
        """Analyze the urgency of rescheduling based on reason"""
        reason_lower = reason.lower()
        
        if any(word in reason_lower for word in ['emergency', 'urgent', 'pain', 'severe']):
            return 'high'
        elif any(word in reason_lower for word in ['conflict', 'work', 'travel']):
            return 'medium'
        else:
            return 'low'
    
    def _analyze_cascade_effects(self, appointment: Appointment) -> Dict[str, Any]:
        """Analyze potential cascade effects of rescheduling"""
        # Check if other appointments might be affected
        same_day_appointments = Appointment.query.filter_by(
            doctor_name=appointment.doctor_name,
            appointment_date=appointment.appointment_date,
            status='scheduled'
        ).filter(Appointment.id != appointment.id).all()
        
        return {
            'affected_appointments': len(same_day_appointments),
            'doctor_utilization_impact': self._calculate_utilization_impact(appointment),
            'patient_impact_score': self._calculate_patient_impact(appointment)
        }
    
    def _generate_rescheduling_recommendations(self, alternatives: List[Dict[str, Any]], urgency: str) -> List[str]:
        """Generate recommendations for rescheduling"""
        recommendations = []
        
        if urgency == 'high':
            recommendations.append("Consider the earliest available slot")
            recommendations.append("Contact patient immediately to confirm new time")
        elif urgency == 'medium':
            recommendations.append("Offer top 3 alternative times")
            recommendations.append("Allow patient to choose preferred option")
        else:
            recommendations.append("Provide flexible rescheduling options")
            recommendations.append("Consider patient's original preferences")
        
        if alternatives:
            best_alternative = alternatives[0]
            recommendations.append(f"Recommended: {best_alternative['date']} at {best_alternative['time']}")
        
        return recommendations
    
    def _calculate_appointment_priority(self, appointment: Appointment) -> float:
        """Calculate priority score for an appointment"""
        score = 50.0  # Base score
        
        # Check urgency based on notes
        if appointment.notes:
            notes_lower = appointment.notes.lower()
            if any(word in notes_lower for word in ['urgent', 'emergency', 'pain']):
                score += 30
            elif any(word in notes_lower for word in ['follow-up', 'routine']):
                score += 10
        
        # Consider appointment age (how long ago it was scheduled)
        days_scheduled = (datetime.now() - appointment.created_at).days
        if days_scheduled > 7:
            score += 10  # Older appointments get slight priority
        
        # Consider department
        if appointment.department.lower() in ['emergency', 'cardiology', 'oncology']:
            score += 20
        
        return score
    
    def _get_priority_factors(self, appointment: Appointment) -> List[str]:
        """Get factors that influence appointment priority"""
        factors = []
        
        if appointment.notes:
            notes_lower = appointment.notes.lower()
            if any(word in notes_lower for word in ['urgent', 'emergency']):
                factors.append("Urgent medical condition")
            if any(word in notes_lower for word in ['follow-up']):
                factors.append("Follow-up appointment")
        
        if appointment.department.lower() in ['emergency', 'cardiology', 'oncology']:
            factors.append("Critical care department")
        
        days_scheduled = (datetime.now() - appointment.created_at).days
        if days_scheduled > 7:
            factors.append("Long-standing appointment")
        
        return factors
    
    def _generate_conflict_resolution_strategy(self, priorities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate strategy for resolving conflicts"""
        highest_priority = priorities[0]
        others = priorities[1:]
        
        strategy = {
            'keep_appointment': highest_priority['appointment']['id'],
            'reschedule_appointments': [apt['appointment']['id'] for apt in others],
            'reasoning': f"Keeping highest priority appointment (score: {highest_priority['priority_score']})",
            'alternative_actions': []
        }
        
        # Add alternative actions
        if len(others) == 1:
            strategy['alternative_actions'].append("Offer premium time slot to rescheduled patient")
        else:
            strategy['alternative_actions'].append("Batch reschedule multiple appointments")
        
        return strategy
    
    def _get_conflict_resolution_actions(self, priorities: List[Dict[str, Any]]) -> List[str]:
        """Get recommended actions for conflict resolution"""
        actions = []
        
        highest_priority = priorities[0]
        actions.append(f"Confirm appointment #{highest_priority['appointment']['id']} (highest priority)")
        
        for priority in priorities[1:]:
            apt_id = priority['appointment']['id']
            actions.append(f"Reschedule appointment #{apt_id} with apology and premium alternative")
        
        actions.append("Send proactive notifications to all affected patients")
        actions.append("Document conflict resolution for future reference")
        
        return actions
    
    def _analyze_appointment_patterns(self, appointments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in patient's appointment history"""
        if not appointments:
            return {}
        
        # Analyze frequency
        appointment_dates = [datetime.strptime(apt['appointment_date'], '%Y-%m-%d') for apt in appointments]
        appointment_dates.sort()
        
        # Calculate average interval
        if len(appointment_dates) > 1:
            intervals = [(appointment_dates[i] - appointment_dates[i-1]).days for i in range(1, len(appointment_dates))]
            avg_interval = sum(intervals) / len(intervals)
        else:
            avg_interval = None
        
        # Analyze departments
        departments = [apt['department'] for apt in appointments]
        department_frequency = {}
        for dept in departments:
            department_frequency[dept] = department_frequency.get(dept, 0) + 1
        
        # Analyze time preferences
        times = [apt['appointment_time'] for apt in appointments]
        morning_count = sum(1 for t in times if int(t.split(':')[0]) < 12)
        afternoon_count = len(times) - morning_count
        
        return {
            'total_appointments': len(appointments),
            'average_interval_days': avg_interval,
            'department_frequency': department_frequency,
            'time_preference': 'morning' if morning_count > afternoon_count else 'afternoon',
            'most_visited_department': max(department_frequency.items(), key=lambda x: x[1])[0] if department_frequency else None
        }
    
    def _predict_future_appointments(self, patterns: Dict[str, Any], patient_history: Dict[str, Any]) -> Dict[str, Any]:
        """Predict future appointment needs"""
        predictions = {}
        
        if patterns.get('average_interval_days'):
            last_appointment = patient_history.get('last_appointment')
            if last_appointment:
                last_date = datetime.strptime(last_appointment['appointment_date'], '%Y-%m-%d')
                predicted_next_date = last_date + timedelta(days=patterns['average_interval_days'])
                predictions['next_appointment_date'] = predicted_next_date.strftime('%Y-%m-%d')
        
        if patterns.get('most_visited_department'):
            predictions['likely_department'] = patterns['most_visited_department']
        
        if patterns.get('time_preference'):
            predictions['preferred_time'] = patterns['time_preference']
        
        return predictions
    
    def _generate_proactive_recommendations(self, predictions: Dict[str, Any]) -> List[str]:
        """Generate proactive recommendations based on predictions"""
        recommendations = []
        
        if predictions.get('next_appointment_date'):
            recommendations.append(f"Consider scheduling next appointment around {predictions['next_appointment_date']}")
        
        if predictions.get('likely_department'):
            recommendations.append(f"Based on history, you may need {predictions['likely_department']} services")
        
        if predictions.get('preferred_time'):
            recommendations.append(f"Your preferred appointment time appears to be {predictions['preferred_time']}")
        
        recommendations.append("Set up automatic reminders for regular check-ups")
        
        return recommendations
    
    def _calculate_prediction_confidence(self, patterns: Dict[str, Any]) -> float:
        """Calculate confidence score for predictions"""
        confidence = 0.0
        
        if patterns.get('total_appointments', 0) >= 3:
            confidence += 30
        
        if patterns.get('average_interval_days'):
            confidence += 25
        
        if patterns.get('most_visited_department'):
            confidence += 25
        
        if patterns.get('time_preference'):
            confidence += 20
        
        return min(confidence, 100.0)
    
    def _predict_wait_time(self, doctor_name: str) -> str:
        """Predict wait time for a doctor"""
        # This would typically use historical data
        return "15-20 minutes"
    
    def _get_preparation_instructions(self, patient_request: str) -> List[str]:
        """Get preparation instructions based on request"""
        request_lower = patient_request.lower()
        
        if 'blood' in request_lower:
            return ["Fast for 8-12 hours before the appointment", "Bring a list of current medications"]
        elif 'x-ray' in request_lower or 'scan' in request_lower:
            return ["Remove all metal objects", "Wear comfortable clothing"]
        else:
            return ["Arrive 15 minutes early", "Bring valid ID and insurance card"]
    
    def _suggest_follow_ups(self, patient_request: str) -> List[str]:
        """Suggest follow-up actions"""
        return ["Schedule follow-up in 2-4 weeks", "Monitor symptoms and report changes"]
    
    def _get_relevant_health_tips(self, patient_request: str) -> List[str]:
        """Get relevant health tips"""
        return ["Maintain regular exercise", "Follow a balanced diet", "Stay hydrated"]
    
    def _calculate_utilization_impact(self, appointment: Appointment) -> float:
        """Calculate impact on doctor utilization"""
        # Simplified calculation
        return 0.15  # 15% impact
    
    def _calculate_patient_impact(self, appointment: Appointment) -> float:
        """Calculate impact on patient"""
        # Simplified calculation
        return 0.3  # 30% impact

