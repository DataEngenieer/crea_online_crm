from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls import handler404
from django.shortcuts import render
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('tickets/', include('tickets.urls')),
    path('chat/', include('chat.urls')),
]

# Configuración de vistas de error personalizadas
def custom_404(request, exception):
    return render(request, '404.html', status=404)

handler404 = custom_404

# Añadir la configuración para servir archivos multimedia en producción.
# Esta configuración permite que Django sirva los archivos multimedia directamente.
# Es una solución práctica para entornos como Railway donde no se configura un servidor web aparte para esta tarea.
if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})
    ]
