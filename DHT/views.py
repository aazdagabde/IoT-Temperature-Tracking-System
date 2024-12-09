from django.shortcuts import render
from .models import Dht11  # Assurez-vous d'importer le modèle Dht11
from django.utils import timezone
import csv
from django.http import HttpResponse
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth import logout

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
def home(request):
    return render(request, 'home.html')
@login_required
def table(request):
    derniere_ligne = Dht11.objects.last()
    derniere_date = derniere_ligne.dt
    delta_temps = timezone.now() - derniere_date
    difference_minutes = delta_temps.seconds // 60
    temps_ecoule = f'il y a {difference_minutes} min'
    if difference_minutes > 60:
        temps_ecoule = f'il y a {difference_minutes // 60}h {difference_minutes % 60}min'
    valeurs = {
        'date': temps_ecoule,
        'id': derniere_ligne.id,
        'temp': derniere_ligne.temp,
        'hum': derniere_ligne.hum
    }
    return render(request, 'value.html', {'valeurs': valeurs})

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

def index_view(request):
    return render(request, 'index.html')

@login_required
def graphiqueTemp(request):
    return render(request, 'ChartTemp.html')

@login_required
def graphiqueHum(request):
    return render(request, 'ChartHum.html')

@login_required
def chart_data(request):
    dht = Dht11.objects.all()
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
    dht = Dht11.objects.filter(dt__range=(last_24_hours, now))
    data = {
        'temps': [record.dt for record in dht],
        'temperature': [record.temp for record in dht],
        'humidity': [record.hum for record in dht]
    }
    return JsonResponse(data)

@login_required
def chart_data_semaine(request):
    date_debut_semaine = timezone.now().date() - timedelta(days=7)
    dht = Dht11.objects.filter(dt__gte=date_debut_semaine)
    data = {
        'temps': [record.dt for record in dht],
        'temperature': [record.temp for record in dht],
        'humidity': [record.hum for record in dht]
    }
    return JsonResponse(data)

@login_required
def chart_data_mois(request):
    date_debut_mois = timezone.now().date() - timedelta(days=30)
    dht = Dht11.objects.filter(dt__gte=date_debut_mois)
    data = {
        'temps': [record.dt for record in dht],
        'temperature': [record.temp for record in dht],
        'humidity': [record.hum for record in dht]
    }
    return JsonResponse(data)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

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