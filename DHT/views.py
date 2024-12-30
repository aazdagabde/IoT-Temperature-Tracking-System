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

@login_required
def table(request):
    data = Dht11.objects.all().order_by('-dt')
    return render(request, 'table.html', {'data': data})

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

@login_required
def register_view(request):
    # Si besoin d'une page d'enregistrement, à adapter.
    if request.user.username not in ["admin", "admin2"]:
        return HttpResponseForbidden("Vous n'avez pas la permission d'accéder à cette page.")
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if password != password_confirm:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect('register_view')
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            user.save()
            messages.success(request, "Utilisateur ajouté avec succès !")
            return redirect('/index')
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
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
from .models import Dht11, Incident ,Profile, Acknowledgment

from .alerts import send_telegram_alert, send_whatsapp_alert, send_email_alert

@login_required
def incident(request):
    open_incident = Incident.objects.filter(end_dt__isnull=True).order_by('-start_dt').first()

    flag_color = 'green'
    message = "Pas d'incidents."
    incident_in_progress = False

    if open_incident:
        flag_color = 'red'
        message = "Attention, incident détecté."
        incident_in_progress = True

    if request.method == 'POST' and incident_in_progress:
        remarks = request.POST.get('remarks', '')
        # Créer une acknowledgment pour l'utilisateur actuel
        acknowledgment, created = Acknowledgment.objects.get_or_create(
            incident=open_incident,
            user=request.user
        )
        if created:
            messages.success(request, "Incident acquitté avec succès.")
            if remarks:
                open_incident.remarks = remarks
                open_incident.save()
        else:
            messages.info(request, "Vous avez déjà acquitté cet incident.")
        return redirect('incident')

    # Vérifier si l'utilisateur a déjà acquitté
    user_acknowledged = False
    if open_incident:
        user_acknowledged = Acknowledgment.objects.filter(incident=open_incident, user=request.user).exists()

    return render(request, 'incident.html', {
        'flag': flag_color,
        'message': message,
        'incident_in_progress': incident_in_progress,
        'user_acknowledged': user_acknowledged
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
@login_required
def log_incident(request):
    # Récupérer le filtre depuis les paramètres GET
    filter_param = request.GET.get('filter', 'all')
    now = timezone.now()

    if filter_param == 'jour':
        incidents = Incident.objects.filter(start_dt__gte=now - timedelta(days=1)).order_by('-start_dt')
    elif filter_param == 'semaine':
        incidents = Incident.objects.filter(start_dt__gte=now - timedelta(weeks=1)).order_by('-start_dt')
    elif filter_param == 'mois':
        incidents = Incident.objects.filter(start_dt__gte=now - timedelta(days=30)).order_by('-start_dt')
    elif filter_param == 'annee':
        incidents = Incident.objects.filter(start_dt__gte=now - timedelta(days=365)).order_by('-start_dt')
    else:
        incidents = Incident.objects.all().order_by('-start_dt')

    # Statistiques Résumées
    total_incidents = Incident.objects.count()
    active_incidents = Incident.objects.filter(end_dt__isnull=True).count()
    last_incident = Incident.objects.order_by('-start_dt').first()

    # Données pour le Graphique (Nombre d'incidents par mois)
    incidents_per_month = defaultdict(int)

    # Filtrer les incidents selon le filtre appliqué
    filtered_incidents = incidents

    for incident in filtered_incidents:
        month_label = incident.start_dt.strftime('%b %Y')
        incidents_per_month[month_label] += 1

    # Trier les mois chronologiquement
    sorted_months = sorted(incidents_per_month.keys(), key=lambda x: datetime.strptime(x, '%b %Y'))
    sorted_counts = [incidents_per_month[month] for month in sorted_months]

    context = {
        'incidents': incidents,
        'total_incidents': total_incidents,
        'active_incidents': active_incidents,
        'last_incident': last_incident,
        'months': sorted_months,
        'incidents_per_month': sorted_counts,
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

    return render(request, 'alertConf.html', {'profile': profile})

def custom_logout(request):
    logout(request)
    return redirect('/')


##########################################""
# DHT/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta, datetime
from collections import defaultdict
from .models import Incident

def is_admin(user):
    return user.is_authenticated and user.groups.filter(name='admin').exists()

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    # Statistiques
    total_users = User.objects.count()
    total_incidents = Incident.objects.count()
    active_incidents = Incident.objects.filter(end_dt__isnull=True).count()
    latest_incidents = Incident.objects.order_by('-start_dt')[:5]

    # Données pour le graphique (Nombre d'incidents par mois)
    incidents_per_month = defaultdict(int)
    for incident in Incident.objects.all():
        month_label = incident.start_dt.strftime('%b %Y')
        incidents_per_month[month_label] += 1

    # Trier les mois chronologiquement
    sorted_months = sorted(incidents_per_month.keys(), key=lambda x: datetime.strptime(x, '%b %Y'))
    sorted_counts = [incidents_per_month[month] for month in sorted_months]

    context = {
        'total_users': total_users,
        'total_incidents': total_incidents,
        'active_incidents': active_incidents,
        'latest_incidents': latest_incidents,
        'months': sorted_months,
        'incidents_per_month': sorted_counts,
    }

    return render(request, 'dashboard.html', context)


#def is_admin(user):
#    return user.groups.filter(name='admin').exists()


from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User

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