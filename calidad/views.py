import json
import os
import threading
import logging
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.http import Http404, JsonResponse, HttpResponseForbidden, HttpResponse
from django.conf import settings
from django.db.models import Q, Sum, Count, F, Value, Avg, IntegerField, FloatField
from django.db.models.functions import Coalesce, TruncMonth
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_http_methods

from .models import MatrizCalidad, Auditoria, DetalleAuditoria, Speech, RespuestaAuditoria
from .models_prepago import AuditoriaPrepago, MatrizCalidadPrepago
from .models_upgrade import AuditoriaUpgrade, MatrizCalidadUpgrade
from .forms_speech import MatrizCalidadForm, SpeechForm
from .forms_auditoria import AuditoriaForm, RespuestaAuditoriaForm
from .forms_prepago import MatrizCalidadPrepagoForm
from .forms_upgrade import MatrizCalidadUpgradeForm
from .decorators import grupo_requerido, ip_permitida
from .utils.whixperx import transcribir_audio
from .utils.texto_de_speech import format_transcript_as_script
from .utils.analisis_de_calidad import AnalizadorTranscripciones, autocompletar_auditoria_desde_analisis

# Constantes
ITEMS_POR_PAGINA = 20

# Clases base para las vistas
class CalidadBaseView(LoginRequiredMixin, UserPassesTestMixin):
    """
    Vista base para el módulo de calidad
    """
    login_url = '/login/'
    permission_denied_message = 'No tiene permisos para acceder a esta sección.'
    
    def test_func(self):
        """
        Verifica que el usuario pertenezca al grupo de Calidad o sea administrador
        """
        # Verificación case-insensitive para mayor compatibilidad
        return (self.request.user.groups.filter(name__iexact='Calidad').exists() or 
                self.request.user.groups.filter(name__iexact='Administrador').exists())
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, self.permission_denied_message)
        return redirect('core:inicio')

@login_required
@ip_permitida
@grupo_requerido('Administrador', 'Calidad')
def dashboard_calidad(request):
    # 1. Obtener parámetros de filtro de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # 2. Obtener todas las auditorías base con filtros aplicados
    auditorias = Auditoria.objects.all()
    
    # Aplicar filtros de fecha si se proporcionan
    if fecha_inicio:
        try:
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            auditorias = auditorias.filter(fecha_llamada__gte=fecha_inicio_obj)
        except ValueError:
            # Si el formato de fecha es incorrecto, ignorar el filtro
            pass
    
    if fecha_fin:
        try:
            fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            auditorias = auditorias.filter(fecha_llamada__lte=fecha_fin_obj)
        except ValueError:
            # Si el formato de fecha es incorrecto, ignorar el filtro
            pass
    
    auditorias_manuales = auditorias.filter(speech__isnull=True)
    auditorias_ia = auditorias.filter(speech__isnull=False)

    # 2. KPIs Principales
    total_auditorias = auditorias.count()
    total_auditorias_manuales = auditorias_manuales.count()
    total_auditorias_ia = auditorias_ia.count()

    # Usar Cast para asegurar que el promedio sea float
    from django.db.models.functions import Cast
    from django.db.models import FloatField
    
    # Calcular promedio manual con conversión explícita a float
    promedio_manual_result = auditorias_manuales.aggregate(
        avg=Avg(Cast('puntaje_total', output_field=FloatField()))
    )
    promedio_manual = float(promedio_manual_result['avg'] or 0)

    # Calcular IA
    puntajes_ia = []
    for aud in auditorias_ia.exclude(puntaje_ia__isnull=True).exclude(puntaje_ia__exact=''):
        if aud.puntaje_ia:
            try:
                valor = str(aud.puntaje_ia).replace('%', '').strip()
                if valor.replace('.', '', 1).isdigit():
                    puntajes_ia.append(float(valor))
            except (ValueError, AttributeError):
                continue
    promedio_ia = float(round(sum(puntajes_ia) / len(puntajes_ia), 2)) if puntajes_ia else 0.0

    if total_auditorias > 0:
        promedio_general = (float(promedio_manual) * total_auditorias_manuales + promedio_ia * total_auditorias_ia) / total_auditorias
    else:
        promedio_general = 0

    # 3. Calcular total de asesores únicos evaluados
    total_asesores_evaluados = User.objects.annotate(
        total_auditorias=Count('auditorias_recibidas')
    ).filter(total_auditorias__gt=0).count()
    
    # 4. Ranking de Asesores (Top 5)
    # Primero obtenemos todos los asesores con auditorías
    asesores_candidatos = User.objects.annotate(
        total_auditorias=Count('auditorias_recibidas'),
        promedio_puntaje=Coalesce(
            Avg(Cast('auditorias_recibidas__puntaje_total', output_field=FloatField())), 
            Value(0.0, output_field=FloatField())
        )
    ).filter(total_auditorias__gt=0)

    # Función para convertir valores de IA a porcentaje 0-100
    def _parse_ia(val):
        """Convierte valores de IA a un porcentaje 0-100"""
        try:
            score_str = str(val).replace('%', '').strip()
            if score_str.replace('.', '', 1).isdigit():
                score = float(score_str)
                # Si viene en escala 0-1 lo convertimos a 0-100
                if score <= 1:
                    score *= 100
                return score
        except Exception:
            pass
        return None

    # Calcular el puntaje real que se mostrará para cada asesor
    asesores_con_puntaje = []
    for asesor in asesores_candidatos:
        auditorias_speech = asesor.auditorias_recibidas.filter(speech__isnull=False)
        if auditorias_speech.exists():
            valores = []
            for aud in auditorias_speech.exclude(puntaje_ia__isnull=True).exclude(puntaje_ia__exact=''):
                v = _parse_ia(aud.puntaje_ia)
                if v is not None:
                    valores.append(v)
            asesor.puntaje_mostrar = round(sum(valores) / len(valores), 1) if valores else 0.0
        else:
            asesor.puntaje_mostrar = round(float(asesor.promedio_puntaje or 0.0), 1)
        asesores_con_puntaje.append(asesor)
    
    # Ordenar por puntaje_mostrar de mayor a menor y tomar los top 5
    ranking_asesores = sorted(asesores_con_puntaje, key=lambda x: (x.puntaje_mostrar, x.total_auditorias), reverse=True)[:5]

    # 5. Datos para Gráfico de Incumplimientos (Top 5)
    top_incumplimientos = DetalleAuditoria.objects.filter(cumple=False) \
        .values('indicador__indicador') \
        .annotate(total=Count('id')) \
        .order_by('-total')[:5]
    top_incumplimientos_labels = [item['indicador__indicador'] for item in top_incumplimientos]
    top_incumplimientos_data = [item['total'] for item in top_incumplimientos]

    # 6. Datos para Gráfico de Tipologías (Solo incumplimientos)
    tipologias_data = DetalleAuditoria.objects.filter(cumple=False).values('indicador__tipologia') \
        .annotate(total=Count('id')).order_by('-total')
    tipologias_labels = [item['indicador__tipologia'] for item in tipologias_data if item['indicador__tipologia']]
    tipologias_values = [item['total'] for item in tipologias_data if item['indicador__tipologia']]

    # 7. Datos para Gráfico de Evolución Mensual (Dinámico)
    current_year = datetime.now().year
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    # Evolución manual
    from django.db.models import FloatField
    from django.db.models.functions import Cast
    
    evolucion_manual = auditorias_manuales.filter(fecha_llamada__year=current_year) \
        .annotate(month=TruncMonth('fecha_llamada')) \
        .values('month') \
        .annotate(avg_score=Avg(Cast('puntaje_total', output_field=FloatField()))) \
        .order_by('month')
    data_manual_dict = {item['month'].month: float(item['avg_score']) if item['avg_score'] is not None else 0.0 for item in evolucion_manual}
    data_manual = [round(data_manual_dict.get(i, 0.0), 2) for i in range(1, 13)]

    # Evolución IA
    evolucion_ia_raw = auditorias_ia.filter(fecha_llamada__year=current_year) \
        .exclude(puntaje_ia__isnull=True).exclude(puntaje_ia__exact='') \
        .values('fecha_llamada', 'puntaje_ia')
    
    # Procesar puntuaciones de IA
    ia_scores_by_month = {i: [] for i in range(1, 13)}
    for aud in evolucion_ia_raw:
        try:
            # Convertir el porcentaje a valor numérico (ej: '85%' -> 0.85)
            score_str = str(aud['puntaje_ia']).replace('%', '').strip()
            if score_str.replace('.', '', 1).isdigit():
                score = float(score_str) / 100.0  # Convertir a decimal (ej: 85 -> 0.85)
                ia_scores_by_month[aud['fecha_llamada'].month].append(score)
        except (ValueError, TypeError, AttributeError):
            continue
    
    # Calcular promedios mensuales, asegurando que sean valores flotantes
    data_ia = [float(round(sum(scores) / len(scores), 4)) if scores else 0.0 for scores in ia_scores_by_month.values()]

    # 8. Preparar contexto para la plantilla
    # Asegurarse de que todos los valores numéricos sean compatibles con JSON
    promedio_general_float = float(round(promedio_general, 2)) if promedio_general is not None else 0.0
    promedio_manual_float = float(round(promedio_manual, 2)) if promedio_manual is not None else 0.0
    promedio_ia_float = float(promedio_ia) if promedio_ia is not None else 0.0
    
    context = {
        'titulo': 'Dashboard de Calidad',
        'subtitulo': 'Análisis de rendimiento y tendencias',
        'total_auditorias': int(total_auditorias),
        'total_auditorias_manuales': int(total_auditorias_manuales),
        'total_auditorias_ia': int(total_auditorias_ia),
        'promedio_general': promedio_general_float,
        'promedio_manual': promedio_manual_float,
        'promedio_ia': promedio_ia_float,
        'total_asesores_evaluados': int(total_asesores_evaluados),
        'ranking_asesores': ranking_asesores,
        'top_incumplimientos_labels': json.dumps(top_incumplimientos_labels, default=str),
        'top_incumplimientos_data': json.dumps(top_incumplimientos_data, default=str),
        'tipologias_labels': json.dumps(tipologias_labels, default=str),
        'tipologias_values': json.dumps(tipologias_values, default=str),
        'meses': json.dumps(meses, default=str),
        'data_manual': json.dumps([float(x) if x is not None else 0.0 for x in data_manual], default=str),
        'data_ia': json.dumps([float(x) if x is not None else 0.0 for x in data_ia], default=str),
        # Agregar valores de filtro para mantener estado en el frontend
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'calidad/dashboard.html', context)




