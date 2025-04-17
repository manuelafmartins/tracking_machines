# database/migrate_billing_tables.py
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

def create_billing_tables():
    """
    Cria as tabelas para o módulo de faturação
    """
    logger.info("Iniciando migração para adicionar tabelas de faturação...")
    
    try:
        # Conectar à base de dados
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Verificar se o tipo InvoiceStatusEnum já existe
        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'invoicestatusenum')")
        enum_exists = cursor.fetchone()[0]
        
        if not enum_exists:
            logger.info("Criando tipo InvoiceStatusEnum...")
            cursor.execute("CREATE TYPE invoicestatusenum AS ENUM ('draft', 'sent', 'paid', 'overdue', 'canceled')")
        
        # Verificar se as tabelas já existem
        tables_to_check = ['services', 'invoices', 'invoice_items']
        existing_tables = []
        
        for table in tables_to_check:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                )
            """)
            if cursor.fetchone()[0]:
                existing_tables.append(table)
        
        logger.info(f"Tabelas existentes: {existing_tables}")
        
        # Criar tabela de serviços
        if 'services' not in existing_tables:
            logger.info("Criando tabela 'services'...")
            cursor.execute("""
                CREATE TABLE services (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    description TEXT,
                    unit_price FLOAT NOT NULL,
                    tax_rate FLOAT DEFAULT 23.0,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            logger.info("Tabela 'services' criada com sucesso.")
        
        # Criar tabela de faturas
        if 'invoices' not in existing_tables:
            logger.info("Criando tabela 'invoices'...")
            cursor.execute("""
                CREATE TABLE invoices (
                    id SERIAL PRIMARY KEY,
                    invoice_number VARCHAR UNIQUE NOT NULL,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    issue_date DATE NOT NULL,
                    due_date DATE NOT NULL,
                    status invoicestatusenum DEFAULT 'draft',
                    subtotal FLOAT DEFAULT 0.0,
                    tax_total FLOAT DEFAULT 0.0,
                    total FLOAT DEFAULT 0.0,
                    notes TEXT,
                    payment_method VARCHAR,
                    payment_date DATE
                )
            """)
            logger.info("Tabela 'invoices' criada com sucesso.")
        
        # Criar tabela de itens de fatura
        if 'invoice_items' not in existing_tables:
            logger.info("Criando tabela 'invoice_items'...")
            cursor.execute("""
                CREATE TABLE invoice_items (
                    id SERIAL PRIMARY KEY,
                    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
                    service_id INTEGER NOT NULL REFERENCES services(id),
                    machine_id INTEGER REFERENCES machines(id),
                    quantity FLOAT NOT NULL DEFAULT 1.0,
                    unit_price FLOAT NOT NULL,
                    tax_rate FLOAT NOT NULL,
                    subtotal FLOAT NOT NULL,
                    tax_amount FLOAT NOT NULL,
                    total FLOAT NOT NULL,
                    description VARCHAR
                )
            """)
            logger.info("Tabela 'invoice_items' criada com sucesso.")
        
        # Commit das alterações
        conn.commit()
        logger.info("Migração de tabelas de faturação concluída com sucesso!")
        
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
    create_billing_tables()