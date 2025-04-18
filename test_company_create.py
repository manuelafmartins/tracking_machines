"""
Script de diagnóstico para testar a criação de empresas diretamente na API.
Salve este arquivo como test_company_create.py e execute-o.
"""

import requests
import json
import os
from dotenv import load_dotenv

# Carregar as variáveis de ambiente
load_dotenv()
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

def test_company_creation():
    """
    Teste a criação de uma empresa diretamente na API.
    """
    # 1. Obter token de autenticação
    print("=== OBTENDO TOKEN DE ACESSO ===")
    login_data = {
        "username": "filipe.ferreira",
        "password": "filipe.ferreira.1984"
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/login", data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            print("Token obtido com sucesso!")
        else:
            print(f"Erro ao obter token: {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"Erro na requisição de login: {str(e)}")
        return
    
    # 2. Criar empresa com todos os campos
    print("\n=== CRIANDO EMPRESA DE TESTE ===")
    
    company_data = {
        "name": "Empresa Teste Diagnóstico",
        "address": "Rua de Teste, 123",
        "tax_id": "123456789",
        "postal_code": "4000-123",
        "city": "Porto",
        "country": "Portugal",
        "billing_email": "teste@empresa.com",
        "phone": "+351987654321",
        "payment_method": "Transferência Bancária",
        "iban": "PT50000201231234567890154"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Criar empresa
        print("Enviando dados:")
        print(json.dumps(company_data, indent=2))
        
        response = requests.post(f"{API_URL}/companies", headers=headers, json=company_data)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            company = response.json()
            print("Empresa criada com sucesso!")
            print("Dados retornados:")
            print(json.dumps(company, indent=2))
            
            # 3. Verificar se a empresa foi criada corretamente
            print("\n=== VERIFICANDO EMPRESA CRIADA ===")
            company_id = company["id"]
            
            response = requests.get(f"{API_URL}/companies/{company_id}", headers=headers)
            
            if response.status_code == 200:
                fetched_company = response.json()
                print("Dados da empresa obtidos:")
                print(json.dumps(fetched_company, indent=2))
                
                # Verificar se todos os campos foram salvos
                missing_fields = []
                for field, value in company_data.items():
                    if fetched_company.get(field) != value:
                        missing_fields.append(f"{field}: enviado '{value}', recebido '{fetched_company.get(field)}'")
                
                if missing_fields:
                    print("\nCampos com problemas:")
                    for field in missing_fields:
                        print(f" - {field}")
                else:
                    print("\nTodos os campos foram salvos corretamente!")
            else:
                print(f"Erro ao obter empresa: {response.status_code}")
                print(response.text)
        else:
            print("Erro ao criar empresa:")
            print(response.text)
    except Exception as e:
        print(f"Erro durante o teste: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_company_creation()