# Mental Health Caregiver Audio-to-Report WhatsApp Bot

A WhatsApp bot that helps mental health caregivers by automatically transcribing patient conversations and generating structured reports.

## Features

- Accepts audio recordings via WhatsApp
- Transcribes audio using Whisper
- Generates structured reports with key observations
- Highlights important mental health information
- Provides recommendations based on conversation analysis

## Prerequisites

- Python 3.8 or higher
- WhatsApp Business API account
- OpenAI API key
- FFmpeg installed for audio processing

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd mental-health-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with the following variables:
```env
WHATSAPP_API_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
VERIFY_TOKEN=your_webhook_verify_token
OPENAI_API_KEY=your_openai_api_key
```

5. Set up WhatsApp webhook:
   - Deploy the application to a server with HTTPS
   - Configure the webhook URL in your WhatsApp Business API settings
   - Set the verify token to match your `VERIFY_TOKEN` in the `.env` file

## Usage

1. Start the server:
```bash
python main.py
```

2. Send a message to your WhatsApp bot:
   - Send "help" or "start" to get usage instructions
   - Send an audio recording of a patient conversation
   - Wait for the bot to process the audio and generate a report
   - Receive a structured report with key observations

## Report Structure

The generated report includes:
- Overview of the conversation
- Key points discussed
- Mental health observations
- Concerning patterns
- Urgent concerns
- Recommendations

## Error Handling

The bot handles various error scenarios:
- Invalid audio format
- Failed transcription
- Processing errors
- Network issues
- API rate limits

## Security Considerations

- All API keys are stored securely in environment variables
- Audio files are processed securely and not stored permanently
- Reports are generated with appropriate privacy considerations
- HIPAA compliance guidelines are followed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the repository or contact the maintainers.