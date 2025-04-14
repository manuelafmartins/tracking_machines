# backend/alarmes.py
from apscheduler.schedulers.background import BackgroundScheduler
from .database import SessionLocal
from .crud import listar_manutencoes_pendentes
from .utils import enviar_sms

def verificar_manutencoes():
    db = SessionLocal()
    manutencoes = listar_manutencoes_pendentes(db)
    for m in manutencoes:
        msg = f"Atenção! Manutenção '{m.tipo}' para a máquina '{m.maquina.nome}', " \
              f"da empresa '{m.maquina.empresa.nome}', está pendente."
        enviar_sms(msg, "351911234567")  # Exemplo de número
    db.close()

def iniciar_agendador():
    scheduler = BackgroundScheduler()
    # A cada 24 horas, executa a função
    scheduler.add_job(verificar_manutencoes, "interval", hours=24)
    scheduler.start()
