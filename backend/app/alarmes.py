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
    Verifica manuten��es pendentes e envia alertas SMS
    """
    logger.info(f"Executando verifica��o de manuten��es em {datetime.now()}")
    
    db = SessionLocal()
    try:
        manutencoes = listar_manutencoes_pendentes(db)
        logger.info(f"Encontradas {len(manutencoes)} manuten��es pendentes")
        
        for m in manutencoes:
            dias_restantes = (m.data_prevista - datetime.now().date()).days
            
            # Formatar a mensagem baseada na urg�ncia
            if dias_restantes <= 2:
                prefixo = "URGENTE! "
            else:
                prefixo = "Aviso: "
                
            msg = f"{prefixo}Manuten��o '{m.tipo}' para m�quina '{m.maquina.nome}' " \
                  f"da empresa '{m.maquina.empresa.nome}' agendada para {m.data_prevista}."
            
            # N�meros de telefone poderiam vir de um cadastro da empresa
            numeros_contato = ["351911234567"]  # Em produ��o, buscar da base de dados
            
            # Enviar para cada n�mero
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
    Inicia o agendador de tarefas para verifica��o peri�dica de manuten��es
    """
    scheduler = BackgroundScheduler()
    
    # Verificar manuten��es diariamente �s 8:00
    scheduler.add_job(
        verificar_manutencoes, 
        'cron', 
        hour=8, 
        minute=0,
        id='verificacao_manutencoes'
    )
    
    # Para desenvolvimento, tamb�m podemos adicionar uma verifica��o por intervalo
    scheduler.add_job(
        verificar_manutencoes, 
        'interval', 
        hours=24,
        id='verificacao_diaria'
    )
    
    scheduler.start()
    logger.info("Agendador de manuten��es iniciado!")