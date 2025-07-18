from django.contrib import admin
from .models import (
    VentaPortabilidad,
    VentaPrePos,
    VentaUpgrade,
    ClientesUpgrade,
    ClientesPrePos,
    GestionAsesor, 
    GestionBackoffice,
    Comision,
    Planes_portabilidad,
    Agendamiento,
    Escalamiento
)


@admin.register(Planes_portabilidad)
class PlanesPortabilidadAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre_plan', 'CFM', 'estado', 'fecha_creacion')
    search_fields = ('codigo', 'nombre_plan')
    list_filter = ('estado',)
    date_hierarchy = 'fecha_creacion'


@admin.register(VentaPortabilidad)
class VentaPortabilidadAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_completo_portabilidad', 'plan_adquiere', 'estado_venta', 'agente', 'backoffice', 'fecha_creacion')
    search_fields = ('documento', 'nombres', 'apellidos', 'numero')
    list_filter = ('estado_venta', 'agente', 'backoffice')
    date_hierarchy = 'fecha_creacion'

@admin.register(ClientesPrePos)
class ClientesPrePosAdmin(admin.ModelAdmin):
    list_display = ('id', 'telefono', 'fecha_creacion')
    search_fields = ('telefono',)
    list_filter = ('fecha_creacion',)
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

@admin.register(VentaPrePos)
class VentaPrePosAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_completo_prepos', 'plan_adquiere', 'cliente_base', 'tipo_cliente', 'agente', 'fecha_creacion')
    search_fields = ('documento', 'nombres', 'apellidos', 'numero', 'telefono_legalizacion')
    list_filter = ('agente', 'tipo_cliente', 'cliente_base')
    date_hierarchy = 'fecha_creacion'

@admin.register(ClientesUpgrade)
class ClientesUpgradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_cliente', 'documento', 'tipo_documento', 'campana', 'promedio_fact', 'fecha_creacion')
    search_fields = ('nombre_cliente', 'documento', 'id_base', 'nro_registro')
    list_filter = ('tipo_documento', 'campana', 'grupo_campana', 'estrategia', 'producto')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

@admin.register(VentaUpgrade)
class VentaUpgradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_completo_upgrade', 'plan_adquiere', 'cliente_base', 'agente', 'fecha_creacion')
    search_fields = ('documento', 'nombres', 'apellidos', 'numero')
    list_filter = ('agente', 'tipo_cliente', 'cliente_base')
    date_hierarchy = 'fecha_creacion'

@admin.register(GestionAsesor)
class GestionAsesorAdmin(admin.ModelAdmin):
    list_display = ('venta', 'agente', 'fecha_gestion')
    search_fields = ('venta__documento', 'venta__nombres', 'agente__username')
    list_filter = ('agente',)
    date_hierarchy = 'fecha_gestion'

@admin.register(GestionBackoffice)
class GestionBackofficeAdmin(admin.ModelAdmin):
    list_display = ('venta', 'backoffice', 'fecha_gestion')
    search_fields = ('venta__documento', 'venta__nombres', 'backoffice__username')
    list_filter = ('backoffice',)
    date_hierarchy = 'fecha_gestion'

@admin.register(Comision)
class ComisionAdmin(admin.ModelAdmin):
    list_display = ('venta', 'agente', 'monto', 'estado')
    search_fields = ('venta__documento', 'agente__username')
    list_filter = ('estado', 'agente')
    date_hierarchy = 'fecha_creacion'

@admin.register(Agendamiento)
class AgendamientoAdmin(admin.ModelAdmin):
    list_display = ('nombre_cliente', 'telefono_contacto', 'tipo_venta', 'fecha_volver_a_llamar', 'hora_volver_a_llamar', 'Estado_agendamiento', 'agente')
    search_fields = ('nombre_cliente', 'telefono_contacto')
    list_filter = ('Estado_agendamiento', 'tipo_venta', 'agente')
    date_hierarchy = 'fecha_volver_a_llamar'

@admin.register(Escalamiento)
class EscalamientoAdmin(admin.ModelAdmin):
    list_display = ('venta', 'tipo_escalamiento', 'solucionado', 'fecha_escalamiento', 'fecha_solucion')
    search_fields = ('venta__documento', 'venta__nombres')
    list_filter = ('tipo_escalamiento', 'solucionado')
    date_hierarchy = 'fecha_escalamiento'