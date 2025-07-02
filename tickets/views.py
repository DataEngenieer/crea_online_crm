from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from .models import Ticket, ArchivoAdjunto, RespuestaTicket
from .forms import TicketForm, RespuestaTicketForm

class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 15

    def get_queryset(self):
        # Obtener el parámetro de filtro de la URL (si existe)
        filtro = self.request.GET.get('filtro', 'abiertos')
        
        # Filtrar tickets según el parámetro
        if filtro == 'cerrados':
            queryset = Ticket.objects.filter(estado__in=[Ticket.Estado.CERRADO, Ticket.Estado.RESUELTO])
        else:  # Por defecto mostrar tickets abiertos/en progreso/pendientes
            queryset = Ticket.objects.exclude(estado__in=[Ticket.Estado.CERRADO, Ticket.Estado.RESUELTO])
        
        # Ordenar por fecha de creación (más recientes primero)
        return queryset.order_by('-fecha_creacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ticket_form'] = TicketForm()
        
        # Obtener el filtro actual
        context['filtro_actual'] = self.request.GET.get('filtro', 'abiertos')
        
        # Añadir conteo de tickets por estado para gráficos
        estado_counts = {
            'AB': Ticket.objects.filter(estado=Ticket.Estado.ABIERTO).count(),
            'EP': Ticket.objects.filter(estado=Ticket.Estado.EN_PROGRESO).count(),
            'PE': Ticket.objects.filter(estado=Ticket.Estado.PENDIENTE).count(),
            'RS': Ticket.objects.filter(estado=Ticket.Estado.RESUELTO).count(),
            'CE': Ticket.objects.filter(estado=Ticket.Estado.CERRADO).count(),
        }
        
        # Enviar datos para gráfico de barras de estados
        context['estados_count'] = [estado_counts['AB'], estado_counts['EP'], 
                                   estado_counts['PE'], estado_counts['RS'], 
                                   estado_counts['CE']]
        
        # Contadores para tarjetas de estadísticas
        context['tickets_abiertos'] = estado_counts['AB'] + estado_counts['EP']
        context['tickets_pendientes'] = estado_counts['PE']
        # Incluir tanto resueltos como cerrados en el contador de resueltos
        context['tickets_resueltos'] = estado_counts['RS'] + estado_counts['CE']
        context['tickets_cerrados'] = estado_counts['CE']
        
        # Añadir conteo de tickets por prioridad para gráfico circular
        context['prioridades_count'] = [
            Ticket.objects.filter(prioridad=Ticket.Prioridad.BAJA).count(),
            Ticket.objects.filter(prioridad=Ticket.Prioridad.MEDIA).count(),
            Ticket.objects.filter(prioridad=Ticket.Prioridad.ALTA).count(),
            Ticket.objects.filter(prioridad=Ticket.Prioridad.URGENTE).count(),
        ]
        
        return context

    def post(self, request, *args, **kwargs):
        ticket_form = TicketForm(request.POST, request.FILES)

        if ticket_form.is_valid():
            ticket = ticket_form.save(commit=False)
            ticket.solicitante = request.user
            ticket.save()

            # Obtener los archivos adjuntos del formulario
            # Usamos getlist para obtener todos los archivos con el mismo nombre
            files = request.FILES.getlist('archivos')
            for f in files:
                ArchivoAdjunto.objects.create(ticket=ticket, archivo=f)
            
            messages.success(request, 'Ticket creado correctamente.')
            return redirect('tickets:ticket_list')
        else:
            # Si el formulario no es válido, mostrar errores
            for field, errors in ticket_form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en {field}: {error}")
        
        # Si el formulario no es válido, se recarga la página mostrando los errores
        return self.get(request, *args, **kwargs)

