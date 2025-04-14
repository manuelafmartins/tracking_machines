import psycopg2
from psycopg2 import OperationalError

# Substitui estes valores pelos teus dados do Supabase
DB_NAME = "postgres"
DB_USER = "postgres.jaauqmyojraoqlklwnfv"
DB_PASSWORD = "Mafmafm563895."
DB_HOST = "aws-0-eu-west-3.pooler.supabase.com"
DB_PORT = "6543"

def create_connection():
    try:
        connection = psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode='require' 
        )
        print("Conexão estabelecida com sucesso ao Supabase!")
        return connection
    except OperationalError as e:
        print(f"Ocorreu um erro ao conectar: {e}")
        return None

def test_query(connection):
    try:
        print(connection)
        cursor = connection.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        print(f"Query executada com sucesso! Resultado: {result}")
        cursor.close()
    except Exception as e:
        print(f"Erro ao executar a query: {e}")

if __name__ == "__main__":
    conn = create_connection()
    if conn:
        test_query(conn)
        conn.close()
