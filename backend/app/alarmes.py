# backend/app/alarmes.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from .database import SessionLocal
from .crud import listar_manutencoes_pendentes
from .utils import enviar_sms
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verificar_manutencoes():
    """
    Verifica manutenções pendentes e envia alertas SMS
    """
    logger.info(f"Executando verificação de manutenções em {datetime.now()}")
    
    db = SessionLocal()
    try:
        manutencoes = listar_manutencoes_pendentes(db)
        logger.info(f"Encontradas {len(manutencoes)} manutenções pendentes")
        
        for m in manutencoes:
            dias_restantes = (m.data_prevista - datetime.now().date()).days
            
            # Formatar a mensagem baseada na urgência
            if dias_restantes <= 2:
                prefixo = "URGENTE! "
            else:
                prefixo = "Aviso: "
                
            msg = f"{prefixo}Manutenção '{m.tipo}' para máquina '{m.maquina.nome}' " \
                  f"da empresa '{m.maquina.empresa.nome}' agendada para {m.data_prevista}."
            
            # Números de telefone poderiam vir de um cadastro da empresa
            numeros_contato = ["351911234567"]  # Em produção, buscar da base de dados
            
            # Enviar para cada número
            for numero in numeros_contato:
                try:
                    enviar_sms(msg, numero)
                    logger.info(f"SMS enviado para {numero}")
                except Exception as e:
                    logger.error(f"Erro ao enviar SMS: {str(e)}")
    
    finally:
        db.close()

def iniciar_agendador():
    """
    Inicia o agendador de tarefas para verificação periódica de manutenções
    """
    scheduler = BackgroundScheduler()
    
    # Verificar manutenções diariamente às 8:00
    scheduler.add_job(
        verificar_manutencoes, 
        'cron', 
        hour=8, 
        minute=0,
        id='verificacao_manutencoes'
    )
    
    # Para desenvolvimento, também podemos adicionar uma verificação por intervalo
    scheduler.add_job(
        verificar_manutencoes, 
        'interval', 
        hours=24,
        id='verificacao_diaria'
    )
    
    scheduler.start()
    logger.info("Agendador de manutenções iniciado!")