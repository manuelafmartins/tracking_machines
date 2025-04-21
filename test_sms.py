# Salve como test_sms.py na raiz do projeto
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Vonage API credentials
VONAGE_API_KEY = os.getenv("VONAGE_API_KEY")
VONAGE_API_SECRET = os.getenv("VONAGE_API_SECRET")

def test_sms(phone_number: str, text: str):
    """
    Test sending SMS using Vonage API
    """
    if not VONAGE_API_KEY or not VONAGE_API_SECRET:
        logger.error("Vonage API credentials not found in environment variables")
        return False
    
    logger.info(f"Using Vonage credentials - API Key: {VONAGE_API_KEY}")
    
    try:
        # Importação em tempo de execução para verificar a versão
        import vonage
        logger.info(f"Vonage library version: {vonage.__version__}")
        
        # Verificar qual é o método correto para a versão atual
        if hasattr(vonage, 'Client'):
            # Para versões mais novas
            client = vonage.Client(key=VONAGE_API_KEY, secret=VONAGE_API_SECRET)
            sms = vonage.Sms(client)
        else:
            # Para versões mais antigas (2.x e abaixo)
            client = vonage.nexmo.Client(key=VONAGE_API_KEY, secret=VONAGE_API_SECRET)
            sms = client.sms
        
        logger.info(f"Attempting to send SMS to {phone_number}")
        response_data = sms.send_message({
            "from": "FleetPilot",
            "to": phone_number,
            "text": text,
        })
        
        logger.info(f"Vonage API response: {response_data}")
        
        if response_data["messages"][0]["status"] == "0":
            logger.info(f"SMS sent successfully to {phone_number}")
            return True
        else:
            logger.error(f"Error sending SMS: {response_data['messages'][0]['error-text']}")
            return False
    except Exception as e:
        logger.error(f"Exception while sending SMS: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Substitua com um número de telefone válido
    test_phone = input("Enter phone number with country code (e.g., +351912345678): ")
    test_sms(test_phone, "Este é um teste do sistema de notificações do FleetPilot")