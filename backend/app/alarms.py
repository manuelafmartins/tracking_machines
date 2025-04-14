# alarms.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from .database import SessionLocal
from .crud import list_pending_maintenances
from .utils import send_sms
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_maintenances():
    """
    Check pending maintenances and send SMS alerts
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
            else:
                prefix = "Notice: "
                
            msg = f"{prefix}Maintenance '{m.type}' for machine '{m.machine.name}' " \
                  f"from company '{m.machine.company.name}' scheduled for {m.scheduled_date}."
            
            # Contact numbers could come from company registration
            contact_numbers = ["351911234567"]  # In production, fetch from database
            
            # Send to each number
            for number in contact_numbers:
                try:
                    send_sms(msg, number)
                    logger.info(f"SMS sent to {number}")
                except Exception as e:
                    logger.error(f"Error sending SMS: {str(e)}")
    
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
    
    # For development, we can also add an interval check
    scheduler.add_job(
        check_maintenances, 
        'interval', 
        hours=24,
        id='daily_check'
    )
    
    scheduler.start()
    logger.info("Maintenance scheduler started!")