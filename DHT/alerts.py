import telepot
from twilio.rest import Client
from django.core.mail import send_mail
from django.conf import settings

def send_telegram_alert(bot_token, chat_id, message):
    """
    bot_token : ex. '6662023260:AA...'
    chat_id   : ex. 123456789
    """
    if not bot_token or not chat_id:
        print("[send_telegram_alert] Token ou chat_id manquant.")
        return
    bot = telepot.Bot(bot_token)
    bot.sendMessage(chat_id, message)
    print("[Telegram] Alerte envoyée.")

def send_whatsapp_alert(account_sid, auth_token, from_whatsapp, to_whatsapp, message):
    """
    from_whatsapp : 'whatsapp:+14155238886' (Twilio sandbox)
    to_whatsapp   : 'whatsapp:+212600000000'
    """
    if not account_sid or not auth_token or not to_whatsapp:
        print("[send_whatsapp_alert] Identifiants manquants.")
        return
    client = Client(account_sid, auth_token)
    client.messages.create(
        body=message,
        from_=from_whatsapp,
        to=to_whatsapp
    )
    print("[WhatsApp] Alerte envoyée.")

def send_email_alert(subject, body, recipients):
    if not recipients:
        return
    from_email = settings.EMAIL_HOST_USER
    send_mail(subject, body, from_email, recipients)
    print("[E-mail] Alerte envoyée.")
