import telepot
from django.shortcuts import render, redirect,get_object_or_404

from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from datetime import timedelta
import csv
from .models import Dht11

def home(request):
    return render(request, 'home.html')

#@login_required
#def table(request):
#    data = Dht11.objects.all().order_by('-dt')
#    return render(request, 'table.html', {'data': data})

@login_required
def download_csv(request):
    model_values = Dht11.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="dht.csv"'
    writer = csv.writer(response)
    writer.writerow(['id', 'temp', 'hum', 'dt'])
    for row in model_values.values_list('id', 'temp', 'hum', 'dt'):
        writer.writerow(row)
    return response

@login_required
def value_view(request):
    derniere_ligne = Dht11.objects.last()
    if derniere_ligne:
        derniere_date = derniere_ligne.dt
        delta_temps = timezone.now() - derniere_date
        difference_minutes = delta_temps.total_seconds() // 60
        if difference_minutes < 60:
            temps_ecoule = f'il y a {int(difference_minutes)} min'
        else:
            heures = int(difference_minutes // 60)
            minutes = int(difference_minutes % 60)
            temps_ecoule = f'il y a {heures}h {minutes}min'
        valeurs = {
            'date': temps_ecoule,
            'id': derniere_ligne.id,
            'temp': derniere_ligne.temp,
            'hum': derniere_ligne.hum
        }
    else:
        valeurs = {
            'date': 'Aucune donnée disponible',
            'id': '-',
            'temp': '-',
            'hum': '-'
        }

    return render(request, 'value.html', {'valeurs': valeurs})

@login_required
def graphiqueTemp(request):
    return render(request, 'ChartTemp.html')

@login_required
def graphiqueHum(request):
    return render(request, 'ChartHum.html')

@login_required
def chart_data(request):
    dht = Dht11.objects.all().order_by('dt')
    data = {
        'temps': [record.dt for record in dht],
        'temperature': [record.temp for record in dht],
        'humidity': [record.hum for record in dht]
    }
    return JsonResponse(data)

@login_required
def chart_data_jour(request):
    now = timezone.now()
    last_24_hours = now - timedelta(hours=24)
    dht = Dht11.objects.filter(dt__range=(last_24_hours, now)).order_by('dt')
    data = {
        'temps': [record.dt for record in dht],
        'temperature': [record.temp for record in dht],
        'humidity': [record.hum for record in dht]
    }
    return JsonResponse(data)

@login_required
def chart_data_semaine(request):
    date_debut_semaine = timezone.now().date() - timedelta(days=7)
    dht = Dht11.objects.filter(dt__gte=date_debut_semaine).order_by('dt')
    data = {
        'temps': [record.dt for record in dht],
        'temperature': [record.temp for record in dht],
        'humidity': [record.hum for record in dht]
    }
    return JsonResponse(data)

@login_required
def chart_data_mois(request):
    date_debut_mois = timezone.now().date() - timedelta(days=30)
    dht = Dht11.objects.filter(dt__gte=date_debut_mois).order_by('dt')
    data = {
        'temps': [record.dt for record in dht],
        'temperature': [record.temp for record in dht],
        'humidity': [record.hum for record in dht]
    }
    return JsonResponse(data)


from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
@login_required
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')  # Récupérer le prénom
        last_name = request.POST.get('last_name')    # Récupérer le nom
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        # Vérifier si les mots de passe correspondent
        if password != password_confirm:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect('register_view')

        # Vérifier si l'utilisateur existe déjà
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur est déjà pris.")
            return redirect('register_view')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return redirect('register_view')

        # Créer un nouvel utilisateur
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,  # Ajouter le prénom
                last_name=last_name,    # Ajouter le nom
                password=password
            )
            user.save()
            messages.success(request, "Utilisateur créé avec succès ! Vous pouvez maintenant vous connecter.")
            return redirect('login')  # Rediriger vers la page de connexion
        except Exception as e:
            messages.error(request, f"Erreur lors de la création de l'utilisateur : {e}")
            return redirect('register_view')

    return render(request, 'register.html')
@login_required
def sendtele():
    token = '6662023260:AAG4z48OO9gL8A6szdxg0SOma5hv9gIII1E'
    rece_id = 1242839034
    bot = telepot.Bot(token)
    bot.sendMessage(rece_id, 'La température dépasse la normale.')
    print('Notification envoyée.')

