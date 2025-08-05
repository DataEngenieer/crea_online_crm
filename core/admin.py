from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import LoginUser, Empleado, Cliente, Gestion, AcuerdoPago, CuotaAcuerdo, Campana, UsuariosPlataformas, IPPermitida, RegistroAccesoIP

# Personalizar el panel de administración
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('documento', 'nombre_completo', 'email', 'ciudad', 'deuda_total', 'fecha_registro')
    search_fields = ('documento', 'nombre_completo', 'email')
    list_filter = ('estado', 'ciudad', 'fecha_registro')
    date_hierarchy = 'fecha_registro'

class GestionAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'usuario_gestion', 'canal_contacto', 'estado_contacto', 'fecha_hora_gestion')
    list_filter = ('canal_contacto', 'estado_contacto', 'usuario_gestion', 'acuerdo_pago_realizado', 'seguimiento_requerido')
    search_fields = ('cliente__nombre_completo', 'cliente__documento', 'observaciones_generales')
    date_hierarchy = 'fecha_hora_gestion'

class LoginUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo', 'ip', 'fecha')
    list_filter = ('tipo', 'fecha')

class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre_empleado', 'apellido_empleado', 'email_empleado', 'documento')
    search_fields = ('nombre_empleado', 'apellido_empleado', 'documento')

# Configuración para los nuevos modelos
class CuotaAcuerdoInline(admin.TabularInline):
    model = CuotaAcuerdo
    extra = 1

class AcuerdoPagoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'fecha_acuerdo', 'monto_total', 'numero_cuotas', 'estado', 'tipo_acuerdo')
    list_filter = ('estado', 'tipo_acuerdo', 'fecha_acuerdo')
    search_fields = ('cliente__nombre_completo', 'cliente__documento', 'observaciones')
    date_hierarchy = 'fecha_acuerdo'
    inlines = [CuotaAcuerdoInline]

class CuotaAcuerdoAdmin(admin.ModelAdmin):
    list_display = ('acuerdo', 'numero_cuota', 'monto', 'fecha_vencimiento', 'fecha_pago', 'estado')
    list_filter = ('estado', 'fecha_vencimiento')
    search_fields = ('acuerdo__cliente__nombre_completo', 'observaciones')
    date_hierarchy = 'fecha_vencimiento'

# Clase para administrar las campañas
class CampanaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'modulo', 'activa', 'fecha_creacion')
    list_filter = ('modulo', 'activa')
    search_fields = ('nombre', 'codigo', 'descripcion')
    date_hierarchy = 'fecha_creacion'
    filter_horizontal = ('usuarios',)  # Permite seleccionar múltiples usuarios de manera más amigable

# Clase para administrar UsuariosPlataformas
class UsuariosPlataformasAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'usuario_greta', 'fecha_creacion', 'fecha_actualizacion')
    search_fields = ('usuario__username', 'usuario__email', 'usuario_greta')
    list_filter = ('fecha_creacion', 'fecha_actualizacion')
    date_hierarchy = 'fecha_creacion'


class IPPermitidaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para gestionar las IPs permitidas.
    """
    list_display = ('ip_address', 'descripcion', 'activa', 'usuario_creacion', 'ultimo_acceso', 'fecha_creacion')
    list_filter = ('activa', 'fecha_creacion', 'ultimo_acceso')
    search_fields = ('ip_address', 'descripcion')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'ultimo_acceso')
    
    def save_model(self, request, obj, form, change):
        """
        Asignar automáticamente el usuario que crea la IP permitida.
        """
        if not change:  # Solo al crear, no al editar
            obj.usuario_creacion = request.user
        super().save_model(request, obj, form, change)


class RegistroAccesoIPAdmin(admin.ModelAdmin):
    """
    Configuración del admin para ver los registros de acceso por IP.
    """
    list_display = ('ip_address', 'usuario', 'tipo_acceso', 'pais', 'ciudad', 'isp', 'es_vpn', 'es_proxy', 'puntuacion_riesgo', 'fecha_acceso')
    list_filter = ('tipo_acceso', 'es_vpn', 'es_proxy', 'pais', 'fecha_acceso')
    search_fields = ('ip_address', 'usuario__username', 'ciudad', 'isp')
    date_hierarchy = 'fecha_acceso'
    readonly_fields = ('usuario', 'ip_address', 'tipo_acceso', 'user_agent', 'pais', 'ciudad', 'isp', 'es_vpn', 'es_proxy', 'puntuacion_riesgo', 'fecha_acceso')
    
    def has_add_permission(self, request):
        """
        No permitir agregar registros manualmente, solo se crean automáticamente.
        """
        return False
    
    def has_change_permission(self, request, obj=None):
        """
        No permitir editar registros, solo visualización.
        """
        return False

# Registrar los modelos en el admin
admin.site.register(LoginUser, LoginUserAdmin)
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Empleado, EmpleadoAdmin)
admin.site.register(Gestion, GestionAdmin)
admin.site.register(AcuerdoPago, AcuerdoPagoAdmin)
admin.site.register(CuotaAcuerdo, CuotaAcuerdoAdmin)
admin.site.register(Campana, CampanaAdmin)
admin.site.register(UsuariosPlataformas, UsuariosPlataformasAdmin)
admin.site.register(IPPermitida, IPPermitidaAdmin)
admin.site.register(RegistroAccesoIP, RegistroAccesoIPAdmin)

# Personalizar el título del panel de administración
admin.site.site_header = 'CREA CRM - Panel de Administración'
admin.site.site_title = 'CREA CRM Admin'
admin.site.index_title = 'Panel de Control'