@login_required
@ip_permitida
@grupo_requerido('Administrador', 'Calidad')
def lista_matriz_calidad(request):
    # Obtener el filtro de tipología si existe
    tipologia_filtro = request.GET.get('tipologia', '')
    
    # Obtener el filtro de mostrar inactivos
    mostrar_inactivos = request.GET.get('mostrar_inactivos', '') == 'true'
    
    # Obtener todos los indicadores ordenados por tipología, categoría e indicador
    matriz_list = MatrizCalidad.objects.all().order_by('tipologia', 'categoria', 'indicador')
    
    # Aplicar filtro de tipología si se especificó
    if tipologia_filtro in dict(MatrizCalidad.TIPOLOGIA_CHOICES).keys():
        matriz_list = matriz_list.filter(tipologia=tipologia_filtro)
    
    # Aplicar filtro de activos/inactivos
    if not mostrar_inactivos:
        matriz_list = matriz_list.filter(activo=True)
    
    # Agrupar indicadores por tipología
    indicadores_por_tipologia = {}
    for tipologia in dict(MatrizCalidad.TIPOLOGIA_CHOICES).keys():
        indicadores_por_tipologia[tipologia] = {
            'nombre': dict(MatrizCalidad.TIPOLOGIA_CHOICES)[tipologia],
            'indicadores': matriz_list.filter(tipologia=tipologia)
        }
    
    # Pasar el contexto a la plantilla
    context = {
        'indicadores_por_tipologia': indicadores_por_tipologia,
        'tipologia_actual': tipologia_filtro,
        'TIPOLOGIA_CHOICES': MatrizCalidad.TIPOLOGIA_CHOICES,
        'mostrar_inactivos': mostrar_inactivos,
    }
    return render(request, 'calidad/matriz/lista_matriz.html', context)

@login_required
@ip_permitida
@grupo_requerido('Administrador', 'Calidad')
def crear_editar_matriz(request, id=None):
    if id:
        matriz = get_object_or_404(MatrizCalidad, id=id)
        titulo = 'Editar Indicador'
        mensaje_exito = 'Indicador actualizado correctamente'
        es_edicion = True
    else:
        matriz = None
        titulo = 'Nuevo Indicador'
        mensaje_exito = 'Indicador creado correctamente'
        es_edicion = False

    if es_edicion and not request.user.has_perm('calidad.change_matrizcalidad'):
        messages.error(request, 'No tiene permisos para editar indicadores')
        return redirect('calidad:lista_matriz')
    elif not es_edicion and not request.user.has_perm('calidad.add_matrizcalidad'):
        messages.error(request, 'No tiene permisos para crear indicadores')
        return redirect('calidad:lista_matriz')

    if request.method == 'POST':
        form = MatrizCalidadForm(request.POST, instance=matriz)
        if form.is_valid():
            indicador = form.save(commit=False)
            if not es_edicion:
                indicador.usuario_creacion = request.user
            indicador.save()
            messages.success(request, mensaje_exito)
            if 'guardar_y_agregar_otro' in request.POST:
                return redirect('calidad:crear_editar_matriz')
            return redirect('calidad:lista_matriz')
    else:
        form = MatrizCalidadForm(instance=matriz)

    context = {
        'form': form,
        'es_edicion': es_edicion,
        'titulo': titulo,
        'subtitulo': 'Complete los datos del indicador',
    }
    return render(request, 'calidad/matriz/form_matriz.html', context)

@login_required
@ip_permitida
@grupo_requerido('Administrador', 'Calidad')
def activar_desactivar_matriz(request, id):
    matriz = get_object_or_404(MatrizCalidad, id=id)
    matriz.activo = not matriz.activo
    matriz.save()
    messages.success(request, f'Indicador {"activado" if matriz.activo else "desactivado"} correctamente.')
    return redirect('calidad:lista_matriz')

@login_required
@ip_permitida
@grupo_requerido('Administrador', 'Calidad')
def toggle_matriz_activo(request, id):
    matriz = get_object_or_404(MatrizCalidad, id=id)
    matriz.activo = not matriz.activo
    matriz.save()
    
    # Si es una petición AJAX, devolver respuesta JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'activo': matriz.activo
        })
    
    return redirect('calidad:lista_matriz')











# ============================================
# Vistas para el módulo de Auditorías de Calidad
# ============================================

