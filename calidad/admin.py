from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import MatrizCalidad, Auditoria, Speech, DetalleAuditoria, UsoProcesamientoAudio

User = get_user_model()


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'agente', 'fecha_llamada', 'tipo_monitoreo', 'evaluador')
    search_fields = ('id', 'agente__username', 'agente__first_name', 'agente__last_name')
    list_filter = ('tipo_monitoreo', 'evaluador')
    date_hierarchy = 'fecha_llamada'
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

@admin.register(Speech)
class SpeechAdmin(admin.ModelAdmin):
    list_display = ('id', 'auditoria', 'audio', 'transcripcion', 'fecha_creacion')
    search_fields = ('auditoria__id', 'audio')
    readonly_fields = ('fecha_creacion',)

@admin.register(UsoProcesamientoAudio)
class UsoProcesamientoAudioAdmin(admin.ModelAdmin):
    list_display = ('id', 'auditoria', 'speech', 'usuario', 'creado_en')
    list_filter = ('proveedor_transcripcion', 'proveedor_analisis')
    search_fields = ('auditoria__id', 'speech__id', 'usuario__username')
    readonly_fields = ('creado_en', 'actualizado_en')
    date_hierarchy = 'creado_en'


@admin.register(MatrizCalidad)
class MatrizCalidadAdmin(admin.ModelAdmin):
    list_display = ('indicador', 'categoria', 'tipologia', 'ponderacion', 'activo')
    list_filter = ('categoria', 'tipologia', 'activo')
    search_fields = ('indicador', 'categoria')
    list_editable = ('activo',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        ('Información Básica', {
            'fields': ('tipologia', 'categoria', 'indicador', 'ponderacion')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'activo'),
            'classes': ('collapse',)
        }),
    )
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.usuario_creacion = request.user
        super().save_model(request, obj, form, change)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(usuario_creacion=request.user)

@admin.register(DetalleAuditoria)
class DetalleAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('auditoria', 'indicador', 'get_speech', 'fecha_creacion')
    search_fields = ('auditoria__id', 'indicador')
    readonly_fields = ('fecha_creacion',)
    list_filter = ('auditoria', 'indicador')
    
    def get_speech(self, obj):
        if hasattr(obj.auditoria, 'speech'):
            return obj.auditoria.speech.id
        return "Sin speech"
    get_speech.short_description = 'Speech ID'
    