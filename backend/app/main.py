# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from . import models
from .routers import companies, machines, maintenances, auth_router
from .alarms import start_scheduler
from .create_admin import create_admin_user

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

# Create admin user if it doesn't exist
create_admin_user()

# Include routers
app.include_router(auth_router.router)
app.include_router(companies.router)
app.include_router(machines.router)
app.include_router(maintenances.router)

# Start the scheduler when API starts
start_scheduler()

@app.get("/")
def home():
    return {"message": "Fleet Management API"}