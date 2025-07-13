from django.urls import path
from . import views

app_name = 'telefonica'

urlpatterns = [
    # URL para el menú lateral
    path('menu/', views.menu_fragment, name='menu_fragment'),
    # Vistas principales
    path('dashboard/', views.dashboard, name='dashboard'),
    path('perfil/', views.perfil_telefonica, name='perfil'),
    path('', views.dashboard, name='dashboard'),
    path('ventas/', views.ventas_lista, name='ventas_lista'),
    path('ventas/nueva/', views.venta_crear, name='venta_crear'),
    path('ventas/nueva/<str:documento>/', views.venta_crear, name='venta_crear_con_documento'),
    path('ventas/<int:pk>/', views.detalle_venta, name='venta_detalle'),
    path('ventas/<int:pk>/corregir/', views.venta_corregir, name='venta_corregir'),
    
    # Bandejas
    path('bandejas/pendientes/', views.bandeja_pendientes, name='bandeja_pendientes'),
    path('bandejas/digitacion/', views.bandeja_digitacion, name='bandeja_digitacion'),
    path('bandejas/seguimiento/', views.bandeja_seguimiento, name='bandeja_seguimiento'),
    path('bandejas/devueltas/', views.bandeja_devueltas, name='bandeja_devueltas'),
    
    # Comisiones
    path('comisiones/', views.comisiones_lista, name='comisiones_lista'),
    path('comisiones/calcular/', views.comisiones_calcular, name='comisiones_calcular'),
    
    # Gestión de planes de portabilidad
    path('planes-portabilidad/', views.planes_portabilidad_lista, name='planes_portabilidad_lista'),
    path('planes-portabilidad/crear/', views.plan_portabilidad_crear, name='plan_portabilidad_crear'),
    path('planes-portabilidad/<int:plan_id>/editar/', views.plan_portabilidad_editar, name='plan_portabilidad_editar'),
    path('planes-portabilidad/<int:plan_id>/eliminar/', views.plan_portabilidad_eliminar, name='plan_portabilidad_eliminar'),
    path('planes-portabilidad/<int:plan_id>/cambiar-estado/', views.plan_portabilidad_cambiar_estado, name='plan_portabilidad_cambiar_estado'),
    path('planes/crear/', views.plan_crear, name='plan_crear'),
    path('planes/<int:plan_id>/', views.plan_detalle, name='plan_detalle'),
    path('planes/<int:plan_id>/editar/', views.plan_editar, name='plan_editar'),
    path('planes/<int:plan_id>/eliminar/', views.plan_eliminar, name='plan_eliminar'),
    path('planes/<int:plan_id>/cambiar-estado/', views.plan_cambiar_estado, name='plan_cambiar_estado'),
]