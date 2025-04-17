import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from . import models
from .routers import companies, machines, maintenances, auth_router, notifications_router, billing_router
from .alarms import start_scheduler
from .create_admin import create_admin_user
from .create_main_admin import create_main_admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize and create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fleet Management System",
    description="API for managing a fleet of trucks and other machines.",
    version="1.0.0"
)

# Configure CORS - in production, set specific allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """
    Runs once on application startup: logs initialization, 
    creates default admin users, and starts the scheduler.
    """
    logger.info("Starting Fleet Management API.")
    logger.info("Creating default users if needed.")
    create_main_admin()  # Creates the main admin user if not present
    # create_admin_user() # Uncomment if you need a separate general admin
    start_scheduler()

# Register routes
app.include_router(auth_router.router)
app.include_router(companies.router)
app.include_router(machines.router)
app.include_router(maintenances.router)
app.include_router(notifications_router.router)
app.include_router(billing_router.router)

@app.get("/")
def home():
    """
    Root endpoint to provide API status and basic details.
    """
    return {
        "message": "Fleet Management API",
        "version": "1.0.0",
        "docs": "/docs"
    }
