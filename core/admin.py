from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import LoginUser, Empleado, Cliente, Gestion

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
    list_display = ('created_user', 'id_user', 'tipo', 'ip')
    list_filter = ('tipo', 'created_user')

class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre_empleado', 'apellido_empleado', 'email_empleado', 'documento')
    search_fields = ('nombre_empleado', 'apellido_empleado', 'documento')

# Registrar modelos con sus configuraciones personalizadas
admin.site.register(LoginUser, LoginUserAdmin)
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Empleado, EmpleadoAdmin)
admin.site.register(Gestion, GestionAdmin)

# Personalizar el título del panel de administración
admin.site.site_header = 'CREA CRM - Panel de Administración'
admin.site.site_title = 'CREA CRM Admin'
admin.site.index_title = 'Panel de Control'