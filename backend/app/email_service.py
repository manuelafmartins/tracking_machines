# backend/app/email_service.py
import os
import logging
import traceback
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações de email
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@fleetpilot.com")

def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Enviar email usando smtplib (biblioteca padrão).
    
    Args:
        to_email: Endereço de email do destinatário
        subject: Assunto do email
        html_content: Conteúdo HTML do email
        
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        logger.warning("Credenciais de email não encontradas nas variáveis de ambiente")
        return False
    
    try:
        # Criar mensagem
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = to_email
        
        # Anexar o conteúdo HTML
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)
        
        # Conectar ao servidor SMTP
        logger.info(f"Conectando ao servidor SMTP: {EMAIL_HOST}:{EMAIL_PORT}")
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        # Login
        logger.info(f"Fazendo login com usuário: {EMAIL_USERNAME}")
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        
        # Enviar email
        logger.info(f"Enviando email para: {to_email}")
        server.sendmail(EMAIL_FROM, to_email, msg.as_string())
        server.quit()
        
        logger.info(f"Email enviado com sucesso para {to_email}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar email: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def send_company_creation_email(company_name: str, admin_email: str) -> bool:
    """
    Enviar email de notificação sobre criação de nova empresa.
    
    Args:
        company_name: Nome da empresa criada
        admin_email: Email do administrador
        
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    subject = f"Nova Empresa Criada: {company_name}"
    html_content = f"""
    <html>
        <body>
            <h1>Nova Empresa Criada no FleetPilot</h1>
            <p>Olá Administrador,</p>
            <p>A empresa <strong>{company_name}</strong> foi adicionada ao sistema FleetPilot.</p>
            <p>Acesse o sistema para configurar permissões e usuários.</p>
            <p>Atenciosamente,<br>Equipe FleetPilot</p>
        </body>
    </html>
    """
    
    return send_email(admin_email, subject, html_content)