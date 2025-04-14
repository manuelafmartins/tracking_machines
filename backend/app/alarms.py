# alarms.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from .database import SessionLocal
from .crud import list_pending_maintenances, get_company_by_id
from .utils import send_sms, send_email
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_maintenances():
    """
    Check pending maintenances and send alerts through available channels
    """
    logger.info(f"Running maintenance check at {datetime.now()}")
    
    db = SessionLocal()
    try:
        maintenances = list_pending_maintenances(db)
        logger.info(f"Found {len(maintenances)} pending maintenances")
        
        for m in maintenances:
            days_remaining = (m.scheduled_date - datetime.now().date()).days
            
            # Format message based on urgency
            if days_remaining <= 2:
                prefix = "URGENT! "
                priority = "high"
            else:
                prefix = "Notice: "
                priority = "normal"
                
            msg = f"{prefix}Maintenance '{m.type}' for machine '{m.machine.name}' " \
                  f"from company '{m.machine.company.name}' scheduled for {m.scheduled_date}."
            
            # Get company responsible for this machine
            company = m.machine.company
            
            # In a production environment, these would come from company settings
            contact_numbers = ["351911234567"]  # Demo number
            contact_emails = ["manager@example.com"]  # Demo email
            
            # Send SMS notifications
            for number in contact_numbers:
                try:
                    send_sms(msg, number)
                    logger.info(f"SMS alert sent to {number}")
                except Exception as e:
                    logger.error(f"Error sending SMS: {str(e)}")
            
            # Send email notifications
            for email in contact_emails:
                try:
                    subject = f"{prefix}Maintenance Alert for {m.machine.name}"
                    send_email(subject, msg, email, priority)
                    logger.info(f"Email alert sent to {email}")
                except Exception as e:
                    logger.error(f"Error sending email: {str(e)}")
    
    finally:
        db.close()

def start_scheduler():
    """
    Start the task scheduler for periodic maintenance checks
    """
    scheduler = BackgroundScheduler()
    
    # Check maintenances daily at 8:00
    scheduler.add_job(
        check_maintenances, 
        'cron', 
        hour=8, 
        minute=0,
        id='maintenance_check'
    )
    
    # For development, add an interval check every hour
    scheduler.add_job(
        check_maintenances, 
        'interval', 
        hours=1,
        id='hourly_check'
    )
    
    scheduler.start()
    logger.info("Maintenance scheduler started!")