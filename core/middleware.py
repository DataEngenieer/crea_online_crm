from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse, resolve

from django.utils.deprecation import MiddlewareMixin
import re

EXEMPT_URLS = [
    re.compile(r'^' + reverse('core:login').lstrip('/')),
    re.compile(r'^' + reverse('core:logout').lstrip('/')),
    re.compile(r'^' + reverse('core:password_reset').lstrip('/')),
    re.compile(r'^' + reverse('core:password_reset_done').lstrip('/')),
    re.compile(r'^' + reverse('core:registro').lstrip('/')),
    re.compile(r'^static/'),
    re.compile(r'^media/'),
]

class LoginRequiredMiddleware(MiddlewareMixin):
    def process_request(self, request):
        path = request.path_info.lstrip('/')
        # Si el usuario autenticado intenta acceder a /login/, redirigir a inicio
        if request.user.is_authenticated and re.match(r'^' + reverse('core:login').lstrip('/'), path):
            return redirect(reverse('core:inicio'))
        # Permitir acceso a URLs exentas (login, logout, password reset, static, media)
        if any(m.match(path) for m in EXEMPT_URLS):
            return None
        if not request.user.is_authenticated:
            return redirect(f"{reverse('core:login')}?next={request.path}")
        return None