def custom_logout(request):
    logout(request)
    return redirect('/')


#####################################################
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from .models import Dht11, Incident, Profile, Acknowledgment, GlobalAlertSettings
from .alerts import send_telegram_alert, send_whatsapp_alert, send_email_alert

@login_required
def incident(request):
    # Récupérer le plus récent incident "en cours" (end_dt est null)
    open_incident = Incident.objects.filter(end_dt__isnull=True).order_by('-start_dt').first()

    # Récupérer les paramètres globaux des alertes
    settings = GlobalAlertSettings.objects.first()

    # Par défaut
    flag_color = 'green'
    message = "Pas d'incidents."
    incident_in_progress = False

    if open_incident:
        # S’il y a un incident en cours
        flag_color = 'red'
        message = "Attention, incident détecté."
        incident_in_progress = True

    # Si l’utilisateur envoie le formulaire pour acquitter
    if request.method == 'POST' and incident_in_progress:
        remarks = request.POST.get('remarks', '')

        # Créer (ou récupérer) un acquittement pour l’utilisateur actuel
        acknowledgment, created = Acknowledgment.objects.get_or_create(
            incident=open_incident,
            user=request.user
        )
        if created:
            # Première fois que cet utilisateur acquitte
            if remarks:
                open_incident.remarks = remarks
                open_incident.save()
            messages.success(request, "Incident acquitté avec succès.")
        else:
            messages.info(request, "Vous avez déjà acquitté cet incident.")
        return redirect('incident')

    # Vérifier si l’utilisateur a déjà acquitté
    user_acknowledged = False
    if open_incident:
        user_acknowledged = Acknowledgment.objects.filter(
            incident=open_incident,
            user=request.user
        ).exists()

    # On renvoie 'open_incident' et 'settings' dans le contexte pour y accéder dans incident.html
    return render(request, 'incident.html', {
        'flag': flag_color,
        'message': message,
        'incident_in_progress': incident_in_progress,
        'user_acknowledged': user_acknowledged,
        'open_incident': open_incident,  # IMPORTANT
        'settings': settings,  # Passer les paramètres globaux au template
    })

####################3333333333333
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Incident


# DHT/views.py

from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta, datetime
from collections import defaultdict
from .models import Incident
from .utils import filter_incidents_by_param

@login_required
def log_incident(request):
    filter_param = request.GET.get('filter', 'all')
    incidents = filter_incidents_by_param(filter_param).order_by('-start_dt')

    # Statistiques
    total_incidents = Incident.objects.count()
    active_incidents = Incident.objects.filter(end_dt__isnull=True).count()
    last_incident = Incident.objects.order_by('-start_dt').first()

    # (Optionnel) calculer incidents_per_month pour un graph, etc.

    context = {
        'incidents': incidents,
        'filter_param': filter_param,
        'total_incidents': total_incidents,
        'active_incidents': active_incidents,
        'last_incident': last_incident,
    }
    return render(request, 'log_incident.html', context)


###################################
@login_required
def alertConf_view(request):
    # Récupérer ou créer le Profile
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Champs User
        username = request.POST.get('username')
        email = request.POST.get('email')

        request.user.username = username
        request.user.email = email
        request.user.save()

        # Champs Profile
        profile.telegram_id = request.POST.get('telegram_id')
        profile.twilio_account_sid = request.POST.get('twilio_account_sid')
        profile.twilio_auth_token = request.POST.get('twilio_auth_token')
        profile.whatsapp_number = request.POST.get('whatsapp_number')
        profile.save()

        messages.success(request, "Paramètres mis à jour avec succès.")
        return redirect('alertConf_view')

    # Récupérer le lien du bot Telegram depuis les paramètres globaux
    global_settings = GlobalAlertSettings.objects.first()
    profile.telegram_bot_link = global_settings.telegram_bot_link if global_settings else ""

    return render(request, 'alertConf.html', {'profile': profile})
def custom_logout(request):
    logout(request)
    return redirect('/')


##########################################""
from collections import defaultdict
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder
import json

from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

# Importez vos modèles depuis votre application
from .models import Incident, Dht11
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, datetime
from collections import defaultdict
from django.core.serializers.json import DjangoJSONEncoder
import json
from .models import Incident, Dht11, User, Acknowledgment
from django.db.models import Count

