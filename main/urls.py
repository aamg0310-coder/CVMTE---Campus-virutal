from django.urls import path
from .views import Index, Catalogo, api_rutas, detalle_ruta, detalle_petrolera, registro_view, login_view, logout_view, perfil_view, toggle_progreso_ruta, toggle_progreso_petrolera

app_name = 'main'

urlpatterns = [
    path('', Index, name='inicio'),
    path('catalogo/', Catalogo, name='catalogo'),
    path('api/rutas/', api_rutas, name='api_rutas'),
    path('ruta/<int:pk>/', detalle_ruta, name='detalle_ruta'),
    path('ruta/<slug:slug>/', detalle_ruta, name='detalle_ruta_slug'),
    path('petrolera/<int:pk>/', detalle_petrolera, name='detalle_petrolera'),
    path('petrolera/<slug:slug>/', detalle_petrolera, name='detalle_petrolera_slug'),

    # auth
    path('registro/', registro_view, name='registro'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('perfil/', perfil_view, name='perfil'),

    # progreso (marcar visto)
    path('progreso/ruta/<slug:slug>/toggle/', toggle_progreso_ruta, name='toggle_ruta'),
    path('progreso/petrolera/<slug:slug>/toggle/', toggle_progreso_petrolera, name='toggle_petrolera'),
]