class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['respuesta_form'] = RespuestaTicketForm()
        context['respuestas'] = self.object.respuestas.all().order_by('fecha_creacion')
        
        # Calcular tiempo de resolución si el ticket está resuelto
        if self.object.fecha_resolucion and self.object.tiempo_resolucion:
            total_seconds = self.object.tiempo_resolucion.total_seconds()
            context['horas_resolucion'] = int(total_seconds // 3600)
            context['minutos_resolucion'] = int((total_seconds % 3600) // 60)
            
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Verificar si el ticket está cerrado
        if self.object.estado == Ticket.Estado.CERRADO:
            messages.error(request, 'No se pueden añadir respuestas a un ticket cerrado.')
            return redirect('tickets:ticket_detail', pk=self.object.pk)
        
        respuesta_form = RespuestaTicketForm(request.POST)

        if respuesta_form.is_valid():
            respuesta = respuesta_form.save(commit=False)
            respuesta.ticket = self.object
            respuesta.autor = request.user
            respuesta.save()

            files = request.FILES.getlist('archivo')
            for f in files:
                ArchivoAdjunto.objects.create(respuesta=respuesta, ticket=self.object, archivo=f)

            self.object.save() # Para actualizar 'fecha_actualizacion'
            return redirect('tickets:ticket_detail', pk=self.object.pk)

        context = self.get_context_data()
        context['respuesta_form'] = respuesta_form
        return self.render_to_response(context)

@login_required
def cerrar_ticket(request, pk):
    """
    Vista para marcar un ticket como resuelto.
    """
    ticket = get_object_or_404(Ticket, pk=pk)
    
    if request.method == 'POST':
        # Verificar si el usuario tiene permisos para cerrar el ticket
        if not request.user.is_staff and ticket.asignado_a != request.user:
            messages.error(request, 'No tienes permiso para cerrar este ticket.')
            return redirect('tickets:ticket_detail', pk=ticket.pk)
        
        # Marcar el ticket como cerrado
        if not ticket.estado == Ticket.Estado.CERRADO:
            ticket.estado = Ticket.Estado.CERRADO
            ticket.fecha_cierre = timezone.now()
            ticket.save()
            messages.success(request, 'El ticket ha sido cerrado exitosamente.')
        else:
            messages.info(request, 'El ticket ya estaba cerrado.')
        
        return redirect('tickets:ticket_detail', pk=ticket.pk)
    
    # Si no es una petición POST, redirigir al detalle del ticket
    return redirect('tickets:ticket_detail', pk=ticket.pk)

@login_required
def reabrir_ticket(request, pk):
    """
    Vista para reabrir un ticket cerrado.
    """
    ticket = get_object_or_404(Ticket, pk=pk)
    
    # Verificar permisos
    if not (request.user.is_staff or request.user == ticket.solicitante or request.user == ticket.asignado):
        messages.error(request, 'No tienes permiso para reabrir este ticket.')
        return redirect('tickets:detalle_ticket', pk=ticket.pk)
    
    if request.method == 'POST':
        try:
            # Cambiar el estado a ABIERTO si estaba CERRADO o RESUELTO
            if ticket.estado in [Ticket.Estado.CERRADO, Ticket.Estado.RESUELTO]:
                ticket.estado = Ticket.Estado.ABIERTO
                ticket.fecha_cierre = None
                ticket.save()
                
                # Registrar la acción en el historial
                RespuestaTicket.objects.create(
                    ticket=ticket,
                    autor=request.user,
                    contenido=f'Ticket reabierto por {request.user.get_full_name() or request.user.username}.'
                )
                
                messages.success(request, 'El ticket ha sido reabierto correctamente.')
            else:
                messages.warning(request, 'El ticket ya está abierto o en progreso.')
                
        except Exception as e:
            messages.error(request, f'Error al reabrir el ticket: {str(e)}')
            
        return redirect('tickets:detalle_ticket', pk=ticket.pk)
    
    # Si no es una solicitud POST, redirigir al detalle del ticket
    return redirect('tickets:detalle_ticket', pk=ticket.pk)

@login_required
def cambiar_estado(request, pk, nuevo_estado):
    """
    Vista para cambiar el estado de un ticket.
    """
    ticket = get_object_or_404(Ticket, pk=pk)
    
    # Verificar permisos
    if not (request.user.is_staff or request.user == ticket.asignado):
        messages.error(request, 'No tienes permiso para cambiar el estado de este ticket.')
        return redirect('tickets:detalle_ticket', pk=ticket.pk)
    
    if request.method == 'POST':
        try:
            estado_anterior = ticket.get_estado_display()
            
            # Cambiar el estado según el parámetro
            if nuevo_estado == 'PE':  # Pendiente
                ticket.estado = Ticket.Estado.PENDIENTE
                mensaje = f'Estado cambiado a Pendiente por {request.user.get_full_name() or request.user.username}.'
                mensaje_exito = 'El ticket ha sido marcado como Pendiente.'
            elif nuevo_estado == 'CE':  # Cerrar
                ticket.estado = Ticket.Estado.CERRADO
                ticket.fecha_cierre = timezone.now()
                mensaje = f'Ticket cerrado por {request.user.get_full_name() or request.user.username}.'
                mensaje_exito = 'El ticket ha sido cerrado correctamente.'
            else:
                messages.error(request, 'Estado no válido.')
                return redirect('tickets:detalle_ticket', pk=ticket.pk)
            
            ticket.save()
            
            # Registrar la acción en el historial
            RespuestaTicket.objects.create(
                ticket=ticket,
                autor=request.user,
                contenido=mensaje
            )
            
            messages.success(request, mensaje_exito)
            
        except Exception as e:
            messages.error(request, f'Error al cambiar el estado del ticket: {str(e)}')
        
        return redirect('tickets:detalle_ticket', pk=ticket.pk)
    
    # Si no es una solicitud POST, redirigir al detalle del ticket
    return redirect('tickets:detalle_ticket', pk=ticket.pk)