class AuditoriaListView(CalidadBaseView, ListView):
    """
    Vista para listar todas las auditorías
    """
    model = Auditoria
    template_name = 'calidad/auditorias/lista_auditorias.html'
    context_object_name = 'auditorias'
    paginate_by = ITEMS_POR_PAGINA
    
    def get_queryset(self):
        queryset = Auditoria.objects.select_related('agente', 'evaluador', 'speech').all()
        
        # Obtener parámetros de filtrado
        params = self.request.GET.copy()
        
        # Filtro de búsqueda general
        busqueda = params.get('busqueda', '').strip()
        if busqueda:
            queryset = queryset.filter(
                Q(agente__first_name__icontains=busqueda) |
                Q(agente__last_name__icontains=busqueda) |
                Q(evaluador__first_name__icontains=busqueda) |
                Q(evaluador__last_name__icontains=busqueda) |
                Q(numero_telefono__icontains=busqueda) |
                Q(observaciones__icontains=busqueda)
            )
        
        # Filtro por agente
        if 'agente' in params and params['agente']:
            queryset = queryset.filter(agente_id=params['agente'])
            
        # Filtro por evaluador
        if 'evaluador' in params and params['evaluador']:
            queryset = queryset.filter(evaluador_id=params['evaluador'])
            
        # Filtro por tipo de llamada/campaña
        if 'tipo_campana' in params and params['tipo_campana']:
            queryset = queryset.filter(speech__tipo_campana=params['tipo_campana'])
            
        # Filtros por área y sede eliminados
            
        # Filtro por fecha
        if 'fecha_inicio' in params and params['fecha_inicio']:
            queryset = queryset.filter(fecha_llamada__date__gte=params['fecha_inicio'])
            
        if 'fecha_fin' in params and params['fecha_fin']:
            # Añadir 1 día para incluir el día completo
            from datetime import datetime, timedelta
            fecha_fin = datetime.strptime(params['fecha_fin'], '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(fecha_llamada__date__lt=fecha_fin)
            
        # Ordenamiento
        orden = params.get('orden', '-fecha_llamada')
        
        # Validar que el campo de ordenamiento sea seguro
        campos_validos = [
            'fecha_llamada', '-fecha_llamada',
            'fecha_creacion', '-fecha_creacion', 
            'agente__first_name', '-agente__first_name',
            'agente__last_name', '-agente__last_name',
            'puntaje_total', '-puntaje_total',
            'evaluador__first_name', '-evaluador__first_name',
            'evaluador__last_name', '-evaluador__last_name',
            # Campos area y sede eliminados del ordenamiento
            'tipo_monitoreo', '-tipo_monitoreo'
        ]
        
        if orden in campos_validos:
            queryset = queryset.order_by(orden)
        else:
            queryset = queryset.order_by('-fecha_llamada')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Auditorías de Calidad'
        context['subtitulo'] = 'Listado de auditorías realizadas'
        
        # Obtener agentes que han sido evaluados
        context['agentes'] = User.objects.filter(
            auditorias_recibidas__isnull=False
        ).distinct().order_by('first_name', 'last_name')
        
        # Obtener evaluadores (solo del grupo Calidad)
        context['evaluadores'] = User.objects.filter(
            groups__name='Calidad',
            is_active=True
        ).order_by('first_name', 'last_name')
        
        # Opciones de filtro eliminadas - los campos area y sede fueron removidos del modelo
        
        # Obtener tipos de campaña disponibles desde el modelo Speech
        from .models import Speech
        context['tipos_campana'] = Speech.TIPO_CAMPANA_CHOICES
        
        # Mantener los parámetros de filtro en el contexto
        context['filtros'] = {}
        for param in ['agente', 'evaluador', 'tipo_campana', 'fecha_inicio', 'fecha_fin', 'orden']:
            if param in self.request.GET:
                context['filtros'][param] = self.request.GET[param]
        
        # Pasar el parámetro de ordenamiento al contexto
        context['orden_filtro'] = self.request.GET.get('orden', '-fecha_llamada')
        
        # Calcular total de auditorías filtradas
        context['total_auditorias'] = self.get_queryset().count()
        
        return context


class AuditoriaCreateView(CalidadBaseView, CreateView):
    """
    Vista para crear una nueva auditoría
    """
    model = Auditoria
    form_class = AuditoriaForm
    template_name = 'calidad/auditorias/form_auditoria.html'
    success_url = reverse_lazy('calidad:lista_auditorias')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nueva Auditoría de Calidad'
        context['submit_text'] = 'Guardar Auditoría'
        
        # SpeechForm para carga de audio
        if self.request.method == 'POST':
            context['speech_form'] = SpeechForm(self.request.POST, self.request.FILES)
        else:
            context['speech_form'] = SpeechForm()
        
        # Obtener indicadores activos agrupados por tipología
        indicadores = MatrizCalidad.objects.filter(activo=True).order_by('categoria', 'id')
        
        # Definir clases CSS corporativas para cada tipología (sincronizado con TIPOLOGIA_CHOICES del modelo)
        colores_tipologias = {
            'ECUF': 'tipologia-atencion',  # Azul índigo corporativo (#7478BC)
            'ECN': 'tipologia-ofrecimiento',  # Magenta principal corporativo (#BB2BA3)
            'Estadistico': 'tipologia-proceso'  # Azul oscuro corporativo (#34387C)
        }
        
        # Definir el orden específico de las tipologías (basado en TIPOLOGIA_CHOICES)
        orden_tipologias = ['ECUF', 'ECN', 'Estadistico']
        
        # Usar OrderedDict para mantener el orden específico
        from collections import OrderedDict
        context['indicadores_por_tipologia'] = OrderedDict()
        
        # Inicializar el diccionario con el orden específico
        for tipologia in orden_tipologias:
            context['indicadores_por_tipologia'][tipologia] = {
                'nombre': dict(MatrizCalidad.TIPOLOGIA_CHOICES).get(tipologia, tipologia),
                'color': colores_tipologias.get(tipologia, 'secondary'),
                'indicadores': []
            }
            
        # Agregar los indicadores a cada tipología
        for indicador in indicadores:
            if indicador.tipologia in context['indicadores_por_tipologia']:
                context['indicadores_por_tipologia'][indicador.tipologia]['indicadores'].append(indicador)
        
        return context
    
    def form_valid(self, form):
        print("\n=== INICIO form_valid ===")
        print(f"Datos del formulario: {form.cleaned_data}")
        print(f"Archivos recibidos: {self.request.FILES}")
        
        # Asignar el usuario actual como evaluador
        form.instance.evaluador = self.request.user
        
        # Guardar la auditoría primero para obtener un ID
        self.object = form.save(commit=False)
        self.object.save()
        print(f"Auditoría guardada con ID: {self.object.id}")
        
        tipo_monitoreo = form.cleaned_data.get('tipo_monitoreo')
        print(f"Tipo de monitoreo seleccionado: {tipo_monitoreo}")
        
        if tipo_monitoreo == 'speech':
            print("Procesando formulario de Speech Analytics...")
            # Si es Speech Analytics, procesar audio
            speech_form = SpeechForm(self.request.POST, self.request.FILES)
            print(f"Formulario Speech válido: {speech_form.is_valid()}")
            print(f"Errores del formulario Speech: {speech_form.errors if not speech_form.is_valid() else 'Ninguno'}")
            print(f"Archivo de audio recibido: {'Sí' if self.request.FILES.get('audio') else 'No'}")
            
            if speech_form.is_valid() and self.request.FILES.get('audio'):
                print("Formulario de Speech válido y archivo de audio presente")
                
                # Guardar el formulario sin commit para modificar los campos
                speech = speech_form.save(commit=False)
                speech.auditoria = self.object
                
                # Verificar que el archivo se asignó correctamente antes de guardar
                audio_file = self.request.FILES.get('audio')
                if audio_file:
                    print(f"Archivo recibido: {audio_file.name}, tamaño: {audio_file.size} bytes")
                    
                    # En producción, subir directamente a MinIO sin guardar localmente
                    from django.conf import settings
                    import os
                    
                    # Verificar si estamos en producción (Railway)
                    is_production = not settings.DEBUG or os.getenv('RAILWAY_ENVIRONMENT') is not None
                    print(f"Entorno de producción detectado: {is_production}")
                    
                    if is_production:
                        print("[PRODUCCIÓN] Subiendo archivo directamente a MinIO...")
                        # Subir directamente a MinIO sin guardar localmente
                        from .utils.minio_utils import subir_a_minio
                        from .utils.audio_utils import obtener_duracion_audio, obtener_tamano_archivo_mb
                        import tempfile
                        
                        # Calcular duración y tamaño ANTES de subir a MinIO
                        # Crear archivo temporal para calcular duración
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                            # Escribir el contenido del archivo subido al archivo temporal
                            for chunk in audio_file.chunks():
                                temp_file.write(chunk)
                            temp_file.flush()
                            
                            # Calcular duración y tamaño del archivo temporal
                            print(f"[PRODUCCIÓN] Calculando duración del archivo temporal: {temp_file.name}")
                            duracion_calculada = obtener_duracion_audio(temp_file.name)
                            tamano_calculado = obtener_tamano_archivo_mb(temp_file.name)
                            print(f"[PRODUCCIÓN] Duración calculada: {duracion_calculada}s, Tamaño: {tamano_calculado}MB")
                            
                            # Limpiar archivo temporal
                            os.unlink(temp_file.name)
                        
                        # Resetear el puntero del archivo para la subida a MinIO
                        audio_file.seek(0)
                        
                        # Generar nombre personalizado basado en la auditoría
                        nombre_personalizado = f"auditoria_{self.object.id}_audio_{speech.id if speech.id else 'temp'}"
                        
                        # Subir archivo a MinIO
                        resultado = subir_a_minio(
                            archivo=audio_file,
                            nombre_personalizado=nombre_personalizado,
                            carpeta="audios",
                            bucket_type="MINIO_BUCKET_NAME_LLAMADAS"
                        )
                        
                        if resultado['success']:
                            print(f"[PRODUCCIÓN] ✅ Archivo subido exitosamente a MinIO: {resultado['url']}")
                            # Configurar los campos de MinIO en el modelo
                            speech.minio_url = resultado['url']
                            speech.minio_object_name = resultado['object_name']
                            speech.subido_a_minio = True
                            # Asignar la duración y tamaño calculados previamente
                            speech.duracion_segundos = duracion_calculada
                            speech.tamano_archivo_mb = tamano_calculado
                            # No asignar el archivo local, solo los datos de MinIO
                            speech.audio = None
                        else:
                            print(f"[PRODUCCIÓN] ❌ Error al subir a MinIO: {resultado.get('error', 'Error desconocido')}")
                            return self.form_invalid(form)
                    else:
                        print("[DESARROLLO] Guardando archivo localmente...")
                        # En desarrollo, usar el flujo normal
                        speech.audio = audio_file
                else:
                    print("Error: No se pudo obtener el archivo de audio del request")
                    return self.form_invalid(form)
                
                # Guardar el modelo
                speech.save()
                
                # Verificar que el proceso fue exitoso
                if not is_production:
                    # En desarrollo, verificar que el archivo se guardó localmente
                    if not speech.audio or not speech.audio.name:
                        print("Error crítico: El archivo no se guardó correctamente en el modelo")
                        return self.form_invalid(form)
                else:
                    # En producción, verificar que se subió a MinIO
                    if not speech.subido_a_minio or not speech.minio_url:
                        print("Error crítico: El archivo no se subió correctamente a MinIO")
                        return self.form_invalid(form)
                
                # ===== PRINTS PARA VERIFICAR RUTA REAL DE GUARDADO =====
                print(f"\n=== INFORMACIÓN DE GUARDADO DE ARCHIVO ===")
                print(f"Campo audio del modelo: {speech.audio}")
                print(f"Nombre del archivo: {speech.audio.name if speech.audio else 'None'}")
                
                # Verificar que el archivo existe antes de intentar obtener la URL
                try:
                    if speech.audio and speech.audio.name:
                        # Si el archivo fue subido a MinIO, usar esa URL
                        if speech.subido_a_minio and speech.minio_url:
                            print(f"URL del archivo (MinIO): {speech.minio_url}")
                        else:
                            # Intentar obtener la URL local solo si el archivo existe
                            if hasattr(speech.audio, 'path') and os.path.exists(speech.audio.path):
                                print(f"URL del archivo (local): {speech.audio.url}")
                            else:
                                print("URL del archivo: Archivo local no existe, esperando subida a MinIO")
                    else:
                        print("URL del archivo: No disponible - archivo no asociado")
                except ValueError as e:
                    print(f"Error al obtener URL del archivo: {str(e)}")
                    print("El campo audio no tiene un archivo asociado correctamente")
                
                print(f"=== FIN INFORMACIÓN DE GUARDADO ===")
                
                # Crear registro de uso para facturación
                try:
                    speech.crear_registro_uso(self.request.user)
                    print(f"[Auditoría {self.object.id}] ✅ Registro de uso de procesamiento de audio creado")
                except Exception as e:
                    print(f"[Auditoría {self.object.id}] ❌ Error al crear registro de uso: {str(e)}")
                
                # Inicializar el JSON de resultado vacío
                speech.resultado_json = {"texto": "[Procesando transcripción...]"}
                
                # Guardar nuevamente para asegurar que los campos se actualicen
                speech.save()
                
                # Verificar que el archivo está disponible (local o MinIO)
                if is_production:
                    if speech.subido_a_minio and speech.minio_url:
                        print(f"Archivo de audio disponible en MinIO: {speech.minio_url}")
                    else:
                        print("Advertencia: No se pudo verificar el archivo de audio en MinIO")
                else:
                    if hasattr(speech.audio, 'path') and os.path.exists(speech.audio.path):
                        print(f"Archivo de audio guardado correctamente en: {speech.audio.path}")
                        print(f"Tamaño del archivo: {os.path.getsize(speech.audio.path) / (1024 * 1024):.2f} MB")
                    else:
                        print(f"Advertencia: No se pudo verificar el archivo de audio en: {getattr(speech.audio, 'path', 'Ruta no disponible')}")
                
                # Las importaciones ya están en el ámbito global

                def procesar_speech_en_background(speech_obj, auditoria_id, is_production=False):
                    """
                    Orquesta todo el proceso de Speech Analytics en un hilo separado.
                    Maneja tanto archivos locales como de MinIO.
                    """
                    print(f"[Auditoría {auditoria_id}] 🚀 Hilo de procesamiento iniciado.")
                    print(f"[Auditoría {auditoria_id}] Modo producción: {is_production}")
                    
                    import os
                    import tempfile
                    import requests
                    from django.conf import settings
                    
                    audio_path = None
                    temp_file_created = False
                    
                    try:
                        # ===== OBTENER ARCHIVO DE AUDIO =====
                        if is_production and speech_obj.subido_a_minio and speech_obj.minio_url:
                            print(f"[Auditoría {auditoria_id}] 📥 Descargando archivo desde MinIO: {speech_obj.minio_url}")
                            
                            # Descargar archivo temporal desde MinIO
                            response = requests.get(speech_obj.minio_url, stream=True)
                            response.raise_for_status()
                            
                            # Crear archivo temporal
                            temp_fd, audio_path = tempfile.mkstemp(suffix='.mp3', prefix=f'audio_{auditoria_id}_')
                            temp_file_created = True
                            
                            with os.fdopen(temp_fd, 'wb') as temp_file:
                                for chunk in response.iter_content(chunk_size=8192):
                                    temp_file.write(chunk)
                            
                            print(f"[Auditoría {auditoria_id}] ✅ Archivo descargado temporalmente: {audio_path}")
                            print(f"[Auditoría {auditoria_id}] Tamaño del archivo: {os.path.getsize(audio_path) / (1024 * 1024):.2f} MB")
                            
                        else:
                            # Modo desarrollo - usar archivo local
                            print(f"[Auditoría {auditoria_id}] 📁 Usando archivo local")
                            
                            # Usar el campo 'audio' del modelo para obtener la ruta correcta
                            if hasattr(speech_obj.audio, 'path'):
                                audio_path = speech_obj.audio.path
                                print(f"[Auditoría {auditoria_id}] Ruta desde speech_obj.audio.path: {audio_path}")
                            else:
                                error_msg = f"[Auditoría {auditoria_id}] ❌ Error: No se pudo obtener la ruta del archivo de audio"
                                print(error_msg)
                                speech_obj.resultado_json = {'texto': error_msg}
                                speech_obj.save()
                                return
                            
                            print(f"[Auditoría {auditoria_id}] 📁 Ruta final del audio: {audio_path}")
                            
                            # Verificar que el archivo existe
                            if not os.path.exists(audio_path):
                                error_msg = f"[Auditoría {auditoria_id}] ❌ Error: El archivo de audio no existe en la ruta: {audio_path}"
                                print(error_msg)
                                speech_obj.resultado_json = {'texto': error_msg}
                                speech_obj.save()
                                raise FileNotFoundError(error_msg)
                            
                            print(f"[Auditoría {auditoria_id}] Tamaño del archivo: {os.path.getsize(audio_path) / (1024 * 1024):.2f} MB")
                            print(f"[Auditoría {auditoria_id}] Permisos del archivo: {oct(os.stat(audio_path).st_mode)[-3:]}")
                        
                        # Paso 1: Transcripción del audio
                        try:
                            print(f"[Auditoría {auditoria_id}] 🎤 Transcribiendo audio...")
                            resultado_transcripcion = transcribir_audio(audio_path)
                            print(f"[Auditoría {auditoria_id}] ✅ Transcripción de audio completada.")
                        
                            # Paso 2: Guardar JSON de transcripción y formatear texto
                            texto_formateado = ""
                            try:
                                # Extraer el resultado de la transcripción - manejar diferentes formatos posibles
                                prediccion = resultado_transcripcion
                                
                                # Si tiene una estructura anidada dentro de 'resultado', extraerla
                                if isinstance(resultado_transcripcion, dict):
                                    if 'resultado' in resultado_transcripcion:
                                        prediccion = resultado_transcripcion['resultado']
                                        print(f"[Auditoría {auditoria_id}] ℹ️ Usando estructura de resultado anidado")
                                
                                if not prediccion:
                                    raise ValueError("No se pudo extraer datos válidos de la transcripción")
                                    
                                # Debug: Mostrar estructura
                                if isinstance(prediccion, dict):
                                    print(f"[Auditoría {auditoria_id}] ⚙️ Estructura del JSON: {list(prediccion.keys())}")
                                else:
                                    print(f"[Auditoría {auditoria_id}] ⚙️ Tipo de predicción: {type(prediccion)}")
                                
                                # Crear directorio para transcripciones si no existe
                                trans_dir = os.path.join(settings.MEDIA_ROOT, 'auditorias', 'transcripciones')
                                os.makedirs(trans_dir, exist_ok=True)
                                
                                # Generar nombre de archivo único
                                import uuid
                                unique_id = str(uuid.uuid4())[:8]
                                json_filename = f'auditoria_{auditoria_id}_{unique_id}.json'
                                json_path = os.path.join(trans_dir, json_filename)
                                
                                # Guardar el JSON de la transcripción
                                with open(json_path, 'w', encoding='utf-8') as f:
                                    json.dump(prediccion, f, ensure_ascii=False, indent=2)
                                
                                # Actualizar el modelo Speech
                                speech_obj.transcripcion = f'auditorias/transcripciones/{json_filename}'
                                print(f"[Auditoría {auditoria_id}] 📄 Archivo de transcripción guardado en: {speech_obj.transcripcion}")
                                
                                # Formatear el texto de la transcripción - intentar primero con el JSON directo
                                print(f"[Auditoría {auditoria_id}] 🔄 Procesando transcripción...")
                                
                                # Primer intento: formatear directamente desde el objeto predicción
                                texto_formateado = format_transcript_as_script(prediccion)
                                
                                # Si hay algún error, probar con la ruta del archivo como respaldo
                                if texto_formateado.startswith('[Error') or texto_formateado.startswith('[Advertencia]'):
                                    print(f"[Auditoría {auditoria_id}] ⚠️ Intento directo fallido: {texto_formateado[:100]}...")
                                    print(f"[Auditoría {auditoria_id}] 🔄 Intentando formatear desde el archivo JSON...")
                                    texto_formateado = format_transcript_as_script(json_path)
                                
                                # Si todavía hay errores, último intento: extracción directa
                                if texto_formateado.startswith('[Error') or texto_formateado.startswith('[Advertencia]'):
                                    print(f"[Auditoría {auditoria_id}] ⚠️ Segundo intento fallido. Último intento: extracción directa")
                                    # Intentar extraer el texto directamente de la respuesta
                                    if isinstance(prediccion, dict) and 'output' in prediccion:
                                        if isinstance(prediccion['output'], str):
                                            # Si output es una cadena, usarla directamente
                                            texto_formateado = prediccion['output']
                                        elif isinstance(prediccion['output'], dict) and 'segments' in prediccion['output']:
                                            # Si tiene estructura de segmentos, extraer textos
                                            texto_formateado = " ".join(seg.get("text", "") for seg in prediccion["output"]["segments"])
                                
                                # Si después de todos los intentos sigue habiendo error, marcar como fallido
                                if texto_formateado.startswith('[Error') or texto_formateado.startswith('[Advertencia]') or not texto_formateado.strip():
                                    texto_formateado = "[Error] No se pudo extraer texto válido de la transcripción tras múltiples intentos"
                                    
                                # Almacenar el resultado y guardar
                                speech_obj.resultado_json = {'texto': texto_formateado}
                                print(f"[Auditoría {auditoria_id}] ✅ Transcripción procesada")
                                
                                # Debug - imprimir primeros caracteres
                                preview_length = min(len(texto_formateado), 100)
                                print(f"[Auditoría {auditoria_id}] 📝 Primeros {preview_length} caracteres:")
                                print(texto_formateado[:preview_length] + ("..." if len(texto_formateado) > preview_length else ""))
                                
                                # Guardar los cambios en la base de datos
                                speech_obj.save(update_fields=['transcripcion', 'resultado_json', 'fecha_actualizacion'])
                                print(f"[Auditoría {auditoria_id}] 💾 Modelo actualizado en la base de datos.")
                                
                            except Exception as e:
                                print(f"[Auditoría {auditoria_id}] ⚠️ Error al guardar/formatear: {e}. Intentando extraer texto plano...")
                                try:
                                    # Intentar extraer el texto directamente del resultado
                                    if isinstance(resultado_transcripcion, dict) and 'output' in resultado_transcripcion and 'segments' in resultado_transcripcion['output']:
                                        texto_formateado = " ".join(seg["text"] for seg in resultado_transcripcion["output"]["segments"])
                                        speech_obj.resultado_json = {'texto': texto_formateado}
                                        speech_obj.save(update_fields=['resultado_json', 'fecha_actualizacion'])
                                        print(f"[Auditoría {auditoria_id}] ✅ Texto extraído directamente del resultado.")
                                    else:
                                        raise ValueError("Formato de transcripción inesperado")
                                except Exception as ex:
                                    error_msg = f"Error extrayendo texto plano: {ex}"
                                    print(f"[Auditoría {auditoria_id}] ❌ {error_msg}")
                                    speech_obj.resultado_json = {'texto': f'[Error: {error_msg}]'}
                                    speech_obj.save(update_fields=['resultado_json', 'fecha_actualizacion'])
                                    raise Exception(error_msg)
                        except Exception as e:
                            error_msg = f"[Auditoría {auditoria_id}] ❌ Error crítico durante la transcripción: {str(e)}"
                            print(error_msg)
                            speech_obj.resultado_json = {'texto': f'Error en transcripción: {str(e)}'}
                            speech_obj.save()
                            raise Exception(f'Error en transcripción: {str(e)}')
                        
                        # Paso 3: Análisis de Calidad con IA
                        if not texto_formateado or "[Error" in texto_formateado or "[Advertencia]" in texto_formateado:
                            print(f"[Auditoría {auditoria_id}] 🛑 Análisis de IA omitido por problemas en la transcripción: {texto_formateado[:100]}...")
                            # Continuar sin análisis de IA pero completar el proceso
                            speech_obj.save()
                            print(f"[Auditoría {auditoria_id}] ✅ Proceso finalizado sin análisis de IA.")
                        else:
                            print(f"[Auditoría {auditoria_id}] 🧠 Iniciando análisis de calidad con IA...")
                            try:
                                analizador = AnalizadorTranscripciones()
                                # Convertimos texto_formateado a str si no lo es
                                if not isinstance(texto_formateado, str):
                                    texto_formateado = str(texto_formateado)
                                analisis_resultado = analizador.evaluar_calidad_llamada(texto_formateado)
                                speech_obj.analisis_json = analisis_resultado
                                
                                if 'error' in analisis_resultado:
                                    print(f"[Auditoría {auditoria_id}] ❌ Error en análisis de IA: {analisis_resultado['error']}")
                                else:
                                    print(f"[Auditoría {auditoria_id}] ✅ Análisis de IA completado. Autocompletando auditoría...")
                                    autocompletar_auditoria_desde_analisis(speech_obj.auditoria, analisis_resultado)

                            except Exception as e:
                                print(f"[Auditoría {auditoria_id}] ❌ Fallo crítico en el proceso de análisis de IA: {e}")
                                speech_obj.analisis_json = {'error': f'Fallo crítico en el proceso de análisis: {str(e)}'}
                            
                            # Paso 4: Guardado final
                            speech_obj.save()
                            print(f"[Auditoría {auditoria_id}] ✅ Proceso finalizado.")
                        
                    except Exception as e:
                        error_msg = f"[Auditoría {auditoria_id}] ❌ Error crítico en el procesamiento: {str(e)}"
                        print(error_msg)
                        speech_obj.resultado_json = {'texto': f'Error crítico: {str(e)}'}
                        speech_obj.save()
                        
                    finally:
                        # Limpiar archivo temporal si se creó uno
                        if temp_file_created and audio_path and os.path.exists(audio_path):
                            try:
                                os.unlink(audio_path)
                                print(f"[Auditoría {auditoria_id}] 🧹 Archivo temporal limpiado: {audio_path}")
                            except Exception as e:
                                print(f"[Auditoría {auditoria_id}] ⚠️ Error al limpiar archivo temporal: {e}")

            # Determinar si estamos en producción
            is_production = os.environ.get('RAILWAY_ENVIRONMENT') is not None
            
            # Iniciar procesamiento en segundo plano
            threading.Thread(target=procesar_speech_en_background, args=(speech, self.object.id, is_production)).start()
            messages.success(self.request, 'Auditoría Speech guardada. El audio será procesado en segundo plano. Recargue el detalle en unos minutos para ver la transcripción.')
        else:
            error_msg = 'Debes adjuntar un archivo de audio válido.'
            print(f"Error en el formulario de Speech: {error_msg}")
            print(f"Errores del formulario: {speech_form.errors}")
            print(f"Archivos recibidos: {self.request.FILES}")
            messages.error(self.request, error_msg)
            return self.form_invalid(form)
        
        # Procesar las respuestas de los indicadores
            indicadores = MatrizCalidad.objects.filter(activo=True)
            from .models import DetalleAuditoria
            self.object.respuestas.all().delete()
            for indicador in indicadores:
                campo_estado = f'indicador_{indicador.id}_estado'
                campo_observaciones = f'observaciones_{indicador.id}'
                
                # Obtener el valor del radio button (cumple, no_cumple, o sin_seleccionar)
                estado = self.request.POST.get(campo_estado, 'sin_seleccionar')
                
                # Determinar si cumple basado en el valor del radio
                cumple = (estado == 'cumple')
                
                # Solo guardar si se seleccionó una opción (no 'sin_seleccionar')
                if estado != 'sin_seleccionar':
                    observaciones = self.request.POST.get(campo_observaciones, '')
                    DetalleAuditoria.objects.create(
                        auditoria=self.object,
                        indicador=indicador,
                        cumple=cumple,
                        observaciones=observaciones if observaciones.strip() else None
                    )

            self.object.save()
            messages.success(self.request, 'Auditoría guardada correctamente.')
        
        print("=== FIN form_valid ===\n")
        # Redirigir explícitamente a la lista de auditorías
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        print("\n=== FORMULARIO INVÁLIDO ===")
        print(f"Errores del formulario: {form.errors}")
        print(f"Errores no asociados a campos: {form.non_field_errors()}")
        print(f"Datos POST: {self.request.POST}")
        print(f"Archivos FILES: {self.request.FILES}")
        return super().form_invalid(form)


class AuditoriaUpdateView(CalidadBaseView, UpdateView):
    """
    Vista para editar una auditoría existente
    """
    model = Auditoria
    form_class = AuditoriaForm
    template_name = 'calidad/auditorias/form_auditoria.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['detalle_formset'] = DetalleAuditoriaFormSet(
                self.request.POST, 
                self.request.FILES,
                instance=self.object,
                form_kwargs={'user': self.request.user}
            )
        else:
            context['detalle_formset'] = DetalleAuditoriaFormSet(
                instance=self.object,
                form_kwargs={'user': self.request.user}
            )
            
        context['titulo'] = 'Editar Auditoría de Calidad'
        context['subtitulo'] = f'Editando auditoría #{self.object.id}'
        context['es_edicion'] = True
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        detalle_formset = context['detalle_formset']
        
        if detalle_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.save()
            
            # Guardar los detalles de la auditoría
            detalle_formset.save()
            
            # Calcular y guardar el puntaje total
            self.object.puntaje_total = self.object.calcular_puntaje_total()
            self.object.save()
            
            messages.success(self.request, 'Auditoría actualizada correctamente.')
            return redirect('calidad:detalle_auditoria', pk=self.object.pk)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class AuditoriaDetailView(CalidadBaseView, DetailView):
    """
    Vista para ver los detalles de una auditoría
    """
    model = Auditoria
    template_name = 'calidad/auditorias/detalle_auditoria.html'
    context_object_name = 'auditoria'
    
    def get(self, request, *args, **kwargs):
        """
        Maneja las solicitudes GET y captura el error 404
        """
        try:
            # Intentar obtener el objeto
            self.object = self.get_object()
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)
            
        except Http404:
            # Si la auditoría no existe, redirigir a la lista con un mensaje
            messages.error(request, 'La auditoría solicitada no existe o ha sido eliminada.')
            return redirect('calidad:lista_auditorias')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        auditoria = self.get_object()
        
        # Obtener la transcripción si existe
        context['transcripcion'] = None
        try:
            if hasattr(auditoria, 'speech') and auditoria.speech:
                # Si hay un resultado_json, obtener el texto de ahí
                if auditoria.speech.resultado_json and 'texto' in auditoria.speech.resultado_json:
                    context['transcripcion'] = auditoria.speech.resultado_json['texto']
                # Si no, intentar obtenerlo del archivo de transcripción
                elif auditoria.speech.transcripcion:
                    import os
                    from django.conf import settings
                    
                    # Construir la ruta completa al archivo de transcripción
                    transcripcion_path = os.path.join(settings.MEDIA_ROOT, auditoria.speech.transcripcion)
                    
                    # Leer el contenido del archivo si existe
                    if os.path.exists(transcripcion_path):
                        with open(transcripcion_path, 'r', encoding='utf-8') as f:
                            try:
                                # Intentar cargar el JSON y extraer el texto de la transcripción
                                data = json.load(f)
                                if isinstance(data, dict):
                                    # Intentar diferentes claves comunes donde podría estar el texto
                                    context['transcripcion'] = data.get('texto') or data.get('transcripcion') or 'Transcripción no disponible'
                                else:
                                    # Si no es un diccionario, mostrar el contenido como está
                                    context['transcripcion'] = str(data)
                            except json.JSONDecodeError:
                                # Si no es un JSON válido, leer el contenido como texto plano
                                f.seek(0)
                                context['transcripcion'] = f.read()
        except Exception as e:
            print(f"Error al obtener la transcripción: {str(e)}")
            context['transcripcion'] = f"Error al cargar la transcripción: {str(e)}"
        
        # Obtener información básica de la auditoría
        context['titulo'] = f'Auditoría de {auditoria.agente.get_full_name()}'
        context['subtitulo'] = f'Realizada el {auditoria.fecha_llamada.strftime("%d/%m/%Y")} por {auditoria.evaluador.get_full_name()}'
        
        # Obtener respuestas de la auditoría agrupadas por categoría
        respuestas = auditoria.respuestas.select_related('indicador').all()
        
        # Organizar respuestas por categoría y tipología
        categorias = {}
        estadisticas_tipologias = {}
        
        for respuesta in respuestas:
            categoria_nombre = respuesta.indicador.categoria
            tipologia = respuesta.indicador.tipologia or 'Sin tipología'
            
            # Inicializar diccionario de categorías si no existe
            if categoria_nombre not in categorias:
                categorias[categoria_nombre] = []
            
            # Inicializar estadísticas de tipología si no existe
            if tipologia not in estadisticas_tipologias:
                estadisticas_tipologias[tipologia] = {
                    'total': 0,
                    'cumplidos': 0,
                    'no_cumplidos': 0,
                    'puntos_perdidos': 0
                }
            
            # Actualizar estadísticas de tipología
            estadisticas_tipologias[tipologia]['total'] += 1
            if respuesta.cumple:
                estadisticas_tipologias[tipologia]['cumplidos'] += 1
            else:
                estadisticas_tipologias[tipologia]['no_cumplidos'] += 1
                estadisticas_tipologias[tipologia]['puntos_perdidos'] += respuesta.indicador.ponderacion
            
            # Calcular puntaje obtenido para este indicador
            puntaje_obtenido = respuesta.indicador.ponderacion if respuesta.cumple else 0
            
            categorias[categoria_nombre].append({
                'indicador': respuesta.indicador,
                'cumple': respuesta.cumple,
                'observaciones': respuesta.observaciones,
                'puntaje_obtenido': puntaje_obtenido,
                'tipologia': tipologia
            })
        
        # Verificar si hay incumplimientos
        context['hay_incumplimientos'] = any(
            not respuesta.cumple 
            for respuesta in respuestas
        )
        
        # Agregar categorías al contexto
        context['categorias'] = categorias
        
        # Agregar información adicional que pueda necesitar el template
        context['observaciones'] = auditoria.observaciones if hasattr(auditoria, 'observaciones') else ''
        context['puntaje_total'] = auditoria.calcular_puntaje_total()
        context['puntaje_maximo'] = 100  # Puntaje máximo posible
        context['porcentaje_total'] = float(context['puntaje_total'])  # Ya viene como porcentaje
        
        # Agregar el texto de transcripción si existe
        try:
            speech = auditoria.speech
            texto_transcripcion = speech.resultado_json.get('texto', '') if speech and speech.resultado_json else ''
        except Exception as e:
            print(f"Error obteniendo transcripción: {e}")
            texto_transcripcion = ''
        
        # Preparar estadísticas de tipologías
        estadisticas = [
            {
                'nombre': tipologia,
                'total': int(stats['total']),  # Convertir a entero
                'cumplidos': int(stats['cumplidos']),  # Convertir a entero
                'no_cumplidos': int(stats['no_cumplidos']),  # Convertir a entero
                'puntos_perdidos': float(stats['puntos_perdidos']),  # Convertir a float
                'porcentaje_cumplimiento': float((stats['cumplidos'] / stats['total'] * 100) if stats['total'] > 0 else 100)  # Convertir a float
            }
            for tipologia, stats in estadisticas_tipologias.items()
        ]
        
        # Ordenar por puntos perdidos (de mayor a menor)
        estadisticas.sort(key=lambda x: x['puntos_perdidos'], reverse=True)
        
        # Agregar al contexto
        context['estadisticas_tipologias'] = estadisticas
        
        # Serializar a JSON asegurando que todos los valores sean tipos nativos
        def decimal_default(obj):
            from decimal import Decimal
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
            
        context['estadisticas_tipologias_json'] = json.dumps(estadisticas, default=decimal_default)
        
        context['texto_transcripcion'] = texto_transcripcion
        return context


