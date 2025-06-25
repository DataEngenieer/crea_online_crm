from django.contrib import admin
from .models import Ticket, RespuestaTicket, ArchivoAdjunto

class ArchivoAdjuntoInline(admin.TabularInline):
    model = ArchivoAdjunto
    extra = 1
    fields = ('archivo', 'fecha_subida')
    readonly_fields = ('fecha_subida',)

class RespuestaTicketInline(admin.TabularInline):
    model = RespuestaTicket
    extra = 1
    fields = ('autor', 'mensaje', 'fecha_creacion')
    readonly_fields = ('fecha_creacion', 'autor')
    show_change_link = True

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'solicitante', 'estado', 'prioridad', 'tipo', 'fecha_creacion')
    list_filter = ('estado', 'prioridad', 'tipo', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion', 'solicitante__username', 'asignado_a__username')
    list_select_related = ('solicitante', 'asignado_a')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'fecha_resolucion', 'fecha_cierre', 'tiempo_resolucion')
    fieldsets = (
        ('Información Básica', {
            'fields': ('titulo', 'descripcion', 'solicitante', 'asignado_a')
        }),
        ('Estado y Prioridad', {
            'fields': ('estado', 'prioridad', 'tipo')
        }),
        ('Fechas Importantes', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'fecha_resolucion', 'fecha_cierre', 'tiempo_resolucion'),
            'classes': ('collapse',)
        }),
    )
    inlines = [RespuestaTicketInline, ArchivoAdjuntoInline]
    actions = ['marcar_como_resuelto', 'marcar_como_cerrado']

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Solo si es un nuevo ticket
            obj.solicitante = request.user
        super().save_model(request, obj, form, change)

    def marcar_como_resuelto(self, request, queryset):
        updated = queryset.update(estado=Ticket.Estado.RESUELTO)
        self.message_user(request, f"{updated} ticket(s) marcado(s) como resuelto(s).")
    marcar_como_resuelto.short_description = "Marcar como resuelto"

    def marcar_como_cerrado(self, request, queryset):
        updated = queryset.update(estado=Ticket.Estado.CERRADO)
        self.message_user(request, f"{updated} ticket(s) marcado(s) como cerrado(s).")
    marcar_como_cerrado.short_description = "Marcar como cerrado"

@admin.register(RespuestaTicket)
class RespuestaTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'autor', 'fecha_creacion')
    list_filter = ('fecha_creacion', 'autor')
    search_fields = ('mensaje', 'ticket__titulo', 'autor__username')
    list_select_related = ('ticket', 'autor')
    readonly_fields = ('fecha_creacion', 'autor')
    inlines = [ArchivoAdjuntoInline]

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Solo si es una nueva respuesta
            obj.autor = request.user
        super().save_model(request, obj, form, change)

@admin.register(ArchivoAdjunto)
class ArchivoAdjuntoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_archivo', 'ticket', 'respuesta', 'fecha_subida')
    list_filter = ('fecha_subida',)
    search_fields = ('archivo', 'ticket__titulo')
    list_select_related = ('ticket', 'respuesta')
    readonly_fields = ('fecha_subida', 'nombre_archivo')
    date_hierarchy = 'fecha_subida'

    def nombre_archivo(self, obj):
        return obj.archivo.name.split('/')[-1]
    nombre_archivo.short_description = 'Nombre del archivo'
