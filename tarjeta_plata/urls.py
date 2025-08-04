from django.urls import path
from . import views

app_name = 'tarjeta_plata'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),
    
    # Gestión de ventas
    path('ventas/', views.lista_ventas, name='lista_ventas'),
    path('venta/crear/', views.crear_venta, name='crear_venta'),
    path('venta/<int:venta_id>/', views.detalle_venta, name='detalle_venta'),
    path('venta/<int:venta_id>/editar/', views.editar_venta, name='editar_venta'),
    
    # Bandejas de trabajo
    path('bandeja/nuevas/', views.bandeja_nuevas, name='bandeja_nuevas'),
    path('bandeja/aceptadas/', views.bandeja_aceptadas, name='bandeja_aceptadas'),
    path('bandeja/rechazadas/', views.bandeja_rechazadas, name='bandeja_rechazadas'),
    
    # Gestión del backoffice
    path('backoffice/validar/<int:venta_id>/', views.validar_venta, name='validar_venta'),
    path('backoffice/rechazar/<int:venta_id>/', views.rechazar_venta, name='rechazar_venta'),
    path('backoffice/auditoria/<int:venta_id>/', views.crear_auditoria, name='crear_auditoria'),
    
    # Gestión de clientes
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/<int:cliente_id>/', views.detalle_cliente, name='detalle_cliente'),
    path('clientes/<int:cliente_id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/carga-masiva/', views.carga_masiva_clientes, name='carga_masiva_clientes'),
    path('clientes/plantilla/', views.plantilla_clientes, name='plantilla_clientes'),
    
    # Reportes y exportación
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/exportar/', views.reportes_exportar, name='reportes_exportar'),
    path('exportar-ventas/', views.exportar_ventas, name='exportar_ventas'),
    path('exportar/clientes/', views.exportar_clientes, name='exportar_clientes'),
    
    # API endpoints para AJAX
    path('api/estadisticas/', views.api_estadisticas, name='api_estadisticas'),
    path('api/ventas-por-dia/', views.api_ventas_por_dia, name='api_ventas_por_dia'),
]