class AuditoriaDeleteView(CalidadBaseView, DeleteView):
    """
    Vista para eliminar una auditoría
    """
    model = Auditoria
    template_name = 'calidad/auditorias/confirmar_eliminar_auditoria.html'
    success_url = reverse_lazy('calidad:lista_auditorias')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Verificar si hay archivos de audio en MinIO que necesitan ser eliminados
        try:
            if hasattr(self.object, 'speech') and self.object.speech:
                speech = self.object.speech
                if speech.subido_a_minio and speech.minio_object_name:
                    print(f"[ELIMINACIÓN] Eliminando archivo de MinIO: {speech.minio_object_name}")
                    resultado_minio = speech.eliminar_de_minio()
                    if resultado_minio['success']:
                        print(f"[ELIMINACIÓN] ✅ Archivo eliminado de MinIO exitosamente")
                    else:
                        print(f"[ELIMINACIÓN] ⚠️ Error al eliminar archivo de MinIO: {resultado_minio.get('error', 'Error desconocido')}")
                        # Continuar con la eliminación aunque falle MinIO
        except Exception as e:
            print(f"[ELIMINACIÓN] ⚠️ Error al intentar eliminar archivo de MinIO: {str(e)}")
            # Continuar con la eliminación aunque falle MinIO
        
        # Eliminar la auditoría (esto eliminará automáticamente los objetos relacionados por CASCADE)
        self.object.delete()
        
        # Si es una petición AJAX, devolver respuesta JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'message': 'La auditoría ha sido eliminada correctamente.'
            })
        
        # Si no es AJAX, comportamiento normal
        messages.success(request, 'La auditoría ha sido eliminada correctamente.')
        return HttpResponseRedirect(self.get_success_url())

