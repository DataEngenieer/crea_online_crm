from django.urls import path
from . import views
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
)

from .forms import EmailAuthenticationForm
from .views import LoginAuditoriaView, LogoutAuditoriaView
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
    path('', views.inicio, name='inicio'),
    path('inicio/', views.inicio, name='inicio'),
    path('registro/', views.registro_usuario, name='registro'),
    path('usuario/<int:user_id>/', views.detalle_usuario, name='detalle_usuario'),
    path('clientes/', views.clientes, name='clientes'),
    path('clientes/carga/', views.carga_clientes, name='carga_clientes'),
    path('clientes/crear/', views.crear_cliente_view, name='crear_cliente'),
    path('clientes/<str:documento_cliente>/', views.detalle_cliente, name='detalle_cliente'),
    path('gestiones/', views.lista_gestiones, name='lista_gestiones'), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)