# utils.py
import vonage
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
            return True
        else:
            logger.error(f"Error sending SMS: {response_data['messages'][0]['error-text']}")
            return False
    except Exception as e:
        logger.error(f"Exception while sending SMS: {str(e)}")
        return False

def send_email(subject: str, body: str, recipient: str, priority: str = "normal"):
    """
    Send email alerts using SMTP
    
    Args:
        subject: Email subject
        body: Email body text
        recipient: Email recipient
        priority: Email priority (normal or high)
    """
    # Get email settings from environment
    smtp_server = os.getenv("SMTP_SERVER", "smtp.example.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "alert@example.com")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    
    if not smtp_user or not smtp_password:
        logger.warning("Email credentials not found in environment variables")
        # For development, just log the message
        logger.info(f"Email would be sent to {recipient}: {subject}")
        return
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = "Fleet Management System <alert@fleetapp.com>"
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Set priority headers if urgent
        if priority == "high":
            msg['X-Priority'] = '1'
            msg['X-MSMail-Priority'] = 'High'
            msg['Importance'] = 'High'
        
        # Attach body text
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to server and send
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            
        logger.info(f"Email sent successfully to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Exception while sending email: {str(e)}")
        return False