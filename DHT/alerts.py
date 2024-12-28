# DHT/alerts.py

import logging
from twilio.rest import Client
from django.core.mail import send_mail
from django.conf import settings
import telepot

logger = logging.getLogger('DHT')


def send_telegram_alert(bot_token, chat_id, message):
    """
    Envoie un message Telegram via un bot.

    Args:
        bot_token (str): Le token du bot Telegram.
        chat_id (int): L'ID du chat où envoyer le message.
        message (str): Le contenu du message à envoyer.
    """
    if not bot_token or not chat_id:
        logger.warning("send_telegram_alert: Token ou chat_id manquant.")
        return
    try:
        bot = telepot.Bot(bot_token)
        bot.sendMessage(chat_id, message)
        logger.info("Alerte Telegram envoyée.")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'alerte Telegram : {e}")


def send_whatsapp_alert(account_sid, auth_token, from_whatsapp, to_whatsapp, message):
    """
    Envoie un message WhatsApp via Twilio.

    Args:
        account_sid (str): SID du compte Twilio.
        auth_token (str): Auth Token du compte Twilio.
        from_whatsapp (str): Numéro WhatsApp de l'expéditeur (fournit par Twilio).
        to_whatsapp (str): Numéro WhatsApp du destinataire.
        message (str): Le contenu du message à envoyer.
    """
    if not account_sid or not auth_token or not to_whatsapp:
        logger.warning("send_whatsapp_alert: Identifiants manquants.")
        return
    try:
        client = Client(account_sid, auth_token)
        client.messages.create(
            body=message,
            from_=from_whatsapp,
            to=to_whatsapp
        )
        logger.info("Alerte WhatsApp envoyée.")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'alerte WhatsApp : {e}")


def send_email_alert(subject, body, recipients):
    """
    Envoie un e-mail avec le sujet et le corps spécifiés aux destinataires.

    Args:
        subject (str): Sujet de l'e-mail.
        body (str): Corps de l'e-mail.
        recipients (list): Liste d'adresses e-mail des destinataires.
    """
    if not recipients:
        logger.warning("send_email_alert: Aucun destinataire spécifié.")
        return
    from_email = settings.EMAIL_HOST_USER
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=recipients,
            fail_silently=False,
        )
        logger.info("Alerte e-mail envoyée avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'alerte e-mail : {e}")
