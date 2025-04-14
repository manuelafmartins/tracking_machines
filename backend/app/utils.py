# utils.py
import vonage
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

def send_sms(text: str, destination_number: str):
    """
    Send SMS using Vonage (formerly Nexmo) API
    """
    api_key = os.getenv("VONAGE_API_KEY")
    api_secret = os.getenv("VONAGE_API_SECRET")
    
    if not api_key or not api_secret:
        logger.warning("Vonage API credentials not found in environment variables")
        # For development, just log the message
        logger.info(f"SMS would be sent to {destination_number}: {text}")
        return
    
    try:
        client = vonage.Client(key=api_key, secret=api_secret)
        sms = vonage.Sms(client)
        response_data = sms.send_message({
            "from": "FleetApp",
            "to": destination_number,
            "text": text,
        })
        
        if response_data["messages"][0]["status"] == "0":
            logger.info(f"SMS sent successfully to {destination_number}")
        else:
            logger.error(f"Error sending SMS: {response_data['messages'][0]['error-text']}")
    except Exception as e:
        logger.error(f"Exception while sending SMS: {str(e)}")