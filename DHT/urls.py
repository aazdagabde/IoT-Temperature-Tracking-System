from django.urls import path
from . import views
from . import api
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("api", api.Dlist, name='json'),
    path("api/post", api.Dlist, name='json'),
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

]
