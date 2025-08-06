"""
Voice Service Integration for Hospital Appointment Scheduler
Supports multiple voice service providers including free tiers
"""
import os
import json
import requests
import base64
from typing import Dict, Any, Optional
from datetime import datetime
import speech_recognition as sr
import pyttsx3
from io import BytesIO
import tempfile
import uuid
import logging

logger = logging.getLogger(__name__)

# Configuration for voice services
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

class VoiceServiceProvider:
    """Base class for voice service providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def text_to_speech(self, text: str, voice: str) -> bytes:
        """Convert text to speech audio"""
        raise NotImplementedError
    
    async def speech_to_text(self, audio_data: bytes) -> str:
        """Convert speech audio to text"""
        raise NotImplementedError

class ElevenLabsProvider(VoiceServiceProvider):
    """ElevenLabs voice service provider (free tier available)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key", ELEVENLABS_API_KEY)
        self.voice_id = config.get("voice_id", "21m00Tcm4TlvDq8ikWAM")  # Default voice
        self.base_url = "https://api.elevenlabs.io/v1"
    
    async def text_to_speech(self, text: str, voice: str) -> bytes:
        """Convert text to speech using ElevenLabs API"""
        try:
            if not self.api_key:
                raise Exception("ElevenLabs API key not configured.")

            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                return response.content
            else:
                raise Exception(f"ElevenLabs API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {str(e)}")
            raise
    
    async def speech_to_text(self, audio_data: bytes) -> str:
        """ElevenLabs doesn't provide STT, fallback to Google Speech Recognition"""
        return await self._fallback_speech_to_text(audio_data)
    
    async def _fallback_speech_to_text(self, audio_data: bytes) -> str:
        """Fallback speech to text using Google Speech Recognition (free)"""
        try:
            recognizer = sr.Recognizer()
            
            # Convert bytes to AudioFile
            audio_file = BytesIO(audio_data)
            
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
            
            # Use Google Speech Recognition (free)
            text = recognizer.recognize_google(audio)
            return text
            
        except Exception as e:
            logger.error(f"Speech recognition error: {str(e)}")
            raise

class LocalTTSProvider(VoiceServiceProvider):
    """Local text-to-speech using pyttsx3 (completely free)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            self.engine = pyttsx3.init()
            
            # Configure voice settings
            voices = self.engine.getProperty("voices")
            if voices:
                # Try to set a specific voice if available
                if config.get("voice") == "male_voice":
                    selected_voice = next((v.id for v in voices if "male" in v.name.lower()), None)
                elif config.get("voice") == "female_voice":
                    selected_voice = next((v.id for v in voices if "female" in v.name.lower()), None)
                else:
                    selected_voice = voices[0].id # Default to first available voice

                if selected_voice:
                    try:
                        self.engine.setProperty("voice", selected_voice)
                    except Exception as e:
                        logger.warning(f"Could not set voice {selected_voice}: {e}. Using default.")

            # Set speech rate and volume
            self.engine.setProperty("rate", config.get("rate", 150))
            self.engine.setProperty("volume", config.get("volume", 0.9))
        except Exception as e:
            logger.error(f"Warning: Could not initialize TTS engine: {e}")
            self.engine = None
    
    async def text_to_speech(self, text: str, voice: str) -> bytes:
        """Convert text to speech using local TTS engine"""
        if not self.engine:
            logger.error("TTS engine not initialized.")
            return b""
        
        try:
            # Create a temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Save speech to file
            self.engine.save_to_file(text, temp_path)
            self.engine.runAndWait()
            
            # Read the audio file
            with open(temp_path, "rb") as audio_file:
                audio_data = audio_file.read()
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error in local text_to_speech: {e}")
            return b""
    
    async def speech_to_text(self, audio_data: bytes) -> str:
        """Speech to text using Google Speech Recognition (free)"""
        try:
            recognizer = sr.Recognizer()
            
            # Convert bytes to AudioFile
            audio_file = BytesIO(audio_data)
            
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
            
            # Use Google Speech Recognition (free)
            text = recognizer.recognize_google(audio)
            return text
            
        except Exception as e:
            logger.error(f"Speech recognition error: {str(e)}")
            raise

class VoiceService:
    """Main voice service class that manages different providers"""
    
    def __init__(self, provider_name: str = "local", config: Dict[str, Any] = None):
        self.provider_name = provider_name
        self.config = config or {}
        
        # Initialize provider
        if provider_name == "elevenlabs":
            self.provider = ElevenLabsProvider(self.config)
        elif provider_name == "local":
            self.provider = LocalTTSProvider(self.config)
        else:
            raise ValueError(f"Unsupported voice provider: {provider_name}")

    async def text_to_speech(self, text: str, voice: str = "female_voice") -> str:
        """Convert text to speech and save to a temporary file, returning the file path."""
        audio_data = await self.provider.text_to_speech(text, voice)
        if not audio_data:
            return ""

        # Save audio to a temporary file
        temp_dir = os.path.join(os.getcwd(), "temp_audio")
        os.makedirs(temp_dir, exist_ok=True)
        file_name = f"tts_{uuid.uuid4()}.wav"
        file_path = os.path.join(temp_dir, file_name)
        
        with open(file_path, "wb") as f:
            f.write(audio_data)
        
        return file_path
    
    async def speech_to_text(self, audio_data: bytes) -> str:
        """Convert speech to text"""
        return await self.provider.speech_to_text(audio_data)

# Global instance of VoiceService
voice_service_instance = VoiceService(provider_name=os.getenv("VOICE_PROVIDER", "local"))

async def text_to_speech(text: str, voice: str = "female_voice") -> str:
    """Global function to convert text to speech and return file path."""
    return await voice_service_instance.text_to_speech(text, voice)

async def speech_to_text(audio_data: bytes) -> str:
    """Global function to convert speech to text."""
    return await voice_service_instance.speech_to_text(audio_data)


