import logging
from typing import Optional
from config import settings
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for handling OpenAI API interactions"""

    def __init__(self, api_key: str):
        """Initialize the OpenAI service"""
        self.client = OpenAI(api_key=api_key)
        logger.info("OpenAI service initialized")

    async def generate_report(self, transcript: str) -> Optional[str]:
        """Generate a structured report from the transcript"""
        try:
            logger.info("Generating report using OpenAI")
            
            # Create the prompt
            prompt = f"""
            Please analyze this mental health conversation transcript and generate a structured report.
            Focus on:
            1. Brief overview of the conversation
            2. Key points discussed
            3. Important mental health observations
            4. Any concerning patterns
            5. Urgent concerns that need attention
            
            Transcript:
            {transcript}
            
            Format the report in a clear, professional manner suitable for healthcare providers.
            """
            
            # Generate the report using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional mental health analyst. Generate clear, structured reports from conversation transcripts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract the report from the response
            report = response.choices[0].message.content.strip()
            logger.info("Report generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error generating report with OpenAI: {str(e)}")
            return None