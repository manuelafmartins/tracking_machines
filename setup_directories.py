import os

def create_directory_structure():
    """Cria a estrutura de diretórios necessária para o projeto."""
    # Diretório para os logos das empresas
    os.makedirs("frontend/images/company_logos", exist_ok=True)
    print("Estrutura de diretórios criada com sucesso!")

if __name__ == "__main__":
    create_directory_structure()