from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('enviar/', views.enviar_mensaje, name='enviar_mensaje'),
    path('mensajes/', views.obtener_mensajes, name='obtener_mensajes'),
    path('masivo/', views.enviar_masivo, name='enviar_masivo'),
]