@login_required
@ip_permitida
@grupo_requerido('Calidad', 'Administrador')
def api_detalle_auditoria(request, pk):
    """
    API para obtener detalles de una auditoría en formato JSON
    """
    try:
        auditoria = get_object_or_404(Auditoria, pk=pk)
        data = {
            'id': auditoria.id,
            'agente_nombre': auditoria.agente.get_full_name() or auditoria.agente.username,
            'fecha_llamada_formateada': auditoria.fecha_llamada.strftime('%d/%m/%Y'),
            'evaluador_nombre': auditoria.evaluador.get_full_name() or auditoria.evaluador.username,
            'porcentaje_aprobacion': str(auditoria.get_porcentaje_aprobacion()),
            'puntaje_total': str(auditoria.puntaje_total)
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@ip_permitida
@grupo_requerido('Calidad', 'Administrador')
def descargar_audio_llamada(request, pk):
    """
    Vista para descargar el archivo de audio de una llamada
    """
    auditoria = get_object_or_404(Auditoria, pk=pk)
    
    if not auditoria.archivo_audio:
        messages.error(request, 'No hay archivo de audio para descargar')
        return redirect('calidad:detalle_auditoria', pk=auditoria.pk)
    
    try:
        response = HttpResponse(auditoria.archivo_audio, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{auditoria.archivo_audio.name}"'
        return response
    except Exception as e:
        messages.error(request, f'Error al descargar el archivo: {str(e)}')
        return redirect('calidad:detalle_auditoria', pk=auditoria.pk)



# ===============================
# Dashboard de Uso de Procesamiento de Audio (Solo superuser)
# ===============================
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum

@staff_member_required
def dashboard_uso_audio(request):
    """Muestra estadísticas globales del modelo UsoProcesamientoAudio con filtros opcionales"""
    from decimal import Decimal  # Import local para evitar ciclos
    from datetime import datetime
    from .models import UsoProcesamientoAudio

    qs = UsoProcesamientoAudio.objects.all()
    
    # Aplicar filtros si se proporcionan
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    agente = request.GET.get('agente')
    
    if fecha_inicio:
        try:
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%d/%m/%Y').date()
            qs = qs.filter(fecha_transcripcion__gte=fecha_inicio_obj)
        except ValueError:
            pass  # Ignorar formato de fecha inválido
    
    if fecha_fin:
        try:
            fecha_fin_obj = datetime.strptime(fecha_fin, '%d/%m/%Y').date()
            qs = qs.filter(fecha_transcripcion__lte=fecha_fin_obj)
        except ValueError:
            pass  # Ignorar formato de fecha inválido
    
    if agente:
        qs = qs.filter(usuario__username__icontains=agente)
    
    # Ordenamiento por defecto
    qs = qs.order_by('-fecha_transcripcion')

    total_registros = qs.count()

    duracion_total_seg = qs.aggregate(total=Sum('duracion_audio_segundos'))['total'] or 0
    duracion_total_horas = round(duracion_total_seg / 3600, 2)
    duracion_total_segundos = int(duracion_total_seg)
    duracion_promedio_seg = round(duracion_total_seg / total_registros, 2) if total_registros else 0

    costo_transcripcion_total = qs.aggregate(total=Sum('costo_transcripcion'))['total'] or Decimal('0')
    costo_analisis_total = qs.aggregate(total=Sum('costo_analisis'))['total'] or Decimal('0')
    costo_total_global = costo_transcripcion_total + costo_analisis_total
    costo_promedio = float(costo_total_global / total_registros) if total_registros else 0

    # Solo tenemos disponible tokens_analisis en el modelo
    tokens_analisis_total = qs.aggregate(total=Sum('tokens_analisis'))['total'] or 0

    # --- Tendencias mensuales ---
    from django.db.models.functions import TruncMonth
    from django.db.models import F
    monthly = qs.annotate(mes=TruncMonth('fecha_transcripcion')).values('mes') \
        .order_by('mes') \
        .annotate(
            duracion_seg=Sum('duracion_audio_segundos'),
            costo_total=Sum(F('costo_transcripcion') + F('costo_analisis'))
        )

    # Preparar datos para las gráficas en formato JSON
    import json
    etiquetas_meses = json.dumps([item['mes'].strftime('%b %Y') for item in monthly if item['mes']])
    duracion_horas_mes = json.dumps([round((item['duracion_seg'] or 0)/3600, 2) for item in monthly])
    costo_total_mes = json.dumps([float(item['costo_total'] or 0) for item in monthly])

    # Obtener lista de agentes únicos para el filtro
    agentes_disponibles = UsoProcesamientoAudio.objects.values_list('usuario__username', flat=True).distinct().order_by('usuario__username')
    
    context = {
        'titulo': 'Dashboard de Procesamiento de Audio',
        'subtitulo': 'Resumen de consumos y costos',
        'total_registros': total_registros,
        'duracion_total_horas': duracion_total_horas,
        'duracion_total_seg': duracion_total_segundos,
        'duracion_promedio_seg': duracion_promedio_seg,
        'costo_promedio': costo_promedio,
        'costo_transcripcion_total': float(costo_transcripcion_total),
        'costo_analisis_total': float(costo_analisis_total),
        'costo_total_global': float(costo_total_global),
        'costo_promedio': costo_promedio,
        'tokens_analisis_total': tokens_analisis_total,
        # Datos para gráficas
        'etiquetas_meses': etiquetas_meses,
        'duracion_horas_mes': duracion_horas_mes,
        'costo_total_mes': costo_total_mes,
        # Datos para filtros
        'agentes_disponibles': agentes_disponibles,
        'fecha_inicio_filtro': fecha_inicio,
        'fecha_fin_filtro': fecha_fin,
        'agente_filtro': agente,
    }

    return render(request, 'calidad/dashboard_uso_audio.html', context)

# Vistas para estadísticas e informes
@login_required
@ip_permitida
@grupo_requerido('Calidad', 'Administrador')
def estadisticas_auditorias(request):
    """
    Vista para mostrar estadísticas de las auditorías
    """
    # Obtener datos para las estadísticas
    total_auditorias = Auditoria.objects.count()

    
    # Obtener los 5 usuarios con más auditorías
    top_usuarios = User.objects.annotate(
        total_auditorias=Count('auditorias_recibidas'),
        promedio_puntaje=Coalesce(Avg('auditorias_recibidas__puntaje_total'), Value(0.0))
    ).filter(total_auditorias__gt=0).order_by('-total_auditorias')[:5]
    
    # Obtener estadísticas por mes
    auditorias_por_mes = Auditoria.objects.annotate(
        mes=TruncMonth('fecha_creacion')
    ).values('mes').annotate(
        total=Count('id'),
        promedio=Avg('puntaje_total')
    ).order_by('mes')
    
    context = {
        'titulo': 'Estadísticas de Auditorías',
        'subtitulo': 'Métricas y análisis de las auditorías realizadas',
        'total_auditorias': total_auditorias,
        'top_usuarios': top_usuarios,
        'auditorias_por_mes': list(auditorias_por_mes),  # Convertir a lista para usar en JavaScript
    }
    
    return render(request, 'calidad/auditorias/estadisticas.html', context)


@login_required
def perfil(request):
    """
    Vista de perfil para el módulo de calidad
    """
    from django.contrib.auth import update_session_auth_hash
    
    if request.method == 'POST':
        user = request.user
        # Actualizar datos del perfil
        user.first_name = request.POST.get('nombre', user.first_name)
        user.email = request.POST.get('email', user.email)
        
        # Manejar cambio de contraseña si se proporcionó
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 and password2:
            if password1 == password2:
                if len(password1) >= 8:  # Validación básica de contraseña
                    user.set_password(password1)
                    update_session_auth_hash(request, user)  # Importante para no cerrar la sesión
                    messages.success(request, 'Contraseña actualizada correctamente')
                else:
                    messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
                    return redirect('calidad:perfil')
            else:
                messages.error(request, 'Las contraseñas no coinciden')
                return redirect('calidad:perfil')
        elif password1 or password2:
            messages.error(request, 'Debe completar ambos campos de contraseña')
            return redirect('calidad:perfil')
        
        try:
            user.save()
            if not (password1 and password2):  # Solo mostrar este mensaje si no se cambió la contraseña
                messages.success(request, 'Perfil actualizado correctamente')
        except Exception as e:
            messages.error(request, f'Error al actualizar el perfil: {str(e)}')
            return redirect('calidad:perfil')
        
        return redirect('calidad:perfil')
    
    return render(request, 'calidad/perfil.html')


# ============================================================================
# VISTAS PARA ASESORES - RESPUESTAS A AUDITORÍAS
# ============================================================================

class AsesorBaseView(LoginRequiredMixin):
    """
    Vista base para asesores que pueden ver y responder a sus auditorías
    """
    login_url = '/login/'
    
    def dispatch(self, request, *args, **kwargs):
        # Los asesores pueden ver sus propias auditorías
        return super().dispatch(request, *args, **kwargs)


class MisAuditoriasListView(AsesorBaseView, ListView):
    """
    Vista para que los asesores vean sus auditorías
    """
    model = Auditoria
    template_name = 'calidad/asesores/mis_auditorias.html'
    context_object_name = 'auditorias'
    paginate_by = 20
    
    def get_queryset(self):
        # Solo mostrar auditorías del usuario actual
        queryset = Auditoria.objects.filter(
            agente=self.request.user
        ).select_related(
            'evaluador', 'agente'
        ).prefetch_related(
            'respuestas__indicador',
            'respuestas_asesor'
        ).order_by('-fecha_llamada')
        
        # Filtros opcionales
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        estado_respuesta = self.request.GET.get('estado_respuesta')
        
        if fecha_desde:
            queryset = queryset.filter(fecha_llamada__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_llamada__lte=fecha_hasta)
            
        # Filtrar por estado de respuesta
        if estado_respuesta == 'pendientes':
            # Auditorías con indicadores no cumplidos sin respuesta
            queryset = queryset.filter(
                respuestas__cumple=False
            ).exclude(
                respuestas_asesor__isnull=False
            ).distinct()
        elif estado_respuesta == 'respondidas':
            # Auditorías con al menos una respuesta
            queryset = queryset.filter(
                respuestas_asesor__isnull=False
            ).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas del asesor
        total_auditorias = Auditoria.objects.filter(agente=self.request.user).count()
        
        # Auditorías con indicadores no cumplidos sin respuesta
        auditorias_pendientes = Auditoria.objects.filter(
            agente=self.request.user,
            respuestas__cumple=False
        ).exclude(
            respuestas_asesor__isnull=False
        ).distinct().count()
        
        # Auditorías con respuestas
        auditorias_respondidas = Auditoria.objects.filter(
            agente=self.request.user,
            respuestas_asesor__isnull=False
        ).distinct().count()
        
        # Promedio de puntaje
        promedio_puntaje = Auditoria.objects.filter(
            agente=self.request.user
        ).aggregate(
            promedio=Avg('puntaje_total')
        )['promedio'] or 0
        
        context.update({
            'total_auditorias': total_auditorias,
            'auditorias_pendientes': auditorias_pendientes,
            'auditorias_respondidas': auditorias_respondidas,
            'promedio_puntaje': round(promedio_puntaje, 2),
            'filtros': {
                'fecha_desde': self.request.GET.get('fecha_desde', ''),
                'fecha_hasta': self.request.GET.get('fecha_hasta', ''),
                'estado_respuesta': self.request.GET.get('estado_respuesta', ''),
            }
        })
        
        return context


class MiAuditoriaDetailView(AsesorBaseView, DetailView):
    """
    Vista detallada de una auditoría para el asesor
    """
    model = Auditoria
    template_name = 'calidad/asesores/detalle_mi_auditoria.html'
    context_object_name = 'auditoria'
    
    def get_queryset(self):
        # Solo permitir ver auditorías propias
        return Auditoria.objects.filter(agente=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        auditoria = self.get_object()
        
        # Obtener indicadores no cumplidos
        indicadores_no_cumplidos = auditoria.respuestas.filter(cumple=False)
        
        # Obtener respuestas existentes del asesor
        respuestas_asesor = RespuestaAuditoria.objects.filter(
            auditoria=auditoria,
            asesor=self.request.user
        ).select_related('detalle_auditoria__indicador')
        
        # Crear diccionario de respuestas por detalle_auditoria_id
        respuestas_dict = {
            respuesta.detalle_auditoria.id: respuesta 
            for respuesta in respuestas_asesor
        }
        
        # Indicadores que necesitan respuesta (no cumplidos sin respuesta)
        indicadores_pendientes = [
            detalle for detalle in indicadores_no_cumplidos 
            if detalle.id not in respuestas_dict
        ]
        
        context.update({
            'indicadores_no_cumplidos': indicadores_no_cumplidos,
            'indicadores_cumplidos': auditoria.respuestas.filter(cumple=True),
            'respuestas_asesor': respuestas_dict,
            'indicadores_pendientes': indicadores_pendientes,
            'puede_responder': len(indicadores_pendientes) > 0,
        })
        
        return context


class ResponderIndicadorView(AsesorBaseView, CreateView):
    """
    Vista para que el asesor responda a un indicador no cumplido
    """
    model = RespuestaAuditoria
    form_class = RespuestaAuditoriaForm
    template_name = 'calidad/asesores/responder_indicador.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que el detalle de auditoría existe y pertenece al usuario
        self.detalle_auditoria = get_object_or_404(
            DetalleAuditoria,
            id=kwargs['detalle_id'],
            auditoria__agente=request.user,
            cumple=False  # Solo se puede responder a indicadores no cumplidos
        )
        
        # Verificar que no existe ya una respuesta
        if RespuestaAuditoria.objects.filter(
            detalle_auditoria=self.detalle_auditoria,
            asesor=request.user
        ).exists():
            messages.warning(request, 'Ya has respondido a este indicador.')
            return redirect('calidad:mi_auditoria_detalle', pk=self.detalle_auditoria.auditoria.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'auditoria': self.detalle_auditoria.auditoria,
            'detalle_auditoria': self.detalle_auditoria,
            'asesor': self.request.user
        })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'auditoria': self.detalle_auditoria.auditoria,
            'detalle_auditoria': self.detalle_auditoria,
            'indicador': self.detalle_auditoria.indicador,
        })
        return context
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Tu respuesta al indicador "{self.detalle_auditoria.indicador.indicador}" ha sido guardada exitosamente.'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('calidad:mi_auditoria_detalle', kwargs={'pk': self.detalle_auditoria.auditoria.pk})