@login_required
def dashboard(request):
    # 1. Comptabiliser les incidents par mois
    incidents_per_month = defaultdict(int)
    for incident in Incident.objects.all():
        month_label = incident.start_dt.strftime('%b %Y')
        incidents_per_month[month_label] += 1

    # 2. Trier les labels de mois chronologiquement
    sorted_months = sorted(
        incidents_per_month.keys(),
        key=lambda x: datetime.strptime(x, '%b %Y')
    )
    sorted_counts = [incidents_per_month[m] for m in sorted_months]

    # 3. Récupérer les dernières mesures DHT (température, humidité, date)
    dht_data = list(
        Dht11.objects
             .values('temp', 'hum', 'dt')
             .order_by('-dt')[:20]
    )

    # 4. Calculer le temps moyen de résolution
    resolved_incidents = Incident.objects.filter(end_dt__isnull=False)
    total_resolution_time = timedelta()
    for incident in resolved_incidents:
        total_resolution_time += incident.end_dt - incident.start_dt

    average_resolution_time = total_resolution_time / resolved_incidents.count() if resolved_incidents.count() > 0 else timedelta()

    # 5. Récupérer les derniers incidents (par exemple, les 10 derniers)
    latest_incidents = Incident.objects.order_by('-start_dt')[:10]

    # 6. Nombre de personnes qui ont acquitté un incident
    total_acknowledgments = Acknowledgment.objects.count()

    # 7. Classement des utilisateurs par nombre total d'acquittements
    user_acknowledgments = (
        User.objects
        .annotate(total_acknowledgments=Count('acknowledgment'))  # Utilisez 'acknowledgment' au lieu de 'acknowledgments'
        .order_by('-total_acknowledgments')[:5]  # Top 5 utilisateurs
    )

    # 8. Contexte pour le template
    context = {
        'total_users': User.objects.count(),
        'total_incidents': Incident.objects.count(),
        'active_incidents': Incident.objects.filter(end_dt__isnull=True).count(),
        'resolved_incidents': resolved_incidents.count(),
        'average_resolution_time': str(average_resolution_time).split(".")[0],  # Format HH:MM:SS
        'months': json.dumps(sorted_months),
        'incidents_per_month': json.dumps(sorted_counts),
        'dht_data': json.dumps(dht_data, cls=DjangoJSONEncoder),
        'latest_incidents': latest_incidents,
        'total_acknowledgments': total_acknowledgments,
        'user_acknowledgments': user_acknowledgments,
    }
    return render(request, 'dashboard.html', context)


##################################
#def is_admin(user):
#    return user.groups.filter(name='admin').exists()


from django.contrib.auth.decorators import user_passes_test


def is_admin(user):
    return user.is_authenticated and user.groups.filter(name='admin').exists()

@login_required
@user_passes_test(is_admin)
def manage_users(request):
    users = User.objects.all()
    return render(request, 'manage_users.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.save()
        messages.success(request, "Utilisateur mis à jour avec succès.")
        return redirect('manage_users')
    return render(request, 'edit_user.html', {'user': user})

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, "Utilisateur supprimé avec succès.")
        return redirect('manage_users')
    return render(request, 'delete_user.html', {'user': user})

##############################################################

# DHT/views.py


from django.contrib.auth.decorators import login_required


