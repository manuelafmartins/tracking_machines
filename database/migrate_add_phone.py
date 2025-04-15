# database/migrate_add_phone.py
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

def add_phone_column():
    """
    Adiciona a coluna phone_number à tabela users
    """
    logger.info("Iniciando migração para adicionar coluna phone_number à tabela users...")
    
    try:
        # Conectar à base de dados
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'phone_number'
            )
        """)
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            logger.info("Adicionando coluna 'phone_number' à tabela 'users'...")
            cursor.execute("ALTER TABLE users ADD COLUMN phone_number VARCHAR(20)")
            conn.commit()
            logger.info("Coluna 'phone_number' adicionada com sucesso!")
        else:
            logger.info("A coluna 'phone_number' já existe na tabela 'users'.")
        
        # Agora vamos adicionar também uma coluna para controlar notificações
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'notifications_enabled'
            )
        """)
        notif_column_exists = cursor.fetchone()[0]
        
        if not notif_column_exists:
            logger.info("Adicionando coluna 'notifications_enabled' à tabela 'users'...")
            cursor.execute("ALTER TABLE users ADD COLUMN notifications_enabled BOOLEAN DEFAULT TRUE")
            conn.commit()
            logger.info("Coluna 'notifications_enabled' adicionada com sucesso!")
        else:
            logger.info("A coluna 'notifications_enabled' já existe na tabela 'users'.")
        
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
    add_phone_column()