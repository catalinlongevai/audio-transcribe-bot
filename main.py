from fastapi import FastAPI, Request, HTTPException
import uvicorn
import json
import os
from typing import Optional
from datetime import datetime
from config import settings
from services.whatsapp_service import WhatsAppService
from services.openai_service import OpenAIService
from services.audio_service import AudioService
from utils.logging_utils import setup_logger, log_webhook_request

# Configure logging
logger = setup_logger("mental_health_bot", log_file="chatbot.log")

# Initialize FastAPI app
app = FastAPI(title="Mental Health Caregiver Audio-to-Report Bot")

# Initialize services
whatsapp_service = WhatsAppService(
    api_token=settings.whatsapp_api_token,
    phone_number_id=settings.whatsapp_phone_number_id,
    api_version=settings.whatsapp_api_version
)

openai_service = OpenAIService(api_key=settings.openai_api_key)
audio_service = AudioService()

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify server is accessible"""
    return {"status": "ok", "message": "Server is running and accessible"}

@app.post("/test-webhook")
async def test_webhook(request: Request):
    """Test endpoint to verify webhook reception"""
    try:
        body = await request.json()
        logger.info("=== TEST WEBHOOK RECEIVED ===")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Body: {json.dumps(body, indent=2)}")
        return {"status": "success", "message": "Test webhook received"}
    except Exception as e:
        logger.error(f"Error in test webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Verify webhook for WhatsApp API setup"""
    try:
        params = dict(request.query_params)
        logger.info(f"Received webhook verification request with params: {params}")
        logger.info(f"Request headers: {dict(request.headers)}")

        # If no params, try to get them from headers
        if not params:
            params = {
                "hub.mode": request.headers.get("hub-mode"),
                "hub.verify_token": request.headers.get("hub-verify-token"),
                "hub.challenge": request.headers.get("hub-challenge")
            }
            logger.info(f"Extracted params from headers: {params}")

        mode = params.get("hub.mode")
        token = params.get("hub.verify_token")
        challenge = params.get("hub.challenge")

        logger.info(f"Mode: {mode}, Token: {token}, Challenge: {challenge}")
        logger.info(f"Expected token: {settings.verify_token}")

        if mode and token:
            if mode == "subscribe" and token == settings.verify_token:
                if challenge:
                    logger.info(f"Webhook verified! Returning challenge: {challenge}")
                    return int(challenge)
                logger.error("Challenge parameter missing")
                raise HTTPException(status_code=400, detail="Challenge parameter missing")
            logger.error(f"Invalid verify token. Expected {settings.verify_token}, got {token}")
            raise HTTPException(status_code=403, detail="Invalid verify token")
        logger.error("Missing mode or token")
        raise HTTPException(status_code=400, detail="Invalid request")
    except Exception as e:
        logger.error(f"Error in webhook verification: {str(e)}")
        raise

