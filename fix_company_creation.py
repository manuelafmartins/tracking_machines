"""
Script para modificar diretamente o arquivo crud.py
Salve como fix_company_creation.py e execute-o.
"""

import os
import re

def fix_crud_file():
    """Modifica diretamente o arquivo crud.py com a correção necessária."""
    
    # Caminho para o arquivo crud.py
    crud_file_path = os.path.join("backend", "app", "crud.py")
    
    # Verificar se o arquivo existe
    if not os.path.exists(crud_file_path):
        print(f"Erro: Arquivo {crud_file_path} não encontrado!")
        return False
    
    # Ler o conteúdo atual do arquivo
    with open(crud_file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    # Código antigo a ser substituído (regex para ser mais flexível)
    old_code_pattern = r"def create_company\(db: Session, company: schemas\.CompanyCreate\).*?return db_company"
    
    # Novo código corrigido
    new_code = """def create_company(db: Session, company: schemas.CompanyCreate) -> models.Company:
    # Extrair explicitamente todos os campos do objeto Pydantic
    company_dict = company.model_dump()
    
    # Criar o objeto Company com atribuições explícitas
    db_company = models.Company(
        name=company_dict.get("name"),
        address=company_dict.get("address"),
        tax_id=company_dict.get("tax_id"),
        postal_code=company_dict.get("postal_code"),
        city=company_dict.get("city"),
        country=company_dict.get("country"),
        billing_email=company_dict.get("billing_email"),
        phone=company_dict.get("phone"),
        payment_method=company_dict.get("payment_method"),
        iban=company_dict.get("iban"),
        logo_path=company_dict.get("logo_path")
    )
    
    # Adicionar à sessão
    db.add(db_company)
    _commit_refresh(db, db_company)
    return db_company"""
    
    # Substituir o código usando regex com flag DOTALL para capturar múltiplas linhas
    new_content = re.sub(old_code_pattern, new_code, content, flags=re.DOTALL)
    
    # Verificar se a substituição ocorreu
    if new_content == content:
        print("Aviso: Nenhuma alteração foi feita! O padrão não foi encontrado.")
        
        # Alternativa manual: localizar a função e substituir
        print("Tentando método alternativo...")
        
        # Procurar pela função manualmente
        function_start = content.find("def create_company(")
        if function_start == -1:
            print("Erro: Função create_company não encontrada no arquivo!")
            return False
        
        # Localizar onde a função termina (próxima definição de função)
        next_function = content.find("def ", function_start + 1)
        if next_function == -1:
            next_function = len(content)
        
        # Substituir a função inteira
        new_content = content[:function_start] + new_code + content[next_function:]
        print("Substituição manual realizada.")
    
    # Criar backup do arquivo original
    backup_path = crud_file_path + ".backup"
    with open(backup_path, "w", encoding="utf-8") as file:
        file.write(content)
    print(f"Backup do arquivo original criado em {backup_path}")
    
    # Escrever o novo conteúdo
    with open(crud_file_path, "w", encoding="utf-8") as file:
        file.write(new_content)
    
    print(f"Arquivo {crud_file_path} modificado com sucesso!")
    print("\nFunção create_company corrigida. Reinicie o backend para aplicar as alterações.")
    return True

if __name__ == "__main__":
    print("Iniciando correção do problema de criação de empresas...")
    fix_crud_file()