# backend/utils.py
import vonage

def enviar_sms(texto: str, numero_destino: str):
    client = vonage.Client(key="SUA_API_KEY", secret="SEU_API_SECRET")
    sms = vonage.Sms(client)
    responseData = sms.send_message({
        "from": "FrotaApp",
        "to": numero_destino,
        "text": texto,
    })
    # Aqui você pode checar se 'responseData' indica sucesso ou erro
