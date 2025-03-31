import logging
from typing import Optional
from config import settings
import tempfile
import subprocess
import os
import whisper
from services.openai_service import OpenAIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioService:
    """Service for handling audio processing and transcription"""

    def __init__(self):
        logger.info("Initializing AudioService...")
        # Initialize Whisper model
        try:
            logger.info("Loading Whisper model...")
            self.model = whisper.load_model("base")
            logger.info("Whisper model loaded successfully")

            # Initialize OpenAI service
            self.openai_service = OpenAIService(settings.openai_api_key)
            logger.info("OpenAI service initialized")
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
            raise

    async def transcribe_audio(
        self, audio_data: bytes, file_type: str = "ogg"
    ) -> Optional[str]:
        """Transcribe audio to text using Whisper"""
        try:
            logger.info(f"Starting audio transcription process for {file_type} file")
            # Save the audio data to a temporary file
            with tempfile.NamedTemporaryFile(
                suffix=f".{file_type}", delete=False
            ) as temp_input:
                temp_input.write(audio_data)
                temp_input_path = temp_input.name
                logger.info(f"Saved audio to temporary file: {temp_input_path}")

            # Convert to WAV using ffmpeg
            temp_wav_path = temp_input_path.replace(f".{file_type}", ".wav")
            logger.info(f"Converting audio to WAV format: {temp_wav_path}")

            # Handle different input formats
            if file_type == "mp4":
                # Extract audio from MP4
                subprocess.run(
                    [
                        "ffmpeg",
                        "-i",
                        temp_input_path,
                        "-vn",  # No video
                        "-acodec",
                        "pcm_s16le",
                        "-ar",
                        "16000",
                        "-ac",
                        "1",
                        temp_wav_path,
                    ],
                    check=True,
                )
            else:
                # Handle MP3 and OGG
                subprocess.run(
                    [
                        "ffmpeg",
                        "-i",
                        temp_input_path,
                        "-acodec",
                        "pcm_s16le",
                        "-ar",
                        "16000",
                        "-ac",
                        "1",
                        temp_wav_path,
                    ],
                    check=True,
                )

            logger.info("Audio conversion completed")

            # Transcribe using Whisper
            logger.info("Starting Whisper transcription")
            result = self.model.transcribe(temp_wav_path)
            transcript = result["text"].strip()
            logger.info(f"Transcription completed: {transcript[:100]}...")

            # Clean up temporary files
            os.unlink(temp_input_path)
            os.unlink(temp_wav_path)
            logger.info("Temporary files cleaned up")

            return transcript

        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return None

    async def generate_report(self, transcript: str) -> Optional[str]:
        """Generate a structured report from the transcript"""
        try:
            logger.info("Starting report generation")
            # Use OpenAI service to generate the report
            response = await self.openai_service.generate_report(transcript)
            if not response:
                logger.error("Failed to generate report using OpenAI")
                return None

            logger.info("Report generated successfully")
            return response

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return None
