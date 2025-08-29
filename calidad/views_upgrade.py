from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

from .models_upgrade import AuditoriaUpgrade, DetalleAuditoriaUpgrade, MatrizCalidadUpgrade, RespuestaAuditoriaUpgrade
from .forms_upgrade import AuditoriaUpgradeForm, DetalleAuditoriaUpgradeFormSet, RespuestaAuditoriaUpgradeForm
from .models import Speech

User = get_user_model()

class AuditoriaUpgradeListView(LoginRequiredMixin, ListView):
    """
    Vista para listar auditorías de campaña Upgrade
    """
    model = AuditoriaUpgrade
    template_name = 'calidad/auditorias_upgrade/lista_auditorias_upgrade.html'
    context_object_name = 'auditorias'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = AuditoriaUpgrade.objects.select_related(
            'agente', 'evaluador'
        ).order_by('-fecha_llamada', '-fecha_creacion')
        
        # Filtros de búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(agente__first_name__icontains=search) |
                Q(agente__last_name__icontains=search) |
                Q(agente__username__icontains=search) |
                Q(numero_telefono__icontains=search)
            )
        
        # Filtro por agente
        agente_id = self.request.GET.get('agente')
        if agente_id:
            queryset = queryset.filter(agente_id=agente_id)
        
        # Filtro por evaluador
        evaluador_id = self.request.GET.get('evaluador')
        if evaluador_id:
            queryset = queryset.filter(evaluador_id=evaluador_id)
        
        # Filtro por fecha
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if fecha_desde:
            try:
                fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_llamada__gte=fecha_desde)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_llamada__lte=fecha_hasta)
            except ValueError:
                pass
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agregar listas para filtros
        context['agentes'] = User.objects.filter(
            auditorias_upgrade_recibidas__isnull=False
        ).distinct().order_by('first_name', 'last_name')
        
        context['evaluadores'] = User.objects.filter(
            auditorias_upgrade_realizadas__isnull=False
        ).distinct().order_by('first_name', 'last_name')
        
        # Mantener valores de filtros en el contexto
        context['search'] = self.request.GET.get('search', '')
        context['agente_selected'] = self.request.GET.get('agente', '')
        context['evaluador_selected'] = self.request.GET.get('evaluador', '')
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        
        # Estadísticas básicas
        total_auditorias = self.get_queryset().count()
        context['total_auditorias'] = total_auditorias
        
        if total_auditorias > 0:
            context['promedio_puntaje'] = self.get_queryset().aggregate(
                promedio=Avg('puntaje_total')
            )['promedio'] or 0
        else:
            context['promedio_puntaje'] = 0
        
        return context


class AuditoriaUpgradeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para crear nuevas auditorías de campaña Upgrade
    """
    model = AuditoriaUpgrade
    form_class = AuditoriaUpgradeForm
    template_name = 'calidad/auditorias_upgrade/crear_auditoria_upgrade.html'
    permission_required = 'calidad.add_auditoriaupgrade'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.evaluador = self.request.user
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener indicadores activos agrupados por tipología
        indicadores = MatrizCalidadUpgrade.objects.filter(activo=True).order_by(
            'categoria', 'indicador'
        )
        
        # Agrupar indicadores por tipología
        indicadores_por_tipologia = {}
        for indicador in indicadores:
            if indicador.categoria not in indicadores_por_tipologia:
                indicadores_por_tipologia[indicador.categoria] = []
            indicadores_por_tipologia[indicador.categoria].append(indicador)
        
        context['indicadores_por_tipologia'] = indicadores_por_tipologia
        
        return context
    
    def form_valid(self, form):
        form.instance.evaluador = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request, 
            f'Auditoría upgrade creada exitosamente para {form.instance.agente.get_full_name()}'
        )
        
        return response
    
    def get_success_url(self):
        return reverse('calidad:detalle_auditoria_upgrade', kwargs={'pk': self.object.pk})


class AuditoriaUpgradeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para editar auditorías de campaña Upgrade
    """
    model = AuditoriaUpgrade
    form_class = AuditoriaUpgradeForm
    template_name = 'calidad/auditorias_upgrade/editar_auditoria_upgrade.html'
    permission_required = 'calidad.change_auditoriaupgrade'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        messages.success(
            self.request, 
            f'Auditoría upgrade actualizada exitosamente'
        )
        
        return response
    
    def get_success_url(self):
        return reverse('calidad:detalle_auditoria_upgrade', kwargs={'pk': self.object.pk})


