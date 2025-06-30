from django.urls import path
from . import views

app_name = 'telefonica'

urlpatterns = [
    # URL para el menú lateral
    path('menu/', views.menu_fragment, name='menu_fragment'),
    # Vistas principales
    path('', views.dashboard, name='dashboard'),
    path('ventas/', views.ventas_lista, name='ventas_lista'),
    path('ventas/nueva/', views.venta_crear, name='venta_crear'),
    path('ventas/nueva/<str:documento>/', views.venta_crear, name='venta_crear_con_documento'),
    path('ventas/<int:pk>/', views.detalle_venta, name='venta_detalle'),
    path('ventas/<int:pk>/corregir/', views.venta_corregir, name='venta_corregir'),
    path('ventas/<int:pk>/gestionar/', views.venta_gestionar, name='venta_gestionar'),
    
    # Bandejas
    path('bandejas/pendientes/', views.bandeja_pendientes, name='bandeja_pendientes'),
    path('bandejas/digitacion/', views.bandeja_digitacion, name='bandeja_digitacion'),
    path('bandejas/seguimiento/', views.bandeja_seguimiento, name='bandeja_seguimiento'),
    path('bandejas/devueltas/', views.bandeja_devueltas, name='bandeja_devueltas'),
    
    # Comisiones
    path('comisiones/', views.comisiones_lista, name='comisiones_lista'),
    path('comisiones/calcular/', views.comisiones_calcular, name='comisiones_calcular'),
    
    # APIs
    path('api/cliente/', views.buscar_cliente, name='buscar_cliente'),
]