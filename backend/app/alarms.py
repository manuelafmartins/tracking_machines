# alarms.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import logging

from .database import SessionLocal
from .crud import list_pending_maintenances, get_company_by_id
from .notifications import (notify_upcoming_maintenance, 
                           send_sms_notification, 
                           notify_admins)

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
            
            # Get company responsible for this machine
            company = m.machine.company
            company_id = company.id
            company_name = company.name
            
            # Notify based on urgency
            if days_remaining <= 2:
                prefix = "URGENTE! "
                priority = "high"
            else:
                prefix = "Aviso: "
                priority = "normal"
            
            # Only notify if we're in the alert window (0-7 days)
            if 0 <= days_remaining <= 7:
                try:
                    # Use the new notification system
                    notify_upcoming_maintenance(
                        db,
                        machine_name=m.machine.name,
                        maintenance_type=m.type,
                        scheduled_date=m.scheduled_date.strftime("%d/%m/%Y"),
                        days_remaining=days_remaining,
                        company_id=company_id,
                        company_name=company_name
                    )
                    logger.info(f"Notification sent for maintenance {m.id} (in {days_remaining} days)")
                except Exception as e:
                    logger.error(f"Error sending maintenance notification: {str(e)}")
    
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