class AuditoriaUpgradeDetailView(LoginRequiredMixin, DetailView):
    """
    Vista para mostrar detalles de una auditoría de campaña Upgrade
    """
    model = AuditoriaUpgrade
    template_name = 'calidad/auditorias_upgrade/detalle_auditoria_upgrade.html'
    context_object_name = 'auditoria'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener detalles de la auditoría
        context['detalles'] = self.object.respuestas_upgrade.select_related(
            'indicador'
        ).order_by('indicador__categoria', 'indicador__indicador')
        
        # Obtener indicadores no cumplidos
        context['indicadores_no_cumplidos'] = self.object.get_indicadores_no_cumplidos()
        
        # Verificar si el usuario actual es el agente evaluado
        context['es_agente_evaluado'] = self.request.user == self.object.agente
        
        # Obtener respuestas del asesor si existen
        context['respuestas_asesor'] = RespuestaAuditoriaUpgrade.objects.filter(
            auditoria=self.object
        ).select_related('detalle_auditoria__indicador')
        
        return context


@login_required
@permission_required('calidad.add_detalleauditoriaupgrade')
def evaluar_auditoria_upgrade(request, pk):
    """
    Vista para evaluar los indicadores de una auditoría upgrade
    """
    auditoria = get_object_or_404(AuditoriaUpgrade, pk=pk)
    
    # Obtener todos los indicadores activos de upgrade
    indicadores = MatrizCalidadUpgrade.objects.filter(activo=True).order_by(
        'categoria', 'indicador'
    )
    
    if request.method == 'POST':
        # Procesar la evaluación
        for indicador in indicadores:
            cumple = request.POST.get(f'indicador_{indicador.id}') == 'on'
            observaciones = request.POST.get(f'observaciones_{indicador.id}', '')
            
            # Crear o actualizar el detalle de auditoría
            detalle, created = DetalleAuditoriaUpgrade.objects.get_or_create(
                auditoria=auditoria,
                indicador=indicador,
                defaults={
                    'cumple': cumple,
                    'observaciones': observaciones
                }
            )
            
            if not created:
                detalle.cumple = cumple
                detalle.observaciones = observaciones
                detalle.save()
        
        # Recalcular el puntaje total
        auditoria.calcular_puntaje_total()
        
        messages.success(request, 'Evaluación de auditoría upgrade guardada exitosamente')
        return redirect('calidad:detalle_auditoria_upgrade', pk=auditoria.pk)
    
    # Obtener evaluaciones existentes
    evaluaciones_existentes = {}
    for detalle in auditoria.respuestas_upgrade.all():
        evaluaciones_existentes[detalle.indicador.id] = {
            'cumple': detalle.cumple,
            'observaciones': detalle.observaciones
        }
    
    context = {
        'auditoria': auditoria,
        'indicadores': indicadores,
        'evaluaciones_existentes': evaluaciones_existentes,
    }
    
    return render(request, 'calidad/auditorias_upgrade/evaluar_auditoria_upgrade.html', context)


