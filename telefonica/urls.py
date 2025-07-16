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
    
    # Rutas para ventas de Portabilidad
    path('ventas/portabilidad/nueva/', views.venta_crear_portabilidad, name='venta_crear_portabilidad'),
    path('ventas/portabilidad/nueva/<str:documento>/', views.venta_crear_portabilidad, name='venta_crear_portabilidad_con_documento'),
    path('ventas/portabilidad/<int:pk>/', views.detalle_venta_portabilidad, name='detalle_venta_portabilidad'),

    
    # Rutas para ventas de Prepago
    path('ventas/prepago/nueva/', views.venta_crear_prepago, name='venta_crear_prepago'),
    path('ventas/prepago/nueva/<str:documento>/', views.venta_crear_prepago, name='venta_crear_prepago_con_documento'),
    path('ventas/prepago/<int:pk>/', views.detalle_venta_prepago, name='detalle_venta_prepago'),
    
    # Rutas para ventas de Upgrade
    path('ventas/upgrade/nueva/', views.venta_crear_upgrade, name='venta_crear_upgrade'),
    path('ventas/upgrade/nueva/<str:documento>/', views.venta_crear_upgrade, name='venta_crear_upgrade_con_documento'),
    path('ventas/upgrade/<int:pk>/', views.detalle_venta_upgrade, name='detalle_venta_upgrade'),
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
]