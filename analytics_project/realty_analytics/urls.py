from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.AnHome, name = 'home'),
    path('about/', views.ShowAbout, name='about'),
    path('journal/', views.ShowJournal, name='journal'),
    path('article/<slug:slug>/', views.ShowArticle, name='article'),
    path('tariffs/', views.ShowTariffs, name='tariffs'),


# --- АУТЕНТИФИКАЦИЯ ---
    path('register/', views.register_view, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile'),


# --- API ---
    path('api/districts/', views.get_districts_geojson, name='get_districts_geojson'),
    # path('api/price-history/<int:district_id>/', views.get_price_history_api, name='get_price_history_api'),
    path('api/analytics-chart/', views.get_analytics_chart_data, name='analytics_chart_data'),
    path('api/zone-class-dynamics/', views.get_zone_class_dynamics_api, name='zone_class_dynamics_api'),




# Подключаем URL-ы для городов
    path('msk/', include('realty_analytics.msk_urls', namespace='msk')),
    path('spb/', include('realty_analytics.spb_urls', namespace='spb')),
]