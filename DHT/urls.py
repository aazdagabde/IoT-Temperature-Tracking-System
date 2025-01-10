from django.urls import path
from . import views
from . import api
from django.contrib.auth import views as auth_views

from django.conf.urls import handler404
from .views import custom_404_view
from .views import alert_globale_view ,stop_alerts
handler404 =custom_404_view

urlpatterns = [
    path("api", api.Dlist, name='api'),
    path("api/post", api.Dlist, name='api_post'),
    path('download_csv/', views.download_csv, name='download_csv'),
    path('table/', views.table, name='table'),
    path('myChartTemp/', views.graphiqueTemp, name='myChartTemp'),
    path('myChartHum/', views.graphiqueHum, name='myChartHum'),
    path('chart-data/', views.chart_data, name='chart-data'),
    path('chart-data-jour/', views.chart_data_jour, name='chart-data-jour'),
    path('chart-data-semaine/', views.chart_data_semaine, name='chart-data-semaine'),
    path('chart-data-mois/', views.chart_data_mois, name='chart-data-mois'),
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register_view, name='register_view'),
    path('index/', views.value_view, name='value_view'),

    # ...
    path('incident/', views.incident, name='incident'),
    path('log_incident/', views.log_incident, name='log_incident'),

    path('alertConf/', views.alertConf_view, name='alertConf_view'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
################

    path('incident-detail/<int:incident_id>/', views.incident_detail, name='incident_detail'),


    path('export/incidents/excel/', views.export_incidents_excel, name='export_incidents_excel'),
    path('export/incidents/pdf/', views.export_incidents_pdf, name='export_incidents_pdf'),
    path('export_pdf_data/', views.export_pdf_data, name='export_pdf_data'),

    path('alert-globale/', alert_globale_view, name='alert_globale_view'),
    path('stop-alerts/', stop_alerts, name='stop_alerts')
]
