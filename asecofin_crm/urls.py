from django.contrib import admin
from django.urls import path, include
from django.conf.urls import handler404
from django.shortcuts import render

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('tickets/', include('tickets.urls')),
]

# Configuración de vistas de error personalizadas
def custom_404(request, exception):
    return render(request, '404.html', status=404)

handler404 = custom_404
