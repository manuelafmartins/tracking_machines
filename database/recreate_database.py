# recreate_database.py
import psycopg2
import os
from dotenv import load_dotenv
import logging
from passlib.context import CryptContext

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Obter URL de conexão do ambiente
DATABASE_URL = os.getenv("DATABASE_URL")

# Criar contexto para hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def execute_safely(cursor, query, params=None, commit_conn=None):
    """Executa uma query com tratamento de erro e commit opcional"""
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        if commit_conn:
            commit_conn.commit()
        return True
    except Exception as e:
        if commit_conn:
            commit_conn.rollback()
        logger.warning(f"Erro ao executar query: {str(e)}")
        logger.warning(f"Query: {query}")
        if params:
            logger.warning(f"Parâmetros: {params}")
        return False

def recreate_database():
    """
    Recria o banco de dados com a nova estrutura e preserva os dados.
    """
    logger.info("Iniciando recriação da base de dados...")
    
    conn = None
    try:
        # Conectar à base de dados
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Desativar verificação de chaves estrangeiras (se possível)
        logger.info("Tentando desativar verificação de chaves estrangeiras...")
        execute_safely(cursor, "SET session_replication_role = 'replica'", commit_conn=conn)
        
        # Fazer backup dos dados existentes
        logger.info("Fazendo backup dos dados existentes...")
        
        # Verificar se as tabelas existem
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('companies', 'machines', 'maintenances', 'users')
            AND table_schema = 'public'
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Tabelas existentes: {existing_tables}")
        
        # Backup dos dados das tabelas existentes
        companies_data = []
        machines_data = []
        maintenances_data = []
        users_data = []
        
        companies_columns = []
        machines_columns = []
        maintenances_columns = []
        users_columns = []
        
        if 'companies' in existing_tables:
            try:
                cursor.execute("SELECT * FROM companies")
                companies_data = cursor.fetchall()
                logger.info(f"Backup de {len(companies_data)} empresas")
                
                # Obter os nomes das colunas para companies
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'companies' ORDER BY ordinal_position")
                companies_columns = [row[0] for row in cursor.fetchall()]
                logger.info(f"Colunas da tabela companies: {companies_columns}")
            except Exception as e:
                logger.warning(f"Erro ao fazer backup de companies: {str(e)}")
                conn.rollback()
        
        if 'machines' in existing_tables:
            try:
                cursor.execute("SELECT * FROM machines")
                machines_data = cursor.fetchall()
                logger.info(f"Backup de {len(machines_data)} máquinas")
                
                # Obter os nomes das colunas para machines
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'machines' ORDER BY ordinal_position")
                machines_columns = [row[0] for row in cursor.fetchall()]
                logger.info(f"Colunas da tabela machines: {machines_columns}")
            except Exception as e:
                logger.warning(f"Erro ao fazer backup de machines: {str(e)}")
                conn.rollback()
        
        if 'maintenances' in existing_tables:
            try:
                cursor.execute("SELECT * FROM maintenances")
                maintenances_data = cursor.fetchall()
                logger.info(f"Backup de {len(maintenances_data)} manutenções")
                
                # Obter os nomes das colunas para maintenances
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'maintenances' ORDER BY ordinal_position")
                maintenances_columns = [row[0] for row in cursor.fetchall()]
                logger.info(f"Colunas da tabela maintenances: {maintenances_columns}")
            except Exception as e:
                logger.warning(f"Erro ao fazer backup de maintenances: {str(e)}")
                conn.rollback()
        
        if 'users' in existing_tables:
            try:
                cursor.execute("SELECT * FROM users")
                users_data = cursor.fetchall()
                logger.info(f"Backup de {len(users_data)} usuários")
                
                # Obter os nomes das colunas para users
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position")
                users_columns = [row[0] for row in cursor.fetchall()]
                logger.info(f"Colunas da tabela users: {users_columns}")
            except Exception as e:
                logger.warning(f"Erro ao fazer backup de users: {str(e)}")
                conn.rollback()
        
        # Fechar a conexão atual e criar uma nova para evitar problemas com transações
        cursor.close()
        conn.close()
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Desativar verificação de chaves estrangeiras novamente
        execute_safely(cursor, "SET session_replication_role = 'replica'", commit_conn=conn)
        
        # Remover tabelas existentes
        for table in ['maintenances', 'machines', 'users', 'companies']:
            if table in existing_tables:
                logger.info(f"Removendo tabela {table}...")
                execute_safely(cursor, f"DROP TABLE IF EXISTS {table} CASCADE", commit_conn=conn)
        
        # Verificar se os tipos enum existem
        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'machinetypeenum')")
        machine_enum_exists = cursor.fetchone()[0]
        
        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'userroleenum')")
        user_enum_exists = cursor.fetchone()[0]
        
        # Remover tipos enum existentes
        if user_enum_exists:
            logger.info("Removendo tipo userroleenum...")
            execute_safely(cursor, "DROP TYPE IF EXISTS userroleenum CASCADE", commit_conn=conn)
        
        if machine_enum_exists:
            logger.info("Removendo tipo machinetypeenum...")
            execute_safely(cursor, "DROP TYPE IF EXISTS machinetypeenum CASCADE", commit_conn=conn)
        
        # Criar os tipos enum
        logger.info("Criando tipo machinetypeenum...")
        execute_safely(cursor, "CREATE TYPE machinetypeenum AS ENUM ('truck', 'fixed')", commit_conn=conn)
        
        logger.info("Criando tipo userroleenum...")
        execute_safely(cursor, "CREATE TYPE userroleenum AS ENUM ('admin', 'fleet_manager')", commit_conn=conn)
        
        # Criar as tabelas com a nova estrutura
        logger.info("Criando tabela companies...")
        execute_safely(cursor, """
            CREATE TABLE companies (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL UNIQUE,
                address VARCHAR
            )
        """, commit_conn=conn)
        
        logger.info("Criando tabela users...")
        execute_safely(cursor, """
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR NOT NULL UNIQUE,
                hashed_password VARCHAR NOT NULL,
                email VARCHAR,
                full_name VARCHAR,
                role userroleenum DEFAULT 'fleet_manager',
                company_id INTEGER,
                is_active BOOLEAN DEFAULT TRUE
            )
        """, commit_conn=conn)
        
        logger.info("Criando tabela machines...")
        execute_safely(cursor, """
            CREATE TABLE machines (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                type machinetypeenum NOT NULL,
                company_id INTEGER NOT NULL
            )
        """, commit_conn=conn)
        
        logger.info("Criando tabela maintenances...")
        execute_safely(cursor, """
            CREATE TABLE maintenances (
                id SERIAL PRIMARY KEY,
                machine_id INTEGER NOT NULL,
                type VARCHAR NOT NULL,
                scheduled_date DATE NOT NULL,
                notes VARCHAR,
                completed BOOLEAN DEFAULT FALSE
            )
        """, commit_conn=conn)
        
        # Adicionar as chaves estrangeiras
        logger.info("Adicionando chaves estrangeiras...")
        execute_safely(cursor, """
            ALTER TABLE users
            ADD CONSTRAINT fk_users_company
            FOREIGN KEY (company_id) REFERENCES companies (id)
        """, commit_conn=conn)
        
        execute_safely(cursor, """
            ALTER TABLE machines
            ADD CONSTRAINT fk_machines_company
            FOREIGN KEY (company_id) REFERENCES companies (id)
        """, commit_conn=conn)
        
        execute_safely(cursor, """
            ALTER TABLE maintenances
            ADD CONSTRAINT fk_maintenances_machine
            FOREIGN KEY (machine_id) REFERENCES machines (id)
        """, commit_conn=conn)
        
        # Restaurar os dados de backup
        if companies_data and companies_columns:
            logger.info("Restaurando dados de empresas...")
            for company in companies_data:
                try:
                    company_id_idx = companies_columns.index('id') if 'id' in companies_columns else -1
                    company_name_idx = companies_columns.index('name') if 'name' in companies_columns else -1
                    
                    if company_id_idx >= 0 and company_name_idx >= 0:
                        company_id = company[company_id_idx]
                        company_name = company[company_name_idx]
                        
                        # Verificar se há coluna de endereço nos dados antigos
                        address = None
                        if 'address' in companies_columns:
                            address_idx = companies_columns.index('address')
                            if address_idx < len(company):
                                address = company[address_idx]
                        
                        # Inserir com ID específico para manter referências
                        execute_safely(cursor, """
                            INSERT INTO companies (id, name, address)
                            VALUES (%s, %s, %s)
                        """, (company_id, company_name, address), commit_conn=conn)
                except Exception as e:
                    logger.warning(f"Erro ao restaurar empresa: {str(e)}")
                    conn.rollback()
            
            # Redefinir a sequência do ID
            execute_safely(cursor, """
                SELECT setval('companies_id_seq', COALESCE((SELECT MAX(id) FROM companies), 1))
            """, commit_conn=conn)
        
        if machines_data and machines_columns:
            logger.info("Restaurando dados de máquinas...")
            for machine in machines_data:
                try:
                    machine_id_idx = machines_columns.index('id') if 'id' in machines_columns else -1
                    machine_name_idx = machines_columns.index('name') if 'name' in machines_columns else -1
                    machine_type_idx = machines_columns.index('type') if 'type' in machines_columns else -1
                    company_id_idx = machines_columns.index('company_id') if 'company_id' in machines_columns else -1
                    
                    if all(idx >= 0 for idx in [machine_id_idx, machine_name_idx, machine_type_idx, company_id_idx]):
                        machine_id = machine[machine_id_idx]
                        machine_name = machine[machine_name_idx]
                        machine_type = machine[machine_type_idx]
                        company_id = machine[company_id_idx]
                        
                        # Inserir com ID específico para manter referências
                        execute_safely(cursor, """
                            INSERT INTO machines (id, name, type, company_id)
                            VALUES (%s, %s, %s, %s)
                        """, (machine_id, machine_name, machine_type, company_id), commit_conn=conn)
                except Exception as e:
                    logger.warning(f"Erro ao restaurar máquina: {str(e)}")
                    conn.rollback()
            
            # Redefinir a sequência do ID
            execute_safely(cursor, """
                SELECT setval('machines_id_seq', COALESCE((SELECT MAX(id) FROM machines), 1))
            """, commit_conn=conn)
        
        if maintenances_data and maintenances_columns:
            logger.info("Restaurando dados de manutenções...")
            for maintenance in maintenances_data:
                try:
                    maint_id_idx = maintenances_columns.index('id') if 'id' in maintenances_columns else -1
                    machine_id_idx = maintenances_columns.index('machine_id') if 'machine_id' in maintenances_columns else -1
                    maint_type_idx = maintenances_columns.index('type') if 'type' in maintenances_columns else -1
                    scheduled_date_idx = maintenances_columns.index('scheduled_date') if 'scheduled_date' in maintenances_columns else -1
                    
                    if all(idx >= 0 for idx in [maint_id_idx, machine_id_idx, maint_type_idx, scheduled_date_idx]):
                        maintenance_id = maintenance[maint_id_idx]
                        machine_id = maintenance[machine_id_idx]
                        maint_type = maintenance[maint_type_idx]
                        scheduled_date = maintenance[scheduled_date_idx]
                        
                        # Verificar se há coluna de completed nos dados antigos
                        completed = False
                        if 'completed' in maintenances_columns:
                            completed_idx = maintenances_columns.index('completed')
                            if completed_idx < len(maintenance):
                                completed = maintenance[completed_idx]
                        
                        # Verificar se há coluna de notes nos dados antigos
                        notes = None
                        if 'notes' in maintenances_columns:
                            notes_idx = maintenances_columns.index('notes')
                            if notes_idx < len(maintenance):
                                notes = maintenance[notes_idx]
                        
                        # Inserir com ID específico para manter referências
                        execute_safely(cursor, """
                            INSERT INTO maintenances (id, machine_id, type, scheduled_date, completed, notes)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (maintenance_id, machine_id, maint_type, scheduled_date, completed, notes), commit_conn=conn)
                except Exception as e:
                    logger.warning(f"Erro ao restaurar manutenção: {str(e)}")
                    conn.rollback()
            
            # Redefinir a sequência do ID
            execute_safely(cursor, """
                SELECT setval('maintenances_id_seq', COALESCE((SELECT MAX(id) FROM maintenances), 1))
            """, commit_conn=conn)
            
        # Criar o administrador principal (Filipe Ferreira) se não existir
        logger.info("Criando administrador principal (Filipe Ferreira)...")
            
        # Gerar hash da senha
        hashed_password = pwd_context.hash("filipe.ferreira.1984")
            
        execute_safely(cursor, """
            INSERT INTO users (username, hashed_password, email, full_name, role, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING
        """, (
            "filipe.ferreira",
            hashed_password,
            "filipe.ferreira@fleetpilot.com",
            "Filipe Ferreira",
            "admin",
            True
        ), commit_conn=conn)
        logger.info("Administrador principal criado com sucesso!")
        
        # Restaurar o modo de verificação de chaves estrangeiras
        execute_safely(cursor, "SET session_replication_role = 'origin'", commit_conn=conn)
            
        logger.info("Recriação da base de dados concluída com sucesso!")
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Erro durante a recriação da base de dados: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    recreate_database()