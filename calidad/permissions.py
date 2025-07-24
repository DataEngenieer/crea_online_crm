# calidad/permissions.py
from rest_framework import permissions

class EsMiembroEquipoCalidad(permissions.BasePermission):
    """
    Permiso personalizado que solo permite el acceso a miembros del equipo de calidad.
    """
    def has_permission(self, request, view):
        # Verificar si el usuario pertenece al grupo 'Calidad' o es superusuario
        return (
            request.user and 
            (request.user.groups.filter(name='Calidad').exists() or request.user.is_superuser)
        )

class EsResponsableProyecto(permissions.BasePermission):
    """
    Permiso que solo permite al responsable del proyecto realizar ciertas acciones.
    """
    def has_object_permission(self, request, view, obj):
        # Solo el responsable del proyecto puede editar/eliminar
        return obj.responsable == request.user

class EsAsignadoTarea(permissions.BasePermission):
    """
    Permiso que solo permite al usuario asignado a la tarea ver/editar.
    """
    def has_object_permission(self, request, view, obj):
        # El asignado, el creador o un superusuario pueden ver/editar
        return (
            obj.asignado_a == request.user or 
            obj.creado_por == request.user or 
            request.user.is_superuser
        )