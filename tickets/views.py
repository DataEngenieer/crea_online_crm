from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Ticket, ArchivoAdjunto
from .forms import TicketForm, RespuestaTicketForm

class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ticket_form'] = TicketForm()
        return context

    def post(self, request, *args, **kwargs):
        ticket_form = TicketForm(request.POST)

        if ticket_form.is_valid():
            ticket = ticket_form.save(commit=False)
            ticket.solicitante = request.user
            ticket.save()

            files = request.FILES.getlist('archivos')  # Cambiado de 'archivo' a 'archivos'
            for f in files:
                ArchivoAdjunto.objects.create(ticket=ticket, archivo=f)
            
            return redirect('tickets:ticket_list')
        
        # Si el formulario no es válido, se recarga la página mostrando los errores.
        # Esto es una simplificación. Una implementación más robusta usaría AJAX.
        return self.get(request, *args, **kwargs)

class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['respuesta_form'] = RespuestaTicketForm()
        context['respuestas'] = self.object.respuestas.all().order_by('fecha_creacion')
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
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