@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming WhatsApp messages"""
    try:
        logger.info("=== NEW WEBHOOK REQUEST ===")
        logger.info("Received POST request to /webhook")
        
        # Log raw request body
        body = await request.json()
        logger.info("Raw webhook body:")
        logger.info(json.dumps(body, indent=2))
        
        # Extract the data
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        
        logger.info("=== WEBHOOK DATA STRUCTURE ===")
        logger.info("Entry:")
        logger.info(json.dumps(entry, indent=2))
        logger.info("Changes:")
        logger.info(json.dumps(changes, indent=2))
        logger.info("Value:")
        logger.info(json.dumps(value, indent=2))

        # Check if this is a message or a status update
        messages = value.get("messages", [])
        statuses = value.get("statuses", [])

        # If it's a status update, just acknowledge it
        if statuses:
            logger.info("=== STATUS UPDATE ===")
            logger.info(json.dumps(statuses, indent=2))
            return {"status": "status update received"}

        # If no messages, return early
        if not messages or len(messages) == 0:
            logger.warning("No messages found in webhook body")
            return {"status": "no message"}

        message = messages[0]
        phone_number = message.get("from")
        logger.info(f"=== MESSAGE RECEIVED FROM: {phone_number} ===")
        logger.info("Full message data:")
        logger.info(json.dumps(message, indent=2))

        if not phone_number:
            logger.warning("Message received without a phone number")
            return {"status": "error", "message": "No phone number provided"}

        message_type = message.get("type", "text")
        logger.info(f"Message type: {message_type}")

        # Handle audio messages and audio documents
        if message_type in ["audio", "document"]:
            try:
                logger.info("=== PROCESSING AUDIO MESSAGE ===")
                # Get audio data
                if message_type == "audio":
                    media_data = message.get("audio", {})
                else:  # document
                    media_data = message.get("document", {})
                    # Check if it's an audio document
                    mime_type = media_data.get("mime_type", "")
                    if not any(audio_type in mime_type for audio_type in ["audio/", "video/"]):
                        error_msg = "I can only process audio files. Please send an audio message or audio file."
                        logger.warning(f"Unsupported document type: {mime_type}")
                        whatsapp_service.send_message(phone_number, error_msg)
                        return {"status": "error", "message": "Unsupported document type"}
                
                logger.info("Media data:")
                logger.info(json.dumps(media_data, indent=2))
                
                if media_data and (media_id := media_data.get("id")):
                    logger.info(f"Processing audio with ID: {media_id}")
                    media_url = WhatsAppService.get_media_url(
                        media_id, settings.whatsapp_api_token, settings.whatsapp_api_version
                    )
                    logger.info(f"Retrieved media URL: {media_url}")
                    
                    if not media_url:
                        error_msg = "Failed to retrieve audio URL. Please try sending the audio again."
                        logger.error("Failed to get media URL")
                        whatsapp_service.send_message(phone_number, error_msg)
                        return {"status": "error", "message": "Failed to get media URL"}

                    audio_data = WhatsAppService.download_media(
                        media_url, settings.whatsapp_api_token
                    )
                    logger.info(f"Downloaded audio data size: {len(audio_data) if audio_data else 0} bytes")
                    
                    if not audio_data:
                        error_msg = "Failed to download audio. Please try sending the audio again."
                        logger.error("Failed to download media")
                        whatsapp_service.send_message(phone_number, error_msg)
                        return {"status": "error", "message": "Failed to download media"}

                    # Send processing message
                    processing_msg = "I'm processing your audio recording. This may take a few minutes..."
                    logger.info("Sending processing message")
                    whatsapp_service.send_message(phone_number, processing_msg)

                    # Get file type from mime_type
                    mime_type = media_data.get("mime_type", "")
                    file_type = "ogg"  # default
                    if "mp3" in mime_type:
                        file_type = "mp3"
                    elif "mp4" in mime_type:
                        file_type = "mp4"
                    logger.info(f"Processing file type: {file_type}")

                    # Transcribe audio
                    logger.info("Starting audio transcription")
                    transcript = await audio_service.transcribe_audio(audio_data, file_type)
                    if not transcript:
                        error_msg = "Failed to transcribe the audio. Please try again with a clearer recording."
                        logger.error("Transcription failed")
                        whatsapp_service.send_message(phone_number, error_msg)
                        return {"status": "error", "message": "Transcription failed"}
                    logger.info(f"Transcription successful: {transcript[:100]}...")

                    # Generate report
                    logger.info("Starting report generation")
                    report = await audio_service.generate_report(transcript)
                    if not report:
                        error_msg = "Failed to generate the report. Please try again."
                        logger.error("Report generation failed")
                        whatsapp_service.send_message(phone_number, error_msg)
                        return {"status": "error", "message": "Report generation failed"}
                    logger.info("Report generated successfully")

                    # Send report
                    logger.info("Sending report")
                    whatsapp_service.send_message(phone_number, report)
                    return {"status": "success"}

            except Exception as e:
                logger.error(f"Error processing audio message: {str(e)}")
                error_msg = "I encountered an error processing your audio. Please try again."
                whatsapp_service.send_message(phone_number, error_msg)
                return {"status": "error", "message": str(e)}

        # Handle text messages
        elif message_type == "text":
            message_text = message.get("text", {}).get("body", "")
            logger.info(f"Received text message: {message_text}")
            
            if message_text.lower() in ["help", "start"]:
                help_message = """
                Welcome to the Mental Health Caregiver Audio-to-Report Bot!
                
                To use this bot:
                1. Send an audio recording of your patient conversation
                2. Wait while I process the audio and generate a report
                3. You'll receive a structured report with key observations
                
                The report will include:
                - Overview of the conversation
                - Key points discussed
                - Mental health observations
                - Concerning patterns
                - Urgent concerns
                - Recommendations
                
                Please ensure your audio recording is clear.
                """
                logger.info("Sending help message")
                whatsapp_service.send_message(phone_number, help_message)
                return {"status": "success"}
            else:
                error_msg = "I can only process audio recordings. Please send an audio message of your patient conversation."
                logger.info("Sending unsupported message type response")
                whatsapp_service.send_message(phone_number, error_msg)
                return {"status": "error", "message": "Unsupported message type"}

        else:
            logger.warning(f"Unsupported message type: {message_type}")
            error_msg = "I can only process audio recordings. Please send an audio message of your patient conversation."
            whatsapp_service.send_message(phone_number, error_msg)
            return {"status": "error", "message": "Unsupported message type"}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {
            "status": "error",
            "message": "Failed to process webhook",
            "error": str(e),
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/test-whatsapp")
async def test_whatsapp():
    """Test endpoint to send a WhatsApp message"""
    try:
        # Replace with your test phone number
        test_number = "+40736259759"  # Replace with your actual phone number
        test_message = "This is a test message from the Mental Health Bot. If you receive this, the WhatsApp API is working correctly."
        
        logger.info(f"Attempting to send test message to {test_number}")
        logger.info(f"Using WhatsApp API URL: {whatsapp_service.api_url}")
        logger.info(f"Using phone number ID: {whatsapp_service.phone_number_id}")
        
        result = whatsapp_service.send_message(test_number, test_message)
        logger.info(f"Test message result: {result}")
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error sending test message: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Start server
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)