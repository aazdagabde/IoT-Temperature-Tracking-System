from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings

from .models import Dht11, Incident, Profile, Acknowledgment, GlobalAlertSettings
from .alerts import send_telegram_alert, send_whatsapp_alert, send_email_alert
from django.shortcuts import render
from rest_framework.decorators import api_view



from django.shortcuts import render, redirect
from django.contrib import messages
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from .models import Dht11


@api_view(['GET', 'POST'])
def Dlist(request):
    if request.method == 'GET':
        # Afficher une interface utilisateur simple avec les dernières mesures
        latest_measures = Dht11.objects.all().order_by('-dt')[:10]  # 10 dernières mesures
        return render(request, 'api_post.html', {'latest_measures': latest_measures})

    elif request.method == 'POST':
        # Traiter les données POST (API ou formulaire)
        if request.content_type == 'application/json':
            # Requête API JSON
            temp = request.data.get('temp')
            hum = request.data.get('hum')
        else:
            # Requête formulaire HTML
            temp = request.POST.get('temp')
            hum = request.POST.get('hum')

        if temp is not None and hum is not None:
            # Enregistrer la nouvelle mesure
            Dht11.objects.create(temp=temp, hum=hum)

            # Ajouter un message de succès
            messages.success(request, "La mesure a été enregistrée avec succès.")
            check_temperature_and_manage_incident(float(temp))
            return redirect('api_post')  # Rediriger vers la même page
        else:
            # Ajouter un message d'erreur
            messages.error(request, "Erreur : Les champs 'température' et 'humidité' sont obligatoires.")
            return redirect('api_post')  # Rediriger vers la même page


def check_temperature_and_manage_incident(current_temp):
    """
    - current_temp : float, la température reçue
    - Gère la création/fermeture d’incident + escalade en fonction
      de la température et de l’état actuel (incident ouvert ou non).
    """
    open_incident = Incident.objects.filter(end_dt__isnull=True).order_by('-start_dt').first()
    settings = GlobalAlertSettings.objects.first()

    if not settings:
        print("[WARN] Aucun paramètre global trouvé.")
        return

    min_temp = settings.min_temperature
    max_temp = settings.max_temperature

    # Vérifier si la température est hors-limites
    if (
            (min_temp is not None and current_temp < min_temp) or
            (max_temp is not None and current_temp > max_temp)
    ):
        # Température hors-norme => Ouvrir un incident si pas déjà ouvert
        if not open_incident:
            new_incident = Incident.objects.create(
                start_dt=timezone.now(),
                iteration=1
            )
            print(f"[INFO] Nouvel incident créé (ID={new_incident.id}). Itération=1")

            # Alerter la première vague (itération=1)
            users_to_alert = get_users_to_alert(new_incident)
            send_custom_alerts(new_incident, users_to_alert)

        else:
            # Incident en cours => on incrémente l'itération
            open_incident.iteration += 1
            open_incident.save()
            print(f"[INFO] Incident en cours (ID={open_incident.id}) -> Itération={open_incident.iteration}")

            users_to_alert = get_users_to_alert(open_incident)
            if users_to_alert:
                send_custom_alerts(open_incident, users_to_alert)
            else:
                print("[INFO] Aucune alerte à envoyer pour cette itération (soit déjà acquitté, "
                      "soit pas de nouvel utilisateur).")

    else:
        # Température dans la norme => fermer l'incident si besoin
        if open_incident:
            open_incident.end_dt = timezone.now()
            open_incident.save()
            print("[INFO] Incident fermé (température redevenue normale).")
        else:
            print("[INFO] Aucun incident en cours, température normale.")


