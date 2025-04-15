"""
M�dulo de configura��o do banco de dados para a aplica��o.
Este arquivo configura a conex�o com o banco de dados PostgreSQL e define
fun��es auxiliares para gerenciar a conex�o.
"""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError

# Configura��o de logging para registrar erros e informa��es
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Carrega as vari�veis de ambiente do arquivo .env
try:
    load_dotenv()
    logger.info("Vari�veis de ambiente carregadas com sucesso")
except Exception as e:
    logger.error(f"Erro ao carregar vari�veis de ambiente: {str(e)}")

# Obt�m a URL de conex�o do banco de dados das vari�veis de ambiente
# Se n�o existir, usa uma URL padr�o para desenvolvimento local
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/fleetdb")
logger.info(f"Usando URL de conex�o: {DATABASE_URL.split('@')[0].split('//')[0]}//******@{DATABASE_URL.split('@')[1]}")

try:
    # Cria o motor de banco de dados SQLAlchemy
    # echo=True faz com que as consultas SQL sejam exibidas no console (�til para depura��o)
    engine = create_engine(
        DATABASE_URL, 
        echo=True,
        pool_pre_ping=True,  # Verifica se a conex�o est� ativa antes de us�-la
        pool_recycle=3600,   # Recicla conex�es ap�s 1 hora para evitar timeout
        connect_args={"connect_timeout": 15}  # Timeout de conex�o de 15 segundos
    )
    logger.info("Motor de banco de dados configurado com sucesso")
    
    # Cria uma f�brica de sess�es para o banco de dados
    # autocommit=False: transa��es n�o s�o confirmadas automaticamente
    # autoflush=False: altera��es n�o s�o sincronizadas automaticamente com o banco
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("F�brica de sess�es configurada com sucesso")
    
    # Classe base para modelos declarativos
    # Todos os modelos (classes) que representam tabelas no banco de dados herdar�o desta classe
    Base = declarative_base()
    
except SQLAlchemyError as e:
    logger.critical(f"Erro cr�tico ao configurar o banco de dados: {str(e)}")
    raise

def get_db():
    """
    Fun��o geradora para fornecer uma sess�o de banco de dados.
    
    Retorna:
        SQLAlchemy Session: Uma sess�o de banco de dados ativa.
        
    Esta fun��o � usada com o sistema de depend�ncias do FastAPI para
    injetar uma sess�o de banco de dados nos endpoints.
    A sess�o � fechada automaticamente ap�s o uso, mesmo se ocorrer uma exce��o.
    
    Exemplo de uso:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        logger.debug("Nova sess�o de banco de dados iniciada")
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Erro na sess�o de banco de dados: {str(e)}")
        db.rollback()  # Reverte altera��es em caso de erro
        raise
    finally:
        logger.debug("Sess�o de banco de dados fechada")
        db.close()  # Garante que a sess�o sempre ser� fechada