from apscheduler.schedulers.background import BackgroundScheduler
from .database import SessionLocal
from .crud import listar_manutencoes_pendentes
from .utils import enviar_sms

def verificar_manutencoes():
    db = SessionLocal()
    manutencoes = listar_manutencoes_pendentes(db)
    for m in manutencoes:
        enviar_sms(f"⚠️ Manutenção {m.tipo} agendada para a máquina {m.maquina.nome} em {m.data_prevista}")
    db.close()

def iniciar_agendador():
    scheduler = BackgroundScheduler()
    scheduler.add_job(verificar_manutencoes, "interval", hours=24)
    scheduler.start()
