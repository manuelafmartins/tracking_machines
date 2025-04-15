"""
Database configuration module for the application.
This file sets up the connection to the PostgreSQL database and defines
helper functions to manage the connection.
"""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError

# Logging configuration to record errors and information
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    load_dotenv()
    logger.info("Environment variables loaded successfully")
except Exception as e:
    logger.error(f"Error loading environment variables: {str(e)}")

# Get database connection URL from environment variables
# If it doesn't exist, use a default URL for local development
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/fleetdb")
logger.info(f"Using connection URL: {DATABASE_URL.split('@')[0].split('//')[0]}//******@{DATABASE_URL.split('@')[1]}")

try:
    # Create the SQLAlchemy database engine
    # echo=True makes SQL queries display in the console (useful for debugging)
    engine = create_engine(
        DATABASE_URL, 
        echo=True,
        pool_pre_ping=True,  # Checks if the connection is active before using it
        pool_recycle=3600,   # Recycles connections after 1 hour to avoid timeout
        connect_args={"connect_timeout": 15}  # Connection timeout of 15 seconds
    )
    logger.info("Database engine configured successfully")
    
    # Create a session factory for the database
    # autocommit=False: transactions are not committed automatically
    # autoflush=False: changes are not synchronized automatically with the database
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Session factory configured successfully")
    
    # Base class for declarative models
    # All models (classes) that represent tables in the database will inherit from this class
    Base = declarative_base()
    
except SQLAlchemyError as e:
    logger.critical(f"Critical error while configuring the database: {str(e)}")
    raise

def get_db():
    """
    Generator function to provide a database session.
    
    Returns:
        SQLAlchemy Session: An active database session.
        
    This function is used with FastAPI's dependency injection system to
    inject a database session into endpoints.
    The session is automatically closed after use, even if an exception occurs.
    
    Usage example:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        logger.debug("New database session started")
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Error in database session: {str(e)}")
        db.rollback()  # Rollback changes in case of error
        raise
    finally:
        logger.debug("Database session closed")
        db.close()  # Ensures that the session is always closed