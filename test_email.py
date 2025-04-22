# test_email.py
import os
import traceback
import logging
from dotenv import load_dotenv

# Configurar logging para mostrar mais detalhes
logging.basicConfig(level=logging.DEBUG)

load_dotenv()

def test_email():
    try:
        # Garanta que estamos importando do módulo correto
        from backend.app.email_service import send_email
        
        # Verifique as credenciais
        email_host = os.getenv("EMAIL_HOST")
        email_port = os.getenv("EMAIL_PORT")
        email_username = os.getenv("EMAIL_USERNAME")
        email_password = os.getenv("EMAIL_PASSWORD")
        
        print(f"Configurações:")
        print(f"Host: {email_host}")
        print(f"Porta: {email_port}")
        print(f"Usuário: {email_username}")
        print(f"Senha: {'*' * (len(email_password) if email_password else 0)}")
        
        recipient = "manuel.martins.maths@gmail.com"
        subject = "Teste do Sistema FleetPilot"
        html_content = """
        <html>
            <body>
                <h1>Teste de Email</h1>
                <p>Este é um teste do sistema de emails do FleetPilot.</p>
                <p>Se você está vendo esta mensagem, o sistema está funcionando corretamente!</p>
            </body>
        </html>
        """
        
        print("Tentando enviar email...")
        result = send_email(recipient, subject, html_content)
        if result:
            print("Email enviado com sucesso!")
        else:
            print("Falha ao enviar email.")
            
    except ImportError as e:
        print(f"Erro de importação: {e}")
        print("Verifique se o módulo email_service existe e está no caminho correto.")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        print("Traceback detalhado:")
        traceback.print_exc()

if __name__ == "__main__":
    test_email()