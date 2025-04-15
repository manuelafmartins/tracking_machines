# notifications.py
from unidecode import unidecode
import vonage
import os
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from .models import User, UserRoleEnum
from .crud import get_users_by_company, get_user_by_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Vonage API credentials
VONAGE_API_KEY = os.getenv("VONAGE_API_KEY")
VONAGE_API_SECRET = os.getenv("VONAGE_API_SECRET")

def init_vonage_client():
    """Initialize the Vonage client with API credentials"""
    if not VONAGE_API_KEY or not VONAGE_API_SECRET:
        logger.warning("Vonage API credentials not found in environment variables")
        return None
    
    try:
        client = vonage.Client(key=VONAGE_API_KEY, secret=VONAGE_API_SECRET)
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Vonage client: {str(e)}")
        return None

def send_sms_notification(phone_number: str, message: str) -> bool:
    """
    Send SMS notification using Vonage API
    
    Args:
        phone_number: Destination phone number (with country code)
        message: SMS message content
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not phone_number:
        logger.warning("No phone number provided for notification")
        return False
    
    # Initialize Vonage client
    client = init_vonage_client()
    if not client:
        logger.error("Failed to initialize Vonage client")
        return False
    
    try:
        sms = vonage.Sms(client)
        response_data = sms.send_message({
            "from": "FleetPilot",
            "to": phone_number,
            "text": message,
        })
        
        if response_data["messages"][0]["status"] == "0":
            logger.info(f"SMS notification sent successfully to {phone_number}")
            return True
        else:
            logger.error(f"Error sending SMS notification: {response_data['messages'][0]['error-text']}")
            return False
    except Exception as e:
        logger.error(f"Exception while sending SMS notification: {str(e)}")
        return False

def notify_admins(db: Session, message: str) -> int:
    """
    Send notification to all admin users
    
    Args:
        db: Database session
        message: Message content
        
    Returns:
        int: Number of successfully sent notifications
    """
    # Get all admin users with notifications enabled
    admin_users = db.query(User).filter(
        User.role == UserRoleEnum.admin,
        User.notifications_enabled == True,
        User.is_active == True,
        User.phone_number.isnot(None)  # Only users with phone numbers
    ).all()
    
    success_count = 0
    
    for admin in admin_users:
        if admin.phone_number:
            # Add timestamp to message
            timestamped_message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {message}"
            
            if send_sms_notification(admin.phone_number, timestamped_message):
                success_count += 1
    
    logger.info(f"Sent admin notifications to {success_count} of {len(admin_users)} admins")
    return success_count

def notify_company_managers(db: Session, company_id: int, message: str) -> int:
    """
    Send notification to all managers of a specific company
    
    Args:
        db: Database session
        company_id: Company ID
        message: Message content
        
    Returns:
        int: Number of successfully sent notifications
    """
    # Get all fleet managers for this company with notifications enabled
    managers = db.query(User).filter(
        User.role == UserRoleEnum.fleet_manager,
        User.company_id == company_id,
        User.notifications_enabled == True,
        User.is_active == True,
        User.phone_number.isnot(None)  # Only users with phone numbers
    ).all()
    
    success_count = 0
    
    for manager in managers:
        if manager.phone_number:
            # Add timestamp to message
            timestamped_message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {message}"
            
            if send_sms_notification(manager.phone_number, timestamped_message):
                success_count += 1
    
    logger.info(f"Sent company notifications to {success_count} of {len(managers)} managers")
    return success_count

def notify_specific_user(db: Session, user_id: int, message: str) -> bool:
    """
    Send notification to a specific user
    
    Args:
        db: Database session
        user_id: User ID
        message: Message content
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    user = get_user_by_id(db, user_id)
    
    if not user or not user.is_active or not user.notifications_enabled or not user.phone_number:
        logger.warning(f"User {user_id} cannot receive notifications")
        return False
    
    # Add timestamp to message
    timestamped_message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {message}"
    
    return send_sms_notification(user.phone_number, timestamped_message)

# Event notification functions
def notify_new_machine_added(db: Session, machine_name: str, company_id: int, company_name: str):
    """Notify admins about a new machine being added"""
    message = unidecode(f"Nova máquina '{machine_name}' adicionada à empresa '{company_name}'")
    
    # Notify admins
    notify_admins(db, message)
    
    # Notify company managers
    notify_company_managers(db, company_id, message)

def notify_new_maintenance_scheduled(db: Session, machine_name: str, maintenance_type: str, 
                                    scheduled_date: str, company_id: int, company_name: str):
    """Notify about a new maintenance being scheduled"""
    message = unidecode(f"Nova manutenção '{maintenance_type}' agendada para a máquina '{machine_name}' da empresa '{company_name}' em {scheduled_date}")
    
    # Notify admins
    notify_admins(db, message)
    
    # Notify company managers
    notify_company_managers(db, company_id, message)

def notify_maintenance_completed(db: Session, machine_name: str, maintenance_type: str, 
                               company_id: int, company_name: str):
    """Notify about a maintenance being completed"""
    message = unidecode(f"Manutenção '{maintenance_type}' para máquina '{machine_name}' da empresa '{company_name}' foi concluída")
    
    # Notify admins
    notify_admins(db, message)
    
    # Notify company managers
    notify_company_managers(db, company_id, message)

def notify_new_user_created(db: Session, username: str, role: str, company_name: Optional[str] = None):
    """Notify admins about a new user being created"""
    if company_name:
        message = unidecode(f"Novo usuário '{username}' com função '{role}' criado para empresa '{company_name}'")
    else:
        message = unidecode(f"Novo usuário '{username}' com função '{role}' criado")
    
    # Only notify admins about new users
    notify_admins(db, message)

def notify_upcoming_maintenance(db: Session, machine_name: str, maintenance_type: str, 
                              scheduled_date: str, days_remaining: int,
                              company_id: int, company_name: str):
    """Notify about an upcoming maintenance"""
    message = unidecode(f"LEMBRETE: Manutenção '{maintenance_type}' para máquina '{machine_name}' da empresa '{company_name}' agendada para {scheduled_date} (em {days_remaining} dias)")
    
    # Notify admins
    notify_admins(db, message)
    
    # Notify company managers
    notify_company_managers(db, company_id, message)