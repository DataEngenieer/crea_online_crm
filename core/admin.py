from django.contrib import admin
from .models import LoginUser, Empleado, Cliente


admin.site.register(LoginUser)
admin.site.register(Cliente)
admin.site.register(Empleado)