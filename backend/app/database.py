"""
Módulo de configuração do banco de dados para a aplicação.
Este arquivo configura a conexão com o banco de dados PostgreSQL e define
funções auxiliares para gerenciar a conexão.
"""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError

# Configuração de logging para registrar erros e informações
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Carrega as variáveis de ambiente do arquivo .env
try:
    load_dotenv()
    logger.info("Variáveis de ambiente carregadas com sucesso")
except Exception as e:
    logger.error(f"Erro ao carregar variáveis de ambiente: {str(e)}")

# Obtém a URL de conexão do banco de dados das variáveis de ambiente
# Se não existir, usa uma URL padrão para desenvolvimento local
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/fleetdb")
logger.info(f"Usando URL de conexão: {DATABASE_URL.split('@')[0].split('//')[0]}//******@{DATABASE_URL.split('@')[1]}")

try:
    # Cria o motor de banco de dados SQLAlchemy
    # echo=True faz com que as consultas SQL sejam exibidas no console (útil para depuração)
    engine = create_engine(
        DATABASE_URL, 
        echo=True,
        pool_pre_ping=True,  # Verifica se a conexão está ativa antes de usá-la
        pool_recycle=3600,   # Recicla conexões após 1 hora para evitar timeout
        connect_args={"connect_timeout": 15}  # Timeout de conexão de 15 segundos
    )
    logger.info("Motor de banco de dados configurado com sucesso")
    
    # Cria uma fábrica de sessões para o banco de dados
    # autocommit=False: transações não são confirmadas automaticamente
    # autoflush=False: alterações não são sincronizadas automaticamente com o banco
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Fábrica de sessões configurada com sucesso")
    
    # Classe base para modelos declarativos
    # Todos os modelos (classes) que representam tabelas no banco de dados herdarão desta classe
    Base = declarative_base()
    
except SQLAlchemyError as e:
    logger.critical(f"Erro crítico ao configurar o banco de dados: {str(e)}")
    raise

def get_db():
    """
    Função geradora para fornecer uma sessão de banco de dados.
    
    Retorna:
        SQLAlchemy Session: Uma sessão de banco de dados ativa.
        
    Esta função é usada com o sistema de dependências do FastAPI para
    injetar uma sessão de banco de dados nos endpoints.
    A sessão é fechada automaticamente após o uso, mesmo se ocorrer uma exceção.
    
    Exemplo de uso:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        logger.debug("Nova sessão de banco de dados iniciada")
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Erro na sessão de banco de dados: {str(e)}")
        db.rollback()  # Reverte alterações em caso de erro
        raise
    finally:
        logger.debug("Sessão de banco de dados fechada")
        db.close()  # Garante que a sessão sempre será fechada