class MisAuditoriasUpgradeListView(LoginRequiredMixin, ListView):
    """
    Vista para que los asesores vean sus propias auditorías de upgrade
    """
    model = AuditoriaUpgrade
    template_name = 'calidad/auditorias_upgrade/mis_auditorias_upgrade.html'
    context_object_name = 'auditorias'
    paginate_by = 20
    
    def get_queryset(self):
        return AuditoriaUpgrade.objects.filter(
            agente=self.request.user
        ).select_related('evaluador').order_by('-fecha_llamada', '-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas del asesor
        auditorias_usuario = self.get_queryset()
        context['total_auditorias'] = auditorias_usuario.count()
        
        if context['total_auditorias'] > 0:
            context['promedio_puntaje'] = auditorias_usuario.aggregate(
                promedio=Avg('puntaje_total')
            )['promedio'] or 0
            
            # Auditorías con respuestas pendientes
            context['auditorias_pendientes'] = sum(
                1 for auditoria in auditorias_usuario if auditoria.tiene_respuestas_pendientes()
            )
        else:
            context['promedio_puntaje'] = 0
            context['auditorias_pendientes'] = 0
        
        return context


@login_required
def responder_auditoria_upgrade(request, pk, detalle_id):
    """
    Vista para que los asesores respondan a indicadores no cumplidos en auditorías upgrade
    """
    auditoria = get_object_or_404(AuditoriaUpgrade, pk=pk, agente=request.user)
    detalle = get_object_or_404(
        DetalleAuditoriaUpgrade, 
        pk=detalle_id, 
        auditoria=auditoria, 
        cumple=False
    )
    
    # Verificar si ya existe una respuesta
    try:
        respuesta = RespuestaAuditoriaUpgrade.objects.get(
            auditoria=auditoria,
            detalle_auditoria=detalle
        )
    except RespuestaAuditoriaUpgrade.DoesNotExist:
        respuesta = None
    
    if request.method == 'POST':
        form = RespuestaAuditoriaUpgradeForm(request.POST, instance=respuesta)
        if form.is_valid():
            respuesta = form.save(commit=False)
            respuesta.auditoria = auditoria
            respuesta.detalle_auditoria = detalle
            respuesta.asesor = request.user
            respuesta.save()
            
            messages.success(request, 'Respuesta guardada exitosamente')
            return redirect('calidad:detalle_auditoria_upgrade', pk=auditoria.pk)
    else:
        form = RespuestaAuditoriaUpgradeForm(instance=respuesta)
    
    context = {
        'auditoria': auditoria,
        'detalle': detalle,
        'form': form,
        'respuesta': respuesta,
    }
    
    return render(request, 'calidad/auditorias_upgrade/responder_auditoria_upgrade.html', context)


@login_required
def dashboard_upgrade(request):
    """
    Dashboard específico para auditorías de campaña Upgrade
    """
    # Estadísticas generales
    total_auditorias = AuditoriaUpgrade.objects.count()
    auditorias_mes_actual = AuditoriaUpgrade.objects.filter(
        fecha_creacion__month=timezone.now().month,
        fecha_creacion__year=timezone.now().year
    ).count()
    
    # Promedio de puntajes
    promedio_general = AuditoriaUpgrade.objects.aggregate(
        promedio=Avg('puntaje_total')
    )['promedio'] or 0
    
    # Auditorías recientes
    auditorias_recientes = AuditoriaUpgrade.objects.select_related(
        'agente', 'evaluador'
    ).order_by('-fecha_creacion')[:10]
    
    # Top agentes por puntaje
    from django.db.models import Avg, Count
    top_agentes = User.objects.filter(
        auditorias_upgrade_recibidas__isnull=False
    ).annotate(
        promedio_puntaje=Avg('auditorias_upgrade_recibidas__puntaje_total'),
        total_auditorias=Count('auditorias_upgrade_recibidas')
    ).filter(
        total_auditorias__gte=3  # Solo agentes con al menos 3 auditorías
    ).order_by('-promedio_puntaje')[:10]
    
    context = {
        'total_auditorias': total_auditorias,
        'auditorias_mes_actual': auditorias_mes_actual,
        'promedio_general': promedio_general,
        'auditorias_recientes': auditorias_recientes,
        'top_agentes': top_agentes,
        'tipo_campana': 'upgrade',
    }
    
    return render(request, 'calidad/dashboard_upgrade.html', context)


@login_required
def ajax_obtener_indicadores_upgrade(request):
    """
    Vista AJAX para obtener indicadores de upgrade por tipología
    """
    tipologia = request.GET.get('tipologia')
    
    if tipologia:
        indicadores = MatrizCalidadUpgrade.objects.filter(
            tipologia=tipologia,
            activo=True
        ).values('id', 'categoria', 'indicador', 'ponderacion')
    else:
        indicadores = MatrizCalidadUpgrade.objects.filter(
            activo=True
        ).values('id', 'categoria', 'indicador', 'ponderacion')
    
    return JsonResponse({
        'indicadores': list(indicadores)
    })