def get_users_to_alert(incident):
    """
    Retourne la liste des utilisateurs à alerter en fonction de l'itération.
    - iteration=1 -> on alerte l'index 0 (user1) s'il n'a pas acquitté
    - iteration=2 -> on alerte l'index 0 (user1) + index 1 (user2), etc.
    - iteration=3 -> user1, user2, user3 (s'ils n'ont pas acquitté)
    - iteration=4 -> admin
    """
    iteration = incident.iteration
    escalation_order = ['user1', 'user2', 'user3', 'admin']  # Ordre d'escalade
    users_to_alert = []

    for i in range(iteration):
        if i < len(escalation_order):
            username = escalation_order[i]
            user = get_user_by_username(username)
            if user:
                # Vérifier s'il a déjà acquitté
                already_ack = Acknowledgment.objects.filter(incident=incident, user=user).exists()
                if not already_ack:
                    users_to_alert.append(user)
            else:
                print(f"[WARN] L'utilisateur {username} n'existe pas.")

    return users_to_alert


def send_custom_alerts(incident, users):
    """
    Envoie des alertes personnalisées aux utilisateurs spécifiés,
    en ajoutant systématiquement le suffixe :
    "(Incident #{incident.id}, itération {incident.iteration}, utilisateur: {user.username})"
    """
    alert_settings = GlobalAlertSettings.objects.first()

    # Message de base personnalisé OU message par défaut
    base_message = (
        alert_settings.alert_message
        if (alert_settings and alert_settings.alert_message)
        else "Alerte: température élevée, veuillez intervenir immédiatement pour vérifier "
             "et corriger cette situation"
    )

    for user in users:
        # On concatène ici le complément demandant d'afficher l'Incident, l'itération, et le user
        full_message = (
            f"{base_message} "
            f"(Incident #{incident.id}, itération {incident.iteration}, utilisateur: {user.username})"
        )

        notify_user(user, full_message)


def notify_user(user, message: str):
    """
    Envoie l'alerte (Telegram, WhatsApp, e-mail) si l'utilisateur a un Profile configuré.
    """
    if not user:
        return

    profile = getattr(user, 'profile', None)
    if not profile:
        print(f"[WARN] L'utilisateur {user.username} n'a pas de profil configuré.")
        return

    alert_settings = GlobalAlertSettings.objects.first()
    telegram_bot_token = alert_settings.telegram_token if alert_settings else None

    # Debug
    print(f"[DEBUG] Envoi d'alerte à {user.username} => telegram_bot_token={telegram_bot_token}, "
          f"profile.telegram_id={profile.telegram_id}")

    # Telegram
    if profile.telegram_id and telegram_bot_token:
        try:
            send_telegram_alert(telegram_bot_token, profile.telegram_id, message)
        except Exception as e:
            print(f"[ERROR] Erreur lors de l'envoi de l'alerte Telegram à {user.username}: {e}")
    else:
        if not profile.telegram_id:
            print(f"[INFO] Pas de telegram_id pour l'utilisateur {user.username}")
        if not telegram_bot_token:
            print("[INFO] Pas de token Telegram configuré dans GlobalAlertSettings")

    # WhatsApp (exemple, à décommenter si nécessaire)

    if (
        profile.twilio_account_sid and
        profile.twilio_auth_token and
        profile.whatsapp_number
    ):
        try:
            send_whatsapp_alert(
                account_sid=profile.twilio_account_sid,
                auth_token=profile.twilio_auth_token,
                from_whatsapp='whatsapp:+14155238886',  # Numéro WhatsApp Sandbox Twilio
                to_whatsapp=f'whatsapp:{profile.whatsapp_number}',
                message=message
            )
        except Exception as e:
            print(f"[ERROR] Erreur lors de l'envoi de l'alerte WhatsApp à {user.username}: {e}")


    # E-mail
    if user.email:
        try:
            send_email_alert(
                subject="Alerte Température Élevée",
                body=message,
                recipients=[user.email]
            )
        except Exception as e:
            print(f"[ERROR] Erreur lors de l'envoi de l'alerte e-mail à {user.username}: {e}")


def get_user_by_username(username):
    """
    Récupère un User Django par son username, ou None s'il n'existe pas.
    """
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return None
