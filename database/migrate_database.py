# migrate_database.py
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

def execute_query(cursor, query, params=None):
    """Executa uma query e faz log do resultado"""
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return True
    except Exception as e:
        logger.error(f"Erro ao executar query: {str(e)}")
        logger.error(f"Query: {query}")
        if params:
            logger.error(f"Parâmetros: {params}")
        return False

def column_exists(cursor, table, column):
    """Verifica se uma coluna existe em uma tabela"""
    query = """
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        )
    """
    cursor.execute(query, (table, column))
    return cursor.fetchone()[0]

def migrate_database():
    """
    Migra a base de dados para a nova estrutura
    """
    logger.info("Iniciando migração da base de dados...")
    
    try:
        # Conectar à base de dados
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Verificar se o tipo UserRoleEnum já existe
        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'userroleenum')")
        enum_exists = cursor.fetchone()[0]
        
        if not enum_exists:
            logger.info("Criando tipo UserRoleEnum...")
            execute_query(cursor, "CREATE TYPE userroleenum AS ENUM ('admin', 'fleet_manager')")
        
        # Atualizar a tabela de usuários
        logger.info("Alterando tabela de usuários...")
        
        # Adicionar coluna email se não existir
        if not column_exists(cursor, 'users', 'email'):
            logger.info("Adicionando coluna 'email'...")
            execute_query(cursor, "ALTER TABLE users ADD COLUMN email VARCHAR")
            
        # Verificar novamente se a coluna email foi criada
        if not column_exists(cursor, 'users', 'email'):
            raise Exception("Falha ao criar coluna 'email' na tabela 'users'")
        
        # Adicionar coluna full_name se não existir
        if not column_exists(cursor, 'users', 'full_name'):
            logger.info("Adicionando coluna 'full_name'...")
            execute_query(cursor, "ALTER TABLE users ADD COLUMN full_name VARCHAR")
        
        # Adicionar coluna role se não existir
        if not column_exists(cursor, 'users', 'role'):
            logger.info("Adicionando coluna 'role'...")
            execute_query(cursor, "ALTER TABLE users ADD COLUMN role userroleenum DEFAULT 'admin'")
            
            # Converter coluna is_admin para role se existir
            if column_exists(cursor, 'users', 'is_admin'):
                logger.info("Convertendo coluna 'is_admin' para 'role'...")
                execute_query(cursor, """
                    UPDATE users 
                    SET role = CASE WHEN is_admin THEN 'admin'::userroleenum ELSE 'fleet_manager'::userroleenum END
                """)
        
        # Adicionar coluna is_active se não existir
        if not column_exists(cursor, 'users', 'is_active'):
            logger.info("Adicionando coluna 'is_active'...")
            execute_query(cursor, "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
        
        # Adicionar coluna company_id se não existir
        if not column_exists(cursor, 'users', 'company_id'):
            logger.info("Adicionando coluna 'company_id'...")
            execute_query(cursor, """
                ALTER TABLE users 
                ADD COLUMN company_id INTEGER,
                ADD CONSTRAINT fk_users_company
                FOREIGN KEY (company_id) REFERENCES companies (id)
            """)
            
        # Adicionar coluna address a companies se não existir
        if not column_exists(cursor, 'companies', 'address'):
            logger.info("Adicionando coluna 'address' à tabela 'companies'...")
            execute_query(cursor, "ALTER TABLE companies ADD COLUMN address VARCHAR")
        
        # Adicionar coluna notes a maintenances se não existir
        if not column_exists(cursor, 'maintenances', 'notes'):
            logger.info("Adicionando coluna 'notes' à tabela 'maintenances'...")
            execute_query(cursor, "ALTER TABLE maintenances ADD COLUMN notes VARCHAR")
        
        # Commit das alterações
        conn.commit()
        logger.info("Migração de estrutura concluída com sucesso!")
        
        # Criar administrador principal se não existir
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'filipe.ferreira'")
        if cursor.fetchone()[0] == 0:
            logger.info("Criando administrador principal (Filipe Ferreira)...")
            
            # Gerar hash da senha
            hashed_password = pwd_context.hash("Mafmafm563895")
            
            # Verificar quais colunas existem na tabela users para construir a query corretamente
            columns = []
            values = []
            params = []
            
            columns.append("username")
            values.append("%s")
            params.append("filipe.ferreira")
            
            columns.append("hashed_password")
            values.append("%s")
            params.append(hashed_password)
            
            if column_exists(cursor, 'users', 'email'):
                columns.append("email")
                values.append("%s")
                params.append("filipe.ferreira@fleetpilot.com")
            
            if column_exists(cursor, 'users', 'full_name'):
                columns.append("full_name")
                values.append("%s")
                params.append("Filipe Ferreira")
            
            if column_exists(cursor, 'users', 'role'):
                columns.append("role")
                values.append("%s")
                params.append("admin")
            elif column_exists(cursor, 'users', 'is_admin'):
                columns.append("is_admin")
                values.append("%s")
                params.append(True)
            
            if column_exists(cursor, 'users', 'is_active'):
                columns.append("is_active")
                values.append("%s")
                params.append(True)
            
            # Construir e executar a query de inserção
            columns_str = ", ".join(columns)
            values_str = ", ".join(values)
            query = f"INSERT INTO users ({columns_str}) VALUES ({values_str})"
            
            logger.info(f"Executando query de inserção: {query}")
            logger.info(f"Com parâmetros: {params}")
            
            if execute_query(cursor, query, params):
                conn.commit()
                logger.info("Administrador principal criado com sucesso!")
            else:
                logger.error("Falha ao criar administrador principal")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro durante a migração: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate_database()