class EditarRespuestaView(AsesorBaseView, UpdateView):
    """
    Vista para editar una respuesta existente
    """
    model = RespuestaAuditoria
    form_class = RespuestaAuditoriaForm
    template_name = 'calidad/asesores/editar_respuesta.html'
    
    def get_queryset(self):
        # Solo permitir editar respuestas propias
        return RespuestaAuditoria.objects.filter(
            asesor=self.request.user,
            estado__in=['pendiente', 'respondido']  # No permitir editar si está en seguimiento o cerrado
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        respuesta = self.get_object()
        context.update({
            'auditoria': respuesta.auditoria,
            'detalle_auditoria': respuesta.detalle_auditoria,
            'indicador': respuesta.detalle_auditoria.indicador,
        })
        return context
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            'Tu respuesta ha sido actualizada exitosamente.'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('calidad:mi_auditoria_detalle', kwargs={'pk': self.object.auditoria.pk})


@login_required
def dashboard_asesor(request):
    """
    Dashboard principal para asesores
    """
    # Estadísticas generales del asesor
    total_auditorias = Auditoria.objects.filter(agente=request.user).count()
    
    # Auditorías recientes (últimas 5)
    auditorias_recientes = Auditoria.objects.filter(
        agente=request.user
    ).order_by('-fecha_llamada')[:5]
    
    # Indicadores pendientes de respuesta
    indicadores_pendientes = DetalleAuditoria.objects.filter(
        auditoria__agente=request.user,
        cumple=False
    ).exclude(
        respuestas_asesor__isnull=False
    ).count()
    
    # Respuestas en seguimiento
    respuestas_seguimiento = RespuestaAuditoria.objects.filter(
        asesor=request.user,
        estado='en_seguimiento'
    ).count()
    
    # Compromisos próximos a vencer (próximos 7 días)
    from datetime import timedelta
    fecha_limite = timezone.now().date() + timedelta(days=7)
    compromisos_proximos = RespuestaAuditoria.objects.filter(
        asesor=request.user,
        fecha_compromiso__lte=fecha_limite,
        fecha_compromiso__gte=timezone.now().date(),
        estado__in=['respondido', 'en_seguimiento']
    ).count()
    
    # Promedio de puntaje
    promedio_puntaje = Auditoria.objects.filter(
        agente=request.user
    ).aggregate(
        promedio=Avg('puntaje_total')
    )['promedio'] or 0
    
    context = {
        'total_auditorias': total_auditorias,
        'auditorias_recientes': auditorias_recientes,
        'indicadores_pendientes': indicadores_pendientes,
        'respuestas_seguimiento': respuestas_seguimiento,
        'compromisos_proximos': compromisos_proximos,
        'promedio_puntaje': round(promedio_puntaje, 2),
    }
    
    return render(request, 'calidad/asesores/dashboard_asesor.html', context)


@login_required
@ip_permitida
@grupo_requerido('Administrador', 'Calidad')
def seleccionar_tipo_auditoria(request):
    """
    Vista para seleccionar el tipo de auditoría a crear
    """
    # Obtener estadísticas básicas para cada tipo de campaña
    stats_portabilidad = {
        'total': Auditoria.objects.filter(speech__tipo_campana='portabilidad').count(),
        'promedio': Auditoria.objects.filter(
            speech__tipo_campana='portabilidad'
        ).aggregate(avg=Avg('puntaje_total'))['avg'] or 0
    }
    
    stats_prepago = {
        'total': AuditoriaPrepago.objects.count(),
        'promedio': AuditoriaPrepago.objects.aggregate(avg=Avg('puntaje_total'))['avg'] or 0
    }
    
    stats_upgrade = {
        'total': AuditoriaUpgrade.objects.count(),
        'promedio': AuditoriaUpgrade.objects.aggregate(avg=Avg('puntaje_total'))['avg'] or 0
    }
    
    context = {
        'stats_portabilidad': stats_portabilidad,
        'stats_prepago': stats_prepago,
        'stats_upgrade': stats_upgrade,
    }
    
    return render(request, 'calidad/auditorias/seleccionar_tipo_auditoria.html', context)


# ============================================
# Vistas para Matrices de Calidad Específicas
# ============================================

@login_required
@ip_permitida
@grupo_requerido('Administrador', 'Calidad')
def lista_matriz_prepago(request):
    """
    Vista para listar matrices de calidad específicas de Prepago
    """
    # Obtener el filtro de tipología si existe
    tipologia_filtro = request.GET.get('tipologia', '')
    
    # Obtener el filtro de mostrar inactivos
    mostrar_inactivos = request.GET.get('mostrar_inactivos', '') == 'true'
    
    # Obtener todos los indicadores ordenados por tipología, categoría e indicador
    matriz_list = MatrizCalidadPrepago.objects.all().order_by('tipologia', 'categoria', 'indicador')
    
    # Aplicar filtro de tipología si se especificó
    if tipologia_filtro in dict(MatrizCalidadPrepago.TIPOLOGIA_CHOICES).keys():
        matriz_list = matriz_list.filter(tipologia=tipologia_filtro)
    
    # Aplicar filtro de activos/inactivos
    if not mostrar_inactivos:
        matriz_list = matriz_list.filter(activo=True)
    
    # Agrupar indicadores por tipología
    indicadores_por_tipologia = {}
    for tipologia in dict(MatrizCalidadPrepago.TIPOLOGIA_CHOICES).keys():
        indicadores_por_tipologia[tipologia] = {
            'nombre': dict(MatrizCalidadPrepago.TIPOLOGIA_CHOICES)[tipologia],
            'indicadores': matriz_list.filter(tipologia=tipologia)
        }
    
    # Pasar el contexto a la plantilla
    context = {
        'indicadores_por_tipologia': indicadores_por_tipologia,
        'tipologia_actual': tipologia_filtro,
        'TIPOLOGIA_CHOICES': MatrizCalidadPrepago.TIPOLOGIA_CHOICES,
        'mostrar_inactivos': mostrar_inactivos,
        'tipo_campana': 'prepago',
        'titulo': 'Matriz de Calidad - Prepago',
    }
    return render(request, 'calidad/matriz/lista_matriz_especifica.html', context)


@login_required
@ip_permitida
@grupo_requerido('Administrador', 'Calidad')
def crear_editar_matriz_prepago(request, id=None):
    """
    Vista para crear o editar matrices de calidad de Prepago
    """
    if id:
        matriz = get_object_or_404(MatrizCalidadPrepago, id=id)
        titulo = 'Editar Indicador Prepago'
        mensaje_exito = 'Indicador de prepago actualizado correctamente'
        es_edicion = True
    else:
        matriz = None
        titulo = 'Nuevo Indicador Prepago'
        mensaje_exito = 'Indicador de prepago creado correctamente'
        es_edicion = False

    if request.method == 'POST':
        form = MatrizCalidadPrepagoForm(request.POST, instance=matriz)
        if form.is_valid():
            indicador = form.save(commit=False)
            if not es_edicion:
                indicador.usuario_creacion = request.user
            indicador.save()
            messages.success(request, mensaje_exito)
            if 'guardar_y_agregar_otro' in request.POST:
                return redirect('calidad:crear_matriz_prepago')
            return redirect('calidad:lista_matriz_prepago')
    else:
        form = MatrizCalidadPrepagoForm(instance=matriz)

    context = {
        'form': form,
        'es_edicion': es_edicion,
        'titulo': titulo,
        'subtitulo': 'Complete los datos del indicador para prepago',
        'tipo_campana': 'prepago',
    }
    return render(request, 'calidad/matriz/form_matriz_especifica.html', context)


@login_required
@ip_permitida
@grupo_requerido('Administrador', 'Calidad')
def toggle_matriz_prepago_activo(request, id):
    """
    Vista para activar/desactivar matrices de calidad de Prepago
    """
    matriz = get_object_or_404(MatrizCalidadPrepago, id=id)
    matriz.activo = not matriz.activo
    matriz.save()
    
    # Si es una petición AJAX, devolver respuesta JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'activo': matriz.activo
        })
    
    return redirect('calidad:lista_matriz_prepago')


