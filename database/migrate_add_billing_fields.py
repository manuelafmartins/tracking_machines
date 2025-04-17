# database/migrate_add_billing_fields.py
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

def add_billing_fields():
    """
    Adiciona campos de faturação à tabela companies
    """
    logger.info("Iniciando migração para adicionar campos de faturação à tabela companies...")
    
    try:
        # Conectar à base de dados
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Lista de novos campos a adicionar
        new_fields = [
            ("tax_id", "VARCHAR"),
            ("postal_code", "VARCHAR"),
            ("city", "VARCHAR"),
            ("country", "VARCHAR"),
            ("billing_email", "VARCHAR"),
            ("phone", "VARCHAR"),
            ("payment_method", "VARCHAR"),
            ("iban", "VARCHAR")
        ]
        
        # Verificar e adicionar cada campo
        for field_name, field_type in new_fields:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name = 'companies' AND column_name = %s
                )
            """, (field_name,))
            
            column_exists = cursor.fetchone()[0]
            
            if not column_exists:
                logger.info(f"Adicionando coluna '{field_name}' à tabela 'companies'...")
                cursor.execute(f"ALTER TABLE companies ADD COLUMN {field_name} {field_type}")
            else:
                logger.info(f"A coluna '{field_name}' já existe na tabela 'companies'.")
        
        conn.commit()
        logger.info("Migração concluída com sucesso!")
        
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
    add_billing_fields()