import vonage

def enviar_sms(mensagem):
    client = vonage.Client(key="API_KEY", secret="API_SECRET")
    sms = vonage.Sms(client)
    sms.send_message({"from": "FrotaApp", "to": "351911234567", "text": mensagem})
