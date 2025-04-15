# Salve este código como database/migrate_add_logo_path.py
import psycopg2
import os
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Obter URL de conexão do ambiente
DATABASE_URL = os.getenv("DATABASE_URL")

def add_logo_path_column():
    """
    Adiciona a coluna logo_path à tabela companies
    """
    logger.info("Iniciando migração para adicionar coluna logo_path à tabela companies...")
    
    try:
        # Conectar à base de dados
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'companies' AND column_name = 'logo_path'
            )
        """)
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            logger.info("Adicionando coluna 'logo_path' à tabela 'companies'...")
            cursor.execute("ALTER TABLE companies ADD COLUMN logo_path VARCHAR")
            conn.commit()
            logger.info("Coluna 'logo_path' adicionada com sucesso!")
        else:
            logger.info("A coluna 'logo_path' já existe na tabela 'companies'.")
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Erro durante a migração: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    add_logo_path_column()