@login_required
@ip_permitida
@grupo_requerido('Administrador', 'Calidad')
def lista_matriz_upgrade(request):
    """
    Vista para listar matrices de calidad específicas de Upgrade
    """
    # Obtener el filtro de tipología si existe
    tipologia_filtro = request.GET.get('tipologia', '')
    
    # Obtener el filtro de mostrar inactivos
    mostrar_inactivos = request.GET.get('mostrar_inactivos', '') == 'true'
    
    # Obtener todos los indicadores ordenados por tipología, categoría e indicador
    matriz_list = MatrizCalidadUpgrade.objects.all().order_by('tipologia', 'categoria', 'indicador')
    
    # Aplicar filtro de tipología si se especificó
    if tipologia_filtro in dict(MatrizCalidadUpgrade.TIPOLOGIA_CHOICES).keys():
        matriz_list = matriz_list.filter(tipologia=tipologia_filtro)
    
    # Aplicar filtro de activos/inactivos
    if not mostrar_inactivos:
        matriz_list = matriz_list.filter(activo=True)
    
    # Agrupar indicadores por tipología
    indicadores_por_tipologia = {}
    for tipologia in dict(MatrizCalidadUpgrade.TIPOLOGIA_CHOICES).keys():
        indicadores_por_tipologia[tipologia] = {
            'nombre': dict(MatrizCalidadUpgrade.TIPOLOGIA_CHOICES)[tipologia],
            'indicadores': matriz_list.filter(tipologia=tipologia)
        }
    
    # Pasar el contexto a la plantilla
    context = {
        'indicadores_por_tipologia': indicadores_por_tipologia,
        'tipologia_actual': tipologia_filtro,
        'TIPOLOGIA_CHOICES': MatrizCalidadUpgrade.TIPOLOGIA_CHOICES,
        'mostrar_inactivos': mostrar_inactivos,
        'tipo_campana': 'upgrade',
        'titulo': 'Matriz de Calidad - Upgrade',
    }
    return render(request, 'calidad/matriz/lista_matriz_especifica.html', context)