@login_required
def incident_detail(request, incident_id):
    incident = get_object_or_404(Incident, pk=incident_id)
    acknowledgments = Acknowledgment.objects.filter(incident=incident).select_related('user')
    ack_users = [ack.user.username for ack in acknowledgments]

    # Filtrer la plage: [start_dt, end_dt ou now]
    end_time = incident.end_dt if incident.end_dt else timezone.now()
    dht_data = Dht11.objects.filter(
        dt__gte=incident.start_dt,
        dt__lte=end_time
    ).order_by('-dt')  # plus récent en premier, par ex.

    data = {
        "id": incident.id,
        "start_dt": incident.start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "end_dt": (incident.end_dt.strftime("%Y-%m-%d %H:%M:%S")
                   if incident.end_dt else "En cours"),
        "remarks": incident.remarks or "",
        "iteration": incident.iteration,
        "ack_users": ack_users,
        "dht_data": [
            {
                "temp": d.temp,
                "hum": d.hum,
                "dt": d.dt.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for d in dht_data
        ],
    }
    return JsonResponse(data)

#############################################################

# views.py
import openpyxl


@login_required
def export_incidents_excel(request):
    filter_param = request.GET.get('filter', 'all')
    incidents = filter_incidents_by_param(filter_param).order_by('-start_dt')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Incidents"

    # En-têtes
    headers = ["ID", "Début", "Fin", "Durée", "Itération", "Remarques", "Nb Acks"]
    ws.append(headers)

    # Lignes
    for inc in incidents:
        row = [
            inc.id,
            inc.start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            inc.end_dt.strftime("%Y-%m-%d %H:%M:%S") if inc.end_dt else "En cours",
            str(inc.duration) if inc.duration else "--",
            inc.iteration,
            inc.remarks or "",
            inc.acknowledgments.count()
        ]
        ws.append(row)

    # Réponse HTTP
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    filedate = datetime.now().strftime("%Y%m%d_%H%M%S")
    response["Content-Disposition"] = f'attachment; filename="incidents_{filter_param}_{filedate}.xlsx"'
    wb.save(response)
    return response

########################
import pdfkit

from django.template.loader import render_to_string




def export_incidents_pdf(request):
    filter_param = request.GET.get('filter', 'all')
    incidents = filter_incidents_by_param(filter_param).order_by('-start_dt')

    # Charger le template HTML qui contient le design du PDF
    html_string = render_to_string('pdf_incidents.html', {
        'incidents': incidents,
        'filter_param': filter_param
    })

    # Sur PythonAnywhere, wkhtmltopdf se trouve généralement ici :
    #config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
    #Sur windows
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')


    # Générer le PDF en mémoire (False signifie "ne pas écrire sur disque")
    pdf_content = pdfkit.from_string(html_string, False, configuration=config)

    # Préparer la réponse HTTP
    response = HttpResponse(pdf_content, content_type='application/pdf')
    filedate = datetime.now().strftime("%Y%m%d_%H%M%S")
    response['Content-Disposition'] = f'attachment; filename="incidents_{filter_param}_{filedate}.pdf"'
    return response


#############################"
# views.py


from django.contrib.auth.decorators import login_required

def filter_data_by_param(filter_param):
    """Filtre les mesures Dht11 selon filter_param."""
    now = timezone.now()
    qs = Dht11.objects.all().order_by('-dt')

    if filter_param == 'jour':
        return qs.filter(dt__gte=now - timedelta(days=1))
    elif filter_param == 'semaine':
        return qs.filter(dt__gte=now - timedelta(weeks=1))
    elif filter_param == 'mois':
        # Sur 30 jours glissants par ex.
        return qs.filter(dt__gte=now - timedelta(days=30))
    elif filter_param == 'annee':
        # Sur 365 jours
        return qs.filter(dt__gte=now - timedelta(days=365))
    else:
        # 'all' ou autre param
        return qs

@login_required
def table(request):
    # Récupère le paramètre filter dans l'URL, ex: ?filter=jour
    filter_param = request.GET.get('filter', 'all')

    # Filtre les données
    data = filter_data_by_param(filter_param)

    return render(request, 'table.html', {
        'data': data,
        'filter_param': filter_param  # pour l’utiliser dans le template
    })

##########

from django.contrib.auth.decorators import login_required



@login_required
def export_pdf_data(request):
    """
    Export des mesures DHT en PDF selon le filtre (jour, semaine, etc.)
    Affiche le nom/prénom de l'utilisateur, la date d'impression
    et une signature pour l'administrateur.
    """
    filter_param = request.GET.get('filter', 'all')
    data = filter_data_by_param(filter_param)

    # Construire le contexte pour le template
    context = {
        'data': data,
        'filter_param': filter_param,
        'user': request.user,         # Pour avoir user.first_name, user.last_name
        'today': timezone.now(),      # Pour afficher la date/heure d'impression
    }

    # 1) Générer le HTML à partir du template
    html_string = render_to_string('pdf_measures.html', context)

    # 2) Configurer pdfkit
    # Sur PythonAnywhere ou Linux : /usr/bin/wkhtmltopdf

    #config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
    # sur windows
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')


    # 3) Générer le PDF en bytes (False = on ne sauvegarde pas de fichier temporaire)
    pdf_file = pdfkit.from_string(html_string, False, configuration=config)

    # 4) Retourner le PDF
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_dht.pdf"'
    return response

#############
#page 404 not found
from django.shortcuts import render

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

###################""

# DHT/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import GlobalAlertSettingsForm
from .models import GlobalAlertSettings


@login_required
def alert_globale_view(request):
    # Récupérer ou créer les paramètres globaux
    settings, created = GlobalAlertSettings.objects.get_or_create()

    if request.method == 'POST':
        form = GlobalAlertSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Paramètres globaux mis à jour avec succès.")
            return redirect('alert_globale_view')
    else:
        form = GlobalAlertSettingsForm(instance=settings)

    return render(request, 'alertGlobale.html', {'form': form})
#######################
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

@login_required
@user_passes_test(lambda u: u.groups.filter(name='admin').exists())
def stop_alerts(request):
    # Récupérer les paramètres globaux
    settings = GlobalAlertSettings.objects.first()
    if settings:
        # Basculer l'état des alertes
        settings.alerts_enabled = not settings.alerts_enabled
        settings.save()

        # Afficher un message en fonction de l'état
        if settings.alerts_enabled:
            messages.success(request, "Les alertes ont été activées.")
        else:
            messages.success(request, "Les alertes ont été désactivées.")
    else:
        messages.error(request, "Aucun paramètre global trouvé.")

    return redirect('incident')

################################""
#################################
# views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random
from .models import OTP, User, GlobalAlertSettings


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('value_view')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    return render(request, 'login.html')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            # Generate a random 6-digit OTP
            otp_code = str(random.randint(100000, 999999))
            expires_at = timezone.now() + timedelta(minutes=10)

            # Delete any existing OTP for this user
            OTP.objects.filter(user=user).delete()

            # Create a new OTP
            OTP.objects.create(user=user, code=otp_code, expires_at=expires_at)

            # Récupérer les paramètres SMTP depuis GlobalAlertSettings
            settings = GlobalAlertSettings.objects.first()
            if settings:
                # Envoyer le code OTP par e-mail
                send_mail(
                    'Réinitialisation de votre mot de passe',
                    f'Votre code OTP est : {otp_code}. Ce code est valide pendant 10 minutes.',
                    settings.smtp_user,  # Utiliser l'e-mail SMTP configuré
                    [user.email],
                    fail_silently=False,
                    auth_user=settings.smtp_user,  # Utilisateur SMTP
                    auth_password=settings.smtp_password,  # Mot de passe SMTP
                    connection=None,
                )
                messages.success(request, "Un code OTP a été envoyé à votre adresse e-mail.")
                return redirect('verify_otp')
            else:
                messages.error(request, "Les paramètres SMTP ne sont pas configurés.")
        else:
            messages.error(request, "Aucun utilisateur trouvé avec cette adresse e-mail.")
    return render(request, 'forgot_password.html')


def verify_otp(request):
    if request.method == 'POST':
        otp_code = request.POST.get('otp')
        user_otp = OTP.objects.filter(code=otp_code).first()
        if user_otp and user_otp.is_valid():
            request.session['reset_user_id'] = user_otp.user.id
            return redirect('reset_password')
        else:
            messages.error(request, "Code OTP invalide ou expiré.")
    return render(request, 'verify_otp.html')


def reset_password(request):
    if request.method == 'POST':
        user_id = request.session.get('reset_user_id')
        if user_id:
            user = User.objects.get(id=user_id)
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Votre mot de passe a été réinitialisé avec succès.")
                return redirect('login')
            else:
                messages.error(request, "Les mots de passe ne correspondent pas.")
        else:
            messages.error(request, "Session expirée. Veuillez réessayer.")
    return render(request, 'reset_password.html')


def chart_data_custom(request):
    # Récupérer les dates de début et de fin depuis les paramètres de la requête
    start_date_str = request.GET.get('start')
    end_date_str = request.GET.get('end')

    # Convertir les dates en objets datetime
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Format de date invalide. Utilisez YYYY-MM-DD.'}, status=400)

    # Filtrer les données dans la plage de dates
    dht_data = Dht11.objects.filter(dt__range=(start_date, end_date)).order_by('dt')

    # Préparer les données pour le graphique
    data = {
        'temps': [record.dt.isoformat() for record in dht_data],  # Format ISO pour JavaScript
        'temperature': [record.temp for record in dht_data],
        'humidity': [record.hum for record in dht_data]
    }

    return JsonResponse(data)