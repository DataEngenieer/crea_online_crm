from django.urls import path

app_name = 'core'  # Necesario para definir el namespace de la aplicación
from . import views
from . import views_acuerdos
from . import views_reportes
from . import views_api
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
)

from .forms import EmailAuthenticationForm
from .views import LoginAuditoriaView, LogoutAuditoriaView, inicio, cambiar_modulo
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('usuarios-admin/', views.admin_usuarios, name='admin_usuarios'),
    path('login/', LoginAuditoriaView.as_view(), name='login'),
    path('logout/', LogoutAuditoriaView.as_view(), name='logout'),
    path('password_reset/', PasswordResetView.as_view(template_name='core/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(template_name='core/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='core/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(template_name='core/password_reset_complete.html'), name='password_reset_complete'),
    path('', views.inicio, name='inicio'),  # Ruta principal ahora apunta al dashboard
    path('dashboard/', views.dashboard, name='dashboard'),  # Mantener compatibilidad con la ruta antigua
    path('registro/', views.registro_usuario, name='registro'),
    path('usuario/<int:user_id>/', views.detalle_usuario, name='detalle_usuario'),
    path('clientes/', views.clientes, name='clientes'),
    path('clientes/carga/', views.carga_clientes, name='carga_clientes'),
    path('clientes/crear/', views.crear_cliente_view, name='crear_cliente'),
    path('clientes/<str:documento_cliente>/', views.detalle_cliente, name='detalle_cliente'),
    path('clientes/<str:documento_cliente>/enviar-email-prueba/', views.enviar_email_prueba, name='enviar_email_prueba'),
    path('gestiones/', views.lista_gestiones, name='lista_gestiones'),
    path('acuerdos-pago/', views.acuerdos_pago, name='acuerdos_pago'),
    path('seguimientos/', views.seguimientos, name='seguimientos'),
    path('api/seguimientos/proximos/', views.api_seguimientos_proximos, name='api_seguimientos_proximos'),
    path('api/opciones-gestion/', views.api_opciones_gestion, name='api_opciones_gestion'),
    path('seguimientos/<int:seguimiento_id>/completar/', views.marcar_seguimiento_completado, name='marcar_seguimiento_completado'),
    # Rutas AJAX para los desplegables dependientes
    path('ajax/get_opciones_nivel1/', views.get_opciones_nivel1, name='ajax_get_opciones_nivel1'),
    path('ajax/get_opciones_nivel2/', views.get_opciones_nivel2, name='ajax_get_opciones_nivel2'),
    
    # Rutas para acuerdos de pago
    path('cuotas/<int:cuota_id>/registrar-pago/', views_acuerdos.registrar_pago_cuota, name='registrar_pago_cuota'),
    path('acuerdos/<int:acuerdo_id>/registrar-multiple-pagos/', views_acuerdos.registrar_multiple_pagos, name='registrar_multiple_pagos'),
    path('api/acuerdos/<int:acuerdo_id>/cuotas/', views_acuerdos.obtener_cuotas_acuerdo, name='api_obtener_cuotas_acuerdo'),
    path('api/acuerdos/detalle/', views.detalle_acuerdo_ajax, name='detalle_acuerdo_ajax'),
    
    # Reportes
    path('reportes/', views_reportes.reportes, name='reportes'),
    path('reportes/exportar/', views_reportes.exportar_excel, name='reportes_exportar'),
    
    # Cambio de módulo
    path('set_module/', views.cambiar_modulo, name='cambiar_modulo'),
    
    # API para verificación de sesión
    path('api/check-session/', views_api.check_session, name='check_session'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)