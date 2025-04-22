import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/fleetdb")
masked_db_url = f"{DATABASE_URL.rsplit('@', 1)[0]}@*****"
#logger.info(f"Connecting to database: {masked_db_url}")

try:
    engine = create_engine(
        DATABASE_URL,
        echo=True,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={"connect_timeout": 15}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    #logger.info("Database configuration successful.")
except SQLAlchemyError as e:
    logger.critical(f"Critical database error: {e}")
    raise


def get_db():
    """
    Yields a new database session and ensures it closes properly.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        #logger.error(f"Session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
