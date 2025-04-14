# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from . import models
from .routers import companies, machines, maintenances, auth_router
from .alarms import start_scheduler
from .create_admin import create_admin_user
from .create_main_admin import create_main_admin
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fleet Management System",
    description="API for managing fleet of trucks and other machines",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create default users if they don't exist
@app.on_event("startup")
def startup_event():
    logger.info("Starting Fleet Management API")
    logger.info("Creating default users if needed")
    
    # Create main administrator (Filipe Ferreira)
    create_main_admin()
    
    # Start the scheduler for maintenance alerts
    start_scheduler()

# Include routers
app.include_router(auth_router.router)
app.include_router(companies.router)
app.include_router(machines.router)
app.include_router(maintenances.router)

@app.get("/")
def home():
    return {
        "message": "Fleet Management API",
        "version": "1.0.0",
        "docs": "/docs"
    }