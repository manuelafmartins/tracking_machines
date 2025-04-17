import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from .database import SessionLocal
from .crud import list_pending_maintenances
from .notifications import notify_upcoming_maintenance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_maintenances():
    """
    Checks for pending maintenances and sends notifications for those within the next 7 days.
    """
    logger.info(f"Running maintenance check at {datetime.now()}")
    db = SessionLocal()
    try:
        maintenances = list_pending_maintenances(db)
        logger.info(f"Found {len(maintenances)} pending maintenances")
        for m in maintenances:
            days_remaining = (m.scheduled_date - datetime.now().date()).days
            if 0 <= days_remaining <= 7:
                try:
                    notify_upcoming_maintenance(
                        db,
                        machine_name=m.machine.name,
                        maintenance_type=m.type,
                        scheduled_date=m.scheduled_date.strftime("%d/%m/%Y"),
                        days_remaining=days_remaining,
                        company_id=m.machine.company.id,
                        company_name=m.machine.company.name
                    )
                    logger.info(f"Notified maintenance {m.id} (in {days_remaining} days)")
                except Exception as e:
                    logger.error(f"Error sending maintenance notification: {e}")
    finally:
        db.close()

def start_scheduler():
    """
    Starts the background scheduler for periodic maintenance checks.
    Includes a daily check at 8:00 and an hourly check for development.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        check_maintenances,
        "cron",
        hour=8,
        minute=0,
        id="daily_maintenance_check"
    )
    scheduler.add_job(
        check_maintenances,
        "interval",
        hours=1,
        id="hourly_maintenance_check"
    )
    scheduler.start()
    logger.info("Maintenance scheduler started!")
