from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseRedirect
from django.http import HttpResponse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

from .models_upgrade import AuditoriaUpgrade, DetalleAuditoriaUpgrade, MatrizCalidadUpgrade, RespuestaAuditoriaUpgrade
from .forms_upgrade import AuditoriaUpgradeForm, DetalleAuditoriaUpgradeFormSet, RespuestaAuditoriaUpgradeForm
from .forms_speech import SpeechForm
from .utils.whixperx import transcribir_audio
from .utils.texto_de_speech import format_transcript_as_script
from .utils.analisis_de_calidad import AnalizadorTranscripciones, autocompletar_auditoria_upgrade_desde_analisis
from .utils.minio_utils import subir_a_minio
from .utils.audio_utils import obtener_duracion_audio, obtener_tamano_archivo_mb

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
                indicadores_por_tipologia[indicador.categoria] = {
                    'nombre': indicador.categoria,
                    'color': 'primary',
                    'indicadores': []
                }
            indicadores_por_tipologia[indicador.categoria]['indicadores'].append(indicador)
        
        context['indicadores_por_tipologia'] = indicadores_por_tipologia

        # Formulario de audio para Speech Analytics
        if self.request.method == 'POST':
            context['speech_form'] = SpeechForm(self.request.POST, self.request.FILES)
        else:
            context['speech_form'] = SpeechForm()
        
        return context
    
    def form_valid(self, form):
        form.instance.evaluador = self.request.user
        response = super().form_valid(form)
        
        # Pipeline de Speech Analytics para Upgrade
        tipo_monitoreo = form.cleaned_data.get('tipo_monitoreo')
        if tipo_monitoreo == 'speech':
            speech_form = SpeechForm(self.request.POST, self.request.FILES)
            if speech_form.is_valid() and self.request.FILES.get('audio'):
                audio_file = self.request.FILES.get('audio')
                import tempfile, os, requests
                temp_fd, temp_path = tempfile.mkstemp(suffix='.mp3', prefix=f'upgrade_{self.object.id}_')
                try:
                    with os.fdopen(temp_fd, 'wb') as tmp:
                        for chunk in audio_file.chunks():
                            tmp.write(chunk)

                    duracion = obtener_duracion_audio(temp_path)
                    tamano_mb = obtener_tamano_archivo_mb(temp_path)

                    audio_file.seek(0)
                    nombre_personalizado = f"auditoria_upgrade_{self.object.id}_audio"
                    resultado = subir_a_minio(
                        archivo=audio_file,
                        nombre_personalizado=nombre_personalizado,
                        carpeta="audios/upgrade",
                        bucket_type="MINIO_BUCKET_NAME_LLAMADAS"
                    )

                    if not resultado.get('success'):
                        messages.error(self.request, f"Error al subir a MinIO: {resultado.get('error', 'Error desconocido')}")
                    else:
                        self.object.minio_url = resultado['url']
                        self.object.minio_object_name = resultado['object_name']
                        self.object.subido_a_minio = True
                        self.object.duracion_segundos = duracion
                        self.object.tamano_archivo_mb = tamano_mb
                        self.object.save(update_fields=['minio_url','minio_object_name','subido_a_minio','duracion_segundos','tamano_archivo_mb'])

                        try:
                            dl_response = requests.get(self.object.minio_url, stream=True)
                            dl_response.raise_for_status()
                            temp_fd2, temp_path2 = tempfile.mkstemp(suffix='.mp3', prefix=f'upgrade_dl_{self.object.id}_')
                            with os.fdopen(temp_fd2, 'wb') as tmp2:
                                for chunk in dl_response.iter_content(chunk_size=8192):
                                    tmp2.write(chunk)

                            resultado_transcripcion = transcribir_audio(temp_path2)
                            prediccion = resultado_transcripcion
                            if isinstance(resultado_transcripcion, dict) and 'resultado' in resultado_transcripcion:
                                prediccion = resultado_transcripcion['resultado']

                            texto_formateado = format_transcript_as_script(prediccion)
                            if texto_formateado.startswith('[Error') or texto_formateado.startswith('[Advertencia]'):
                                texto_formateado = format_transcript_as_script(temp_path2)

                            if not texto_formateado or texto_formateado.strip() == '' or texto_formateado.startswith('[Error'):
                                messages.warning(self.request, 'Transcripción inválida, se omitió análisis de IA.')
                            else:
                                try:
                                    self.object.transcripcion = str(texto_formateado)
                                    self.object.save(update_fields=['transcripcion'])
                                except Exception:
                                    pass
                                analizador = AnalizadorTranscripciones(matriz_model=MatrizCalidadUpgrade)
                                analisis_resultado = analizador.evaluar_calidad_llamada(str(texto_formateado))
                                if 'error' in analisis_resultado:
                                    messages.error(self.request, f"Error en análisis de IA: {analisis_resultado['error']}")
                                else:
                                    autocompletar_auditoria_upgrade_desde_analisis(self.object, analisis_resultado)
                        finally:
                            try:
                                if 'temp_path2' in locals() and os.path.exists(temp_path2):
                                    os.unlink(temp_path2)
                            except Exception:
                                pass
                except Exception as e:
                    messages.error(self.request, f'Error procesando audio: {str(e)}')
                finally:
                    try:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                    except Exception:
                        pass

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
        
        detalles_qs = self.object.respuestas_upgrade.select_related('indicador').order_by(
            'indicador__categoria', 'indicador__indicador'
        )
        context['detalles'] = detalles_qs
        
        categorias = {}
        hay_incumplimientos = False
        estadisticas = {}
        for d in detalles_qs:
            cat = d.indicador.categoria
            if cat not in categorias:
                categorias[cat] = []
            puntaje_obtenido = d.indicador.ponderacion if d.cumple else 0
            categorias[cat].append({
                'indicador': d.indicador,
                'cumple': d.cumple,
                'observaciones': d.observaciones,
                'puntaje_obtenido': puntaje_obtenido,
            })
            if not d.cumple:
                hay_incumplimientos = True
            if cat not in estadisticas:
                estadisticas[cat] = {
                    'nombre': cat,
                    'cumplidos': 0,
                    'no_cumplidos': 0,
                    'puntos_perdidos': 0,
                }
            if d.cumple:
                estadisticas[cat]['cumplidos'] += 1
            else:
                estadisticas[cat]['no_cumplidos'] += 1
                try:
                    estadisticas[cat]['puntos_perdidos'] += float(d.indicador.ponderacion)
                except Exception:
                    pass
        
        context['categorias'] = categorias
        context['hay_incumplimientos'] = hay_incumplimientos
        context['estadisticas_tipologias'] = list(estadisticas.values())
        try:
            import json
            context['estadisticas_tipologias_json'] = json.dumps(context['estadisticas_tipologias'])
        except Exception:
            context['estadisticas_tipologias_json'] = '[]'
        
        context['es_agente_evaluado'] = self.request.user == self.object.agente
        context['respuestas_asesor'] = RespuestaAuditoriaUpgrade.objects.filter(
            auditoria=self.object
        ).select_related('detalle_auditoria__indicador')
        
        context['audio_url'] = self.object.minio_url if self.object.subido_a_minio and self.object.minio_url else None
        context['transcripcion'] = self.object.transcripcion
        
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


@login_required
def descargar_audio_upgrade(request, pk):
    auditoria = get_object_or_404(AuditoriaUpgrade, pk=pk)
    if not auditoria.subido_a_minio or not auditoria.minio_url:
        messages.error(request, 'No hay archivo de audio para descargar')
        return redirect('calidad:detalle_auditoria_upgrade', pk=auditoria.pk)
    try:
        import requests
        r = requests.get(auditoria.minio_url, stream=True)
        r.raise_for_status()
        response = HttpResponse(r.content, content_type='application/octet-stream')
        filename = auditoria.minio_object_name.split('/')[-1] if auditoria.minio_object_name else 'audio_upgrade.mp3'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f'Error al descargar el archivo: {str(e)}')
        return redirect('calidad:detalle_auditoria_upgrade', pk=auditoria.pk)