@login_required
@ip_permitida
@grupo_requerido('Administrador', 'Calidad')
def crear_editar_matriz_upgrade(request, id=None):
    """
    Vista para crear o editar matrices de calidad de Upgrade
    """
    if id:
        matriz = get_object_or_404(MatrizCalidadUpgrade, id=id)
        titulo = 'Editar Indicador Upgrade'
        mensaje_exito = 'Indicador de upgrade actualizado correctamente'
        es_edicion = True
    else:
        matriz = None
        titulo = 'Nuevo Indicador Upgrade'
        mensaje_exito = 'Indicador de upgrade creado correctamente'
        es_edicion = False

    if request.method == 'POST':
        form = MatrizCalidadUpgradeForm(request.POST, instance=matriz)
        if form.is_valid():
            indicador = form.save(commit=False)
            if not es_edicion:
                indicador.usuario_creacion = request.user
            indicador.save()
            messages.success(request, mensaje_exito)
            if 'guardar_y_agregar_otro' in request.POST:
                return redirect('calidad:crear_matriz_upgrade')
            return redirect('calidad:lista_matriz_upgrade')
    else:
        form = MatrizCalidadUpgradeForm(instance=matriz)

    context = {
        'form': form,
        'es_edicion': es_edicion,
        'titulo': titulo,
        'subtitulo': 'Complete los datos del indicador para upgrade',
        'tipo_campana': 'upgrade',
    }
    return render(request, 'calidad/matriz/form_matriz_especifica.html', context)


@login_required
@ip_permitida
@grupo_requerido('Administrador', 'Calidad')
def toggle_matriz_upgrade_activo(request, id):
    """
    Vista para activar/desactivar matrices de calidad de Upgrade
    """
    matriz = get_object_or_404(MatrizCalidadUpgrade, id=id)
    matriz.activo = not matriz.activo
    matriz.save()
    
    # Si es una petición AJAX, devolver respuesta JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'activo': matriz.activo
        })
    
    return redirect('calidad:lista_matriz_upgrade')
