import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""

    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gpt_model: str = "gpt-4"  # Updated to use GPT-4 for better mental health analysis
    max_tokens: int = 2000  # Increased for longer reports
    temperature: float = 0.3  # Lower temperature for more consistent reports

    # WhatsApp Configuration
    whatsapp_api_token: str = os.getenv("WHATSAPP_API_TOKEN", "")
    whatsapp_phone_number_id: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    verify_token: str = os.getenv("VERIFY_TOKEN", "")
    whatsapp_api_version: str = "v21.0"

    # Server Configuration
    port: int = int(os.getenv("PORT", "8000"))
    host: str = "0.0.0.0"

    # Audio Processing Configuration
    max_audio_duration: int = int(os.getenv("MAX_AUDIO_DURATION", "3000"))  # 50 minutes in seconds
    supported_audio_formats: list = ["audio/mpeg", "audio/wav", "audio/ogg", "audio/x-wav", "audio/x-mp3"]
    speech_recognition_energy_threshold: int = 4000
    speech_recognition_dynamic_energy_threshold: bool = True
    speech_recognition_pause_threshold: float = 0.8

    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "chatbot.log")

    # Mental Health Report Configuration
    report_template: str = """
    Mental Health Conversation Report
    Date: {date}
    Duration: {duration}
    
    Overview:
    {overview}
    
    Key Points:
    {key_points}
    
    Mental Health Observations:
    {observations}
    
    Concerning Patterns:
    {patterns}
    
    Urgent Concerns:
    {urgent_concerns}
    
    Recommendations:
    {recommendations}
    """

    # Use the new SettingsConfigDict instead of the inner Config class
    model_config = SettingsConfigDict(env_file=".env")


# Create settings instance
settings = Settings()

# WhatsApp API URL
WHATSAPP_API_URL = f"https://graph.facebook.com/{settings.whatsapp_api_version}/{settings.whatsapp_phone_number_id}/messages"