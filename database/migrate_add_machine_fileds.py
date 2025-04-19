# database/migrate_add_machine_fields.py
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

def add_machine_fields():
    """
    Adiciona campos expandidos à tabela machines
    """
    logger.info("Iniciando migração para adicionar campos expandidos à tabela machines...")
    
    try:
        # Conectar à base de dados
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Lista de novos campos a adicionar
        new_fields = [
            # Campos comuns
            ("brand", "VARCHAR"),
            ("model", "VARCHAR"),
            ("year", "INTEGER"),
            ("serial_number", "VARCHAR"),
            ("purchase_date", "DATE"),
            
            # Campos específicos para camiões
            ("license_plate", "VARCHAR"),
            ("vehicle_identification_number", "VARCHAR"),
            
            # Campos específicos para máquinas fixas
            ("location", "VARCHAR"),
            ("installation_date", "DATE")
        ]
        
        # Verificar e adicionar cada campo
        for field_name, field_type in new_fields:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name = 'machines' AND column_name = %s
                )
            """, (field_name,))
            
            column_exists = cursor.fetchone()[0]
            
            if not column_exists:
                logger.info(f"Adicionando coluna '{field_name}' à tabela 'machines'...")
                cursor.execute(f"ALTER TABLE machines ADD COLUMN {field_name} {field_type}")
            else:
                logger.info(f"A coluna '{field_name}' já existe na tabela 'machines'.")
        
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
    add_machine_fields()