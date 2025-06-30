from django.contrib import admin
from .models import (
    Cliente, 
    Venta, 
    GestionAsesor, 
    GestionBackoffice,
    Comision
)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('documento', 'nombres', 'apellidos', 'correo', 'telefono')
    search_fields = ('documento', 'nombres', 'apellidos', 'correo')
    list_filter = ('ciudad', 'departamento')

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'plan_adquiere', 'estado_revisado', 'agente', 'backoffice', 'fecha_creacion')
    search_fields = ('cliente__documento', 'cliente__nombres', 'cliente__apellidos', 'numero', 'imei')
    list_filter = ('estado_revisado', 'agente', 'backoffice', 'tipo_cliente', 'segmento')
    date_hierarchy = 'fecha_creacion'

@admin.register(GestionAsesor)
class GestionAsesorAdmin(admin.ModelAdmin):
    list_display = ('venta', 'agente', 'fecha_gestion', 'estado')
    search_fields = ('venta__cliente__documento', 'venta__cliente__nombres', 'agente__username')
    list_filter = ('estado', 'agente')
    date_hierarchy = 'fecha_gestion'

@admin.register(GestionBackoffice)
class GestionBackofficeAdmin(admin.ModelAdmin):
    list_display = ('venta', 'backoffice', 'fecha_gestion', 'estado')
    search_fields = ('venta__cliente__documento', 'venta__cliente__nombres', 'backoffice__username')
    list_filter = ('estado', 'backoffice')
    date_hierarchy = 'fecha_gestion'

@admin.register(Comision)
class ComisionAdmin(admin.ModelAdmin):
    list_display = ('venta', 'agente', 'valor', 'fecha_calculo', 'estado')
    search_fields = ('venta__cliente__documento', 'agente__username')
    list_filter = ('estado', 'agente')
    date_hierarchy = 'fecha_calculo'