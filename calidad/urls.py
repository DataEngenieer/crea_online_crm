from django.urls import path, include
from . import views
from . import views_prepago
from . import views_upgrade
from .views_audio import obtener_grafico_onda, control_voz, obtener_url_audio, resubir_a_minio, obtener_grafico_onda_upgrade

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
    # Selección de tipo de auditoría
    path('auditorias/nueva/', calidad_required(views.seleccionar_tipo_auditoria), name='seleccionar_tipo_auditoria'),
    
    # Listado y creación - Portabilidad (original)
    path('auditorias/', calidad_required(views.AuditoriaListView.as_view()), name='lista_auditorias'),
    path('auditorias/crear/', calidad_required(views.AuditoriaCreateView.as_view()), name='crear_auditoria'),
    
    # Detalle, edición y eliminación - Portabilidad
    path('auditorias/<int:pk>/', calidad_required(views.AuditoriaDetailView.as_view()), name='detalle_auditoria'),
    path('auditorias/editar/<int:pk>/', calidad_required(views.AuditoriaUpdateView.as_view()), name='editar_auditoria'),
    path('auditorias/eliminar/<int:pk>/', calidad_required(views.AuditoriaDeleteView.as_view()), name='eliminar_auditoria'),
    
    # ========== Auditorías Prepago ==========
    path('auditorias-prepago/', calidad_required(views_prepago.AuditoriaPrepagoListView.as_view()), name='lista_auditorias_prepago'),
    path('auditorias-prepago/crear/', calidad_required(views_prepago.AuditoriaPrepagoCreateView.as_view()), name='crear_auditoria_prepago'),
    path('auditorias-prepago/<int:pk>/', calidad_required(views_prepago.AuditoriaPrepagoDetailView.as_view()), name='detalle_auditoria_prepago'),
    path('auditorias-prepago/editar/<int:pk>/', calidad_required(views_prepago.AuditoriaPrepagoUpdateView.as_view()), name='editar_auditoria_prepago'),
    path('auditorias-prepago/evaluar/<int:pk>/', calidad_required(views_prepago.evaluar_auditoria_prepago), name='evaluar_auditoria_prepago'),
    path('auditorias-prepago/ajax/indicadores/<int:matriz_id>/', calidad_required(views_prepago.ajax_obtener_indicadores_prepago), name='ajax_obtener_indicadores_prepago'),
    path('auditorias-prepago/responder/<int:auditoria_id>/', calidad_required(views_prepago.responder_auditoria_prepago), name='responder_auditoria_prepago'),
    path('dashboard-prepago/', calidad_required(views_prepago.dashboard_prepago), name='dashboard_prepago'),
    
    # ========== Auditorías Upgrade ==========
    path('auditorias-upgrade/', calidad_required(views_upgrade.AuditoriaUpgradeListView.as_view()), name='lista_auditorias_upgrade'),
    path('auditorias-upgrade/crear/', calidad_required(views_upgrade.AuditoriaUpgradeCreateView.as_view()), name='crear_auditoria_upgrade'),
    path('auditorias-upgrade/<int:pk>/', calidad_required(views_upgrade.AuditoriaUpgradeDetailView.as_view()), name='detalle_auditoria_upgrade'),
    path('auditorias-upgrade/editar/<int:pk>/', calidad_required(views_upgrade.AuditoriaUpgradeUpdateView.as_view()), name='editar_auditoria_upgrade'),
    path('auditorias-upgrade/evaluar/<int:pk>/', calidad_required(views_upgrade.evaluar_auditoria_upgrade), name='evaluar_auditoria_upgrade'),
    path('auditorias-upgrade/ajax/indicadores/<int:matriz_id>/', calidad_required(views_upgrade.ajax_obtener_indicadores_upgrade), name='ajax_obtener_indicadores_upgrade'),
    path('auditorias-upgrade/responder/<int:auditoria_id>/', calidad_required(views_upgrade.responder_auditoria_upgrade), name='responder_auditoria_upgrade'),
    path('dashboard-upgrade/', calidad_required(views_upgrade.dashboard_upgrade), name='dashboard_upgrade'),
    path('auditorias-upgrade/<int:pk>/descargar-audio/', calidad_required(views_upgrade.descargar_audio_upgrade), name='descargar_audio_upgrade'),
    
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
    path('api/audio/grafico-onda-upgrade/<int:auditoria_id>/',
         calidad_required(obtener_grafico_onda_upgrade),
         name='obtener_grafico_onda_upgrade'),
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
    
    # URLs para matrices de calidad específicas por tipo de campaña
    # Matrices de Prepago
    path('matriz/prepago/', views.lista_matriz_prepago, name='lista_matriz_prepago'),
    path('matriz/prepago/crear/', views.crear_editar_matriz_prepago, name='crear_matriz_prepago'),
    path('matriz/prepago/editar/<int:id>/', views.crear_editar_matriz_prepago, name='editar_matriz_prepago'),
    path('matriz/prepago/toggle/<int:id>/', views.toggle_matriz_prepago_activo, name='toggle_matriz_prepago_activo'),
    
    # Matrices de Upgrade
    path('matriz/upgrade/', views.lista_matriz_upgrade, name='lista_matriz_upgrade'),
    path('matriz/upgrade/crear/', views.crear_editar_matriz_upgrade, name='crear_matriz_upgrade'),
    path('matriz/upgrade/editar/<int:id>/', views.crear_editar_matriz_upgrade, name='editar_matriz_upgrade'),
    path('matriz/upgrade/toggle/<int:id>/', views.toggle_matriz_upgrade_activo, name='toggle_matriz_upgrade_activo'),
    
    # ========== VISTAS PARA ASESORES ==========
    # Dashboard para asesores
    path('asesor/', views.dashboard_asesor, name='dashboard_asesor'),
    
    # Mis auditorías - Portabilidad (original)
    path('asesor/mis-auditorias/', views.MisAuditoriasListView.as_view(), name='mis_auditorias'),
    path('asesor/auditoria/<int:pk>/', views.MiAuditoriaDetailView.as_view(), name='mi_auditoria_detalle'),
    
    # Mis auditorías - Prepago
    path('asesor/mis-auditorias-prepago/', views_prepago.MisAuditoriasPrepagoListView.as_view(), name='mis_auditorias_prepago'),
    
    # Mis auditorías - Upgrade
    path('asesor/mis-auditorias-upgrade/', views_upgrade.MisAuditoriasUpgradeListView.as_view(), name='mis_auditorias_upgrade'),
    
    # Responder a indicadores
    path('asesor/responder/<int:detalle_id>/', views.ResponderIndicadorView.as_view(), name='responder_indicador'),
    path('asesor/editar-respuesta/<int:pk>/', views.EditarRespuestaView.as_view(), name='editar_respuesta'),
]
