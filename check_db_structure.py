"""
Script para verificar a estrutura da tabela companies diretamente no banco de dados.
Salve como check_db_structure.py e execute-o.
"""

import os
import psycopg2
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Conexão com o banco de dados
DATABASE_URL = os.getenv("DATABASE_URL")

def check_companies_table():
    """Verifica a estrutura da tabela companies no banco de dados."""
    
    print("=== VERIFICANDO ESTRUTURA DA TABELA COMPANIES ===")
    
    try:
        # Conectar ao banco de dados
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Consultar informações sobre as colunas
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'companies' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        print("\nEstrutura da tabela companies:")
        print("=" * 60)
        print(f"{'COLUNA':<20} {'TIPO':<15} {'NULLABLE':<10}")
        print("-" * 60)
        
        for column in columns:
            name, data_type, nullable = column
            print(f"{name:<20} {data_type:<15} {nullable:<10}")
        
        print("=" * 60)
        
        # Verificar se as colunas esperadas existem
        expected_columns = [
            "id", "name", "address", "logo_path", "tax_id", "postal_code", 
            "city", "country", "billing_email", "phone", "payment_method", "iban"
        ]
        
        column_names = [col[0] for col in columns]
        missing_columns = [col for col in expected_columns if col not in column_names]
        
        if missing_columns:
            print("\nColunas faltantes:")
            for col in missing_columns:
                print(f" - {col}")
        else:
            print("\nTodas as colunas esperadas existem na tabela.")
        
        # Verificar os registros existentes
        cursor.execute("""
            SELECT id, name, address, logo_path, tax_id, postal_code, city, 
                   country, billing_email, phone, payment_method, iban 
            FROM companies 
            LIMIT 5
        """)
        
        rows = cursor.fetchall()
        
        if rows:
            print("\nExemplos de registros:")
            print("=" * 100)
            for row in rows:
                print(f"ID: {row[0]}")
                print(f"Nome: {row[1]}")
                print(f"Morada: {row[2]}")
                print(f"Logo: {row[3]}")
                print(f"NIF: {row[4]}")
                print(f"Código Postal: {row[5]}")
                print(f"Cidade: {row[6]}")
                print(f"País: {row[7]}")
                print(f"Email: {row[8]}")
                print(f"Telefone: {row[9]}")
                print(f"Método Pagamento: {row[10]}")
                print(f"IBAN: {row[11]}")
                print("-" * 100)
        else:
            print("\nNenhum registro encontrado na tabela.")
            
    except Exception as e:
        print(f"Erro ao verificar a estrutura da tabela: {str(e)}")
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    check_companies_table()