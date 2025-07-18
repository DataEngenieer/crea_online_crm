from django.urls import path
from . import views, views_clientes
import json

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
    path('ventas/prepago/nueva/telefono/<str:telefono>/', views.venta_crear_prepago, name='venta_crear_prepago_con_telefono'),
    path('ventas/prepago/<int:pk>/', views.detalle_venta_prepago, name='detalle_venta_prepago'),
    
    # Rutas para ventas de Upgrade
    path('ventas/upgrade/nueva/', views.venta_crear_upgrade, name='venta_crear_upgrade'),
    path('ventas/upgrade/nueva/<str:documento>/', views.venta_crear_upgrade, name='venta_crear_upgrade_con_documento'),
    path('ventas/upgrade/nueva/registro/<str:nro_registro>/', views.venta_crear_upgrade, name='venta_crear_upgrade_con_nro_registro'),
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
    
    # Rutas para agendamientos
    path('agendamientos/', views.agendamiento_lista, name='agendamiento_lista'),
    path('agendamientos/crear/', views.agendamiento_crear, name='agendamiento_crear'),
    path('agendamientos/<int:pk>/', views.agendamiento_detalle, name='agendamiento_detalle'),
    path('agendamientos/<int:pk>/editar/', views.agendamiento_editar, name='agendamiento_editar'),
    path('agendamientos/calendario/', views.agendamiento_calendario, name='agendamiento_calendario'),
    path('agendamientos/eventos-api/', views.agendamiento_eventos_api, name='agendamiento_eventos_api'),
    
    # Rutas para gestión de clientes
    path('clientes/', views_clientes.clientes_lista, name='clientes_lista'),
    
    # Clientes Upgrade
    path('clientes/upgrade/crear/', views_clientes.cliente_upgrade_crear, name='cliente_upgrade_crear'),
    path('clientes/upgrade/<int:pk>/editar/', views_clientes.cliente_upgrade_editar, name='cliente_upgrade_editar'),
    path('clientes/upgrade/<int:pk>/eliminar/', views_clientes.cliente_upgrade_eliminar, name='cliente_upgrade_eliminar'),
    path('clientes/upgrade/carga/', views_clientes.carga_clientes_upgrade, name='carga_clientes_upgrade'),
    path('clientes/upgrade/plantilla/', views_clientes.descargar_plantilla_upgrade, name='descargar_plantilla_upgrade'),
    
    # Clientes PrePos
    path('clientes/prepos/crear/', views_clientes.cliente_prepos_crear, name='cliente_prepos_crear'),
    path('clientes/prepos/<int:pk>/editar/', views_clientes.cliente_prepos_editar, name='cliente_prepos_editar'),
    path('clientes/prepos/<int:pk>/eliminar/', views_clientes.cliente_prepos_eliminar, name='cliente_prepos_eliminar'),
    path('clientes/prepos/carga/', views_clientes.carga_clientes_prepos, name='carga_clientes_prepos'),
    path('clientes/prepos/plantilla/', views_clientes.descargar_plantilla_prepos, name='descargar_plantilla_prepos'),
    
    # API para autocompletado
    path('api/clientes/upgrade/buscar/', views_clientes.buscar_cliente_upgrade_por_documento, name='buscar_cliente_upgrade'),
    path('api/clientes/prepos/buscar/', views_clientes.buscar_cliente_prepos_por_telefono, name='buscar_cliente_prepos'),
]