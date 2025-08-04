from django.contrib import admin
from .models import (
    ClienteTarjetaPlata,
    VentaTarjetaPlata,
    AuditoriaBackofficeTarjetaPlata,
    GestionBackofficeTarjetaPlata
)


@admin.register(ClienteTarjetaPlata)
class ClienteTarjetaPlataAdmin(admin.ModelAdmin):
    """Administración de clientes de tarjeta de crédito"""
    
    list_display = (
        'item', 'nombre_completo', 'telefono', 'factibilidad', 
        'tipo', 'rfc', 'fecha_creacion'
    )
    list_filter = ('factibilidad', 'tipo', 'genero', 'fecha_creacion')
    search_fields = ('item', 'nombre_completo', 'telefono', 'rfc', 'email')
    date_hierarchy = 'fecha_creacion'
    ordering = ['-fecha_creacion']
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('item', 'nombre_completo', 'telefono', 'email')
        }),
        ('Datos Personales', {
            'fields': ('rfc', 'fecha_nacimiento', 'genero')
        }),
        ('Clasificación', {
            'fields': ('factibilidad', 'tipo')
        }),
        ('Control', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VentaTarjetaPlata)
class VentaTarjetaPlataAdmin(admin.ModelAdmin):
    """Administración de ventas de tarjeta de crédito"""
    
    list_display = (
        'id_preap', 'nombre', 'telefono', 'estado_venta', 
        'agente', 'backoffice', 'fecha_creacion'
    )
    list_filter = ('estado_venta', 'agente', 'backoffice', 'fecha_creacion')
    search_fields = ('id_preap', 'item', 'nombre', 'rfc', 'telefono', 'correo')
    date_hierarchy = 'fecha_creacion'
    ordering = ['-fecha_creacion']
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'fecha_revision')
    
    fieldsets = (
        ('Identificación', {
            'fields': ('id_preap', 'item')
        }),
        ('Datos del Cliente', {
            'fields': ('nombre', 'ine', 'rfc', 'telefono', 'correo')
        }),
        ('Dirección', {
            'fields': ('direccion', 'codigo_postal')
        }),
        ('Estado y Gestión', {
            'fields': ('estado_venta', 'agente', 'backoffice', 'cliente_base')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
        ('Control de Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'fecha_revision'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related"""
        return super().get_queryset(request).select_related('agente', 'backoffice', 'cliente_base')


@admin.register(AuditoriaBackofficeTarjetaPlata)
class AuditoriaBackofficeTarjetaPlataAdmin(admin.ModelAdmin):
    """Administración de auditorías del backoffice"""
    
    list_display = (
        'id_auditoria_back', 'venta', 'call_review', 
        'auditor', 'fecha_auditoria'
    )
    list_filter = ('call_review', 'auditor', 'fecha_auditoria')
    search_fields = ('id_auditoria_back', 'venta__id_preap', 'venta__nombre')
    date_hierarchy = 'fecha_auditoria'
    ordering = ['-fecha_auditoria']
    readonly_fields = ('id_auditoria_back', 'fecha_auditoria', 'fecha_actualizacion')
    
    fieldsets = (
        ('Identificación', {
            'fields': ('id_auditoria_back', 'venta')
        }),
        ('Auditoría', {
            'fields': ('call_review', 'call_upload', 'auditor')
        }),
        ('Observaciones', {
            'fields': ('observaciones_auditoria',)
        }),
        ('Control', {
            'fields': ('fecha_auditoria', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related"""
        return super().get_queryset(request).select_related('venta', 'auditor')


@admin.register(GestionBackofficeTarjetaPlata)
class GestionBackofficeTarjetaPlataAdmin(admin.ModelAdmin):
    """Administración de gestiones del backoffice"""
    
    list_display = (
        'venta', 'estado_anterior', 'estado_nuevo', 
        'backoffice', 'fecha_gestion'
    )
    list_filter = ('estado_anterior', 'estado_nuevo', 'backoffice', 'fecha_gestion')
    search_fields = ('venta__id_preap', 'venta__nombre', 'comentario')
    date_hierarchy = 'fecha_gestion'
    ordering = ['-fecha_gestion']
    readonly_fields = ('fecha_gestion',)
    
    fieldsets = (
        ('Venta', {
            'fields': ('venta',)
        }),
        ('Cambio de Estado', {
            'fields': ('estado_anterior', 'estado_nuevo', 'backoffice')
        }),
        ('Comentario', {
            'fields': ('comentario',)
        }),
        ('Control', {
            'fields': ('fecha_gestion',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related"""
        return super().get_queryset(request).select_related('venta', 'backoffice')


# Configuración adicional del admin
admin.site.site_header = "CREA Online CRM - Administración"
admin.site.site_title = "CREA Online CRM"
admin.site.index_title = "Panel de Administración"
