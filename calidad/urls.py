from django.urls import path, include
from . import views
from .views_audio import obtener_grafico_onda, control_voz, obtener_url_audio, resubir_a_minio

from .api import buscar_usuarios
from .decorators import grupo_requerido, ip_permitida
from django.views.decorators.http import require_http_methods

app_name = 'calidad'

# Decoradores comunes para las vistas
def calidad_required(view_func):
    """
    Decorador para verificar que el usuario pertenezca al grupo de Calidad o sea Administrador
    y que su IP esté permitida
    """
    wrapped_view = ip_permitida(grupo_requerido('Calidad', 'Administrador')(view_func))
    return wrapped_view

urlpatterns = [
    # Dashboard
    path('', calidad_required(views.dashboard_calidad), name='dashboard'),


    # ========== API ==========
    path('api/usuarios/buscar/', buscar_usuarios, name='api_buscar_usuarios'),
    path('api/auditorias/<int:pk>/', calidad_required(views.api_detalle_auditoria), name='api_detalle_auditoria'),
    
    # ========== Matriz de Calidad ==========
    path('matriz/', calidad_required(views.lista_matriz_calidad), name='lista_matriz'),
    path('matriz/crear/', calidad_required(views.crear_editar_matriz), name='crear_editar_matriz'),
    path('matriz/editar/<int:id>/', calidad_required(views.crear_editar_matriz), name='editar_matriz'),
    path('matriz/activar/<int:id>/', calidad_required(views.activar_desactivar_matriz), name='activar_matriz'),
    path('matriz/toggle-activo/<int:id>/', calidad_required(views.toggle_matriz_activo), name='toggle_matriz_activo'),
    
 

    # ========== Auditorías de Calidad ==========
    # Listado y creación
    path('auditorias/', calidad_required(views.AuditoriaListView.as_view()), name='lista_auditorias'),
    path('auditorias/crear/', calidad_required(views.AuditoriaCreateView.as_view()), name='crear_auditoria'),
    
    # Detalle, edición y eliminación
    path('auditorias/<int:pk>/', calidad_required(views.AuditoriaDetailView.as_view()), name='detalle_auditoria'),
    path('auditorias/editar/<int:pk>/', calidad_required(views.AuditoriaUpdateView.as_view()), name='editar_auditoria'),
    path('auditorias/eliminar/<int:pk>/', calidad_required(views.AuditoriaDeleteView.as_view()), name='eliminar_auditoria'),
    
    path('auditorias/<int:pk>/descargar-audio/', 
         calidad_required(views.descargar_audio_llamada), 
         name='descargar_audio_auditoria'),
    
    # Estadísticas e informes
    path('uso-audio/', views.dashboard_uso_audio, name='dashboard_uso_audio'),
    path('auditorias/estadisticas/', 
         calidad_required(views.estadisticas_auditorias), 
         name='estadisticas_auditorias'),
         
    # ========== API de Audio ==========
    path('api/audio/grafico-onda/<int:speech_id>/', 
         calidad_required(obtener_grafico_onda), 
         name='obtener_grafico_onda'),
    path('api/audio/control-voz/', 
         calidad_required(control_voz), 
         name='control_voz'),
    path('api/audio/url/<int:speech_id>/', 
         calidad_required(obtener_url_audio), 
         name='obtener_url_audio'),
    path('api/audio/resubir-minio/<int:speech_id>/', 
         calidad_required(resubir_a_minio), 
         name='resubir_a_minio'),
    
    # URL de perfil
    path('perfil/', views.perfil, name='perfil'),
    
    # ========== VISTAS PARA ASESORES ==========
    # Dashboard para asesores
    path('asesor/', views.dashboard_asesor, name='dashboard_asesor'),
    
    # Mis auditorías
    path('asesor/mis-auditorias/', views.MisAuditoriasListView.as_view(), name='mis_auditorias'),
    path('asesor/auditoria/<int:pk>/', views.MiAuditoriaDetailView.as_view(), name='mi_auditoria_detalle'),
    
    # Responder a indicadores
    path('asesor/responder/<int:detalle_id>/', views.ResponderIndicadorView.as_view(), name='responder_indicador'),
    path('asesor/editar-respuesta/<int:pk>/', views.EditarRespuestaView.as_view(), name='editar_respuesta'),
]