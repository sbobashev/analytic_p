from django.urls import path
from . import views

app_name = 'realty_analytics'

urlpatterns = [
    path('map/', views.ShowMap,  {'city_code': 'msk'}, name='map'),
    path('district/<slug:slug>/', views.ShowDistrict,  {'city_code': 'msk'}, name='district'),

]