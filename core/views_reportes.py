from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from datetime import datetime, timedelta
import pandas as pd

from .models import Cliente, Gestion, AcuerdoPago, CuotaAcuerdo

# Diccionario con los campos disponibles para cada tipo de reporte
CAMPOS_DISPONIBLES = {
    'clientes': [
        ('documento', 'Documento'),
        ('nombre_completo', 'Nombre Completo'),
        ('deuda_total', 'Deuda Total'),
        ('total_dias_mora', 'Días de Mora'),
        ('telefono_celular', 'Teléfono'),
        ('email', 'Email'),
        ('estado', 'Estado'),
        ('fecha_registro', 'Fecha de Registro'),
    ],
    'gestiones': [
        ('fecha_hora_gestion', 'Fecha y Hora'),
        ('cliente__nombre_completo', 'Cliente'),
        ('tipo_gestion_n1', 'Tipo de Gestión'),
        ('estado_contacto', 'Estado de Contacto'),
        ('usuario_gestion__username', 'Usuario'),
        ('comentarios', 'Comentarios'),
        ('acuerdos__monto_total', 'Monto Acuerdo'),
        ('acuerdos__numero_cuotas', 'Número de Cuotas'),
        ('acuerdos__fecha_creacion', 'Fecha Acuerdo'),
        ('acuerdos__estado', 'Estado Acuerdo'),
    ],
    'acuerdos': [
        ('id', 'ID Acuerdo'),
        ('cliente__nombre_completo', 'Cliente'),
        ('monto_total', 'Monto Total'),
        ('numero_cuotas', 'Número de Cuotas'),
        ('estado', 'Estado'),
        ('fecha_creacion', 'Fecha de Creación'),
        ('fecha_vencimiento', 'Fecha de Vencimiento'),
    ],
    'pagos': [
        ('id', 'ID Cuota'),
        ('acuerdo__cliente__nombre_completo', 'Cliente'),
        ('monto', 'Monto'),
        ('fecha_pago', 'Fecha de Pago'),
        ('fecha_vencimiento', 'Fecha de Vencimiento'),
        ('estado', 'Estado'),
        ('medio_pago', 'Medio de Pago'),
    ]
}

@login_required
def reportes(request):
    # Obtener parámetros de filtro comunes
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    tipo_reporte = request.GET.get('tipo_reporte', 'clientes')
    
    # Obtener campos seleccionados o usar todos por defecto
    campos_seleccionados = request.GET.getlist('campos')
    if not campos_seleccionados and tipo_reporte in CAMPOS_DISPONIBLES:
        campos_seleccionados = [campo[0] for campo in CAMPOS_DISPONIBLES[tipo_reporte]]
    
    # Establecer fechas por defecto (últimos 30 días)
    if not fecha_fin:
        fecha_fin = timezone.now().strftime('%Y-%m-%d')
    if not fecha_inicio:
        fecha_inicio = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Inicializar contexto
    context = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'tipo_reporte': tipo_reporte,
        'seccion_activa': 'reportes',
        'CAMPOS_DISPONIBLES': CAMPOS_DISPONIBLES.get(tipo_reporte, []),
        'campos_seleccionados': campos_seleccionados,
    }
    
    # Obtener datos según el tipo de reporte
    if tipo_reporte == 'clientes':
        # Lógica para reporte de clientes
        clientes = Cliente.objects.all()
        
        # Aplicar filtros
        if fecha_inicio and fecha_fin:
            clientes = clientes.filter(
                fecha_registro__date__range=[fecha_inicio, fecha_fin]
            )
            
        datos = clientes
        
    elif tipo_reporte == 'gestiones':
        # Lógica para reporte de gestiones
        gestiones = Gestion.objects.select_related('cliente').all()
        
        if fecha_inicio and fecha_fin:
            gestiones = gestiones.filter(
                fecha_hora_gestion__date__range=[fecha_inicio, fecha_fin]
            )
            
        context['datos'] = gestiones[:100]
        context['total_registros'] = gestiones.count()
        
    elif tipo_reporte == 'acuerdos':
        # Lógica para reporte de acuerdos
        acuerdos = AcuerdoPago.objects.select_related('cliente').all()
        
        if fecha_inicio and fecha_fin:
            acuerdos = acuerdos.filter(
                fecha_creacion__date__range=[fecha_inicio, fecha_fin]
            )
            
        context['datos'] = acuerdos[:100]
        context['total_registros'] = acuerdos.count()
        
    elif tipo_reporte == 'pagos':
        # Lógica para reporte de pagos
        pagos = CuotaAcuerdo.objects.select_related('acuerdo__cliente').filter(
            estado='pagada'
        )
        
        if fecha_inicio and fecha_fin:
            pagos = pagos.filter(
                fecha_pago__date__range=[fecha_inicio, fecha_fin]
            )
            
        context['datos'] = pagos[:100]
        context['total_registros'] = pagos.count()
    
    return render(request, 'core/reportes/reportes.html', context)

@login_required
def exportar_excel(request):
    if request.method == 'POST':
        tipo_reporte = request.POST.get('tipo_reporte', 'clientes')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        campos_seleccionados = request.POST.getlist('campos')
    else:
        # Si por alguna razón se accede por GET, redirigir a la página de reportes
        return redirect('core:reportes')
    
    # Crear el libro de Excel
    wb = Workbook()
    ws = wb.active
    ws.title = tipo_reporte.capitalize()
    
    # Estilos para el encabezado
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    # Obtener etiquetas de los campos seleccionados
    if not campos_seleccionados and tipo_reporte in CAMPOS_DISPONIBLES:
        campos_seleccionados = [campo[0] for campo in CAMPOS_DISPONIBLES[tipo_reporte]]
    
    # Mapeo de campos a funciones de obtención de valor
    def get_valor(objeto, campo, valor_default=''):
        try:
            # Manejar campos con relaciones (usando __ como separador)
            if '__' in campo:
                partes = campo.split('__')
                obj = objeto
                
                for i, parte in enumerate(partes):
                    if obj is None:
                        return valor_default
                    
                    # Obtener el atributo del objeto actual
                    obj = getattr(obj, parte, None)
                    
                    # Si es None, retornar valor por defecto
                    if obj is None:
                        return valor_default
                    
                    # Si es un queryset, obtener el primer elemento
                    if hasattr(obj, 'all') and not isinstance(obj, (str, int, float, bool, dict, list)):
                        if hasattr(obj, 'first'):
                            obj = obj.first()
                            if obj is None:
                                return valor_default
                
                # Si llegamos aquí, devolver el valor final
                if hasattr(obj, '__str__'):
                    return str(obj)
                return obj if obj is not None else valor_default
            
            # Manejar campos directos
            valor = getattr(objeto, campo, valor_default)
            
            # Si es una fecha/hora, formatear sin microsegundos
            if hasattr(valor, 'strftime'):
                return valor.strftime('%Y-%m-%d %H:%M:%S')
            # Si es un objeto, obtener su representación como string
            elif hasattr(valor, '__str__') and not isinstance(valor, (str, int, float, bool)):
                return str(valor)
                
            return valor if valor is not None else valor_default
                
        except Exception as e:
            print(f"Error al obtener valor para {campo}: {str(e)}")
            return valor_default
    
    # Obtener datos según el tipo de reporte
    if tipo_reporte == 'clientes':
        # Obtener datos
        queryset = Cliente.objects.all()
        if fecha_inicio and fecha_fin:
            queryset = queryset.filter(
                fecha_registro__date__range=[fecha_inicio, fecha_fin]
            )
        
        # Escribir encabezados
        for col_num, campo in enumerate(campos_seleccionados, 1):
            # Buscar la etiqueta del campo
            etiqueta = next((etq for c, etq in CAMPOS_DISPONIBLES[tipo_reporte] if c == campo), campo.replace('_', ' ').title())
            cell = ws.cell(row=1, column=col_num, value=etiqueta)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = alignment
        
        # Escribir datos
        for row_num, obj in enumerate(queryset, 2):
            for col_num, campo in enumerate(campos_seleccionados, 1):
                valor = get_valor(obj, campo)
                ws.cell(row=row_num, column=col_num, value=valor)
    
    elif tipo_reporte == 'gestiones':
        # Precargar relaciones para mejorar el rendimiento
        # Primero aplicar los filtros
        queryset = Gestion.objects.select_related('cliente', 'usuario_gestion').prefetch_related('acuerdos')
        
        if fecha_inicio and fecha_fin:
            queryset = queryset.filter(
                fecha_hora_gestion__date__range=[fecha_inicio, fecha_fin]
            )
        
        # Forzar la carga de los acuerdos para evitar consultas adicionales
        gestiones_con_acuerdos = []
        for gestion in queryset:
            gestion.acuerdos_list = list(gestion.acuerdos.all())
            if gestion.acuerdos_list:
                gestion.acuerdo = gestion.acuerdos_list[0]
            else:
                gestion.acuerdo = None
            gestiones_con_acuerdos.append(gestion)
            
        queryset = gestiones_con_acuerdos
        
        print(f"Total de gestiones encontradas: {len(queryset)}")
        
        # Escribir encabezados
        for col_num, campo in enumerate(campos_seleccionados, 1):
            etiqueta = next((etq for c, etq in CAMPOS_DISPONIBLES[tipo_reporte] if c == campo), campo.replace('_', ' ').title())
            cell = ws.cell(row=1, column=col_num, value=etiqueta)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = alignment
        
        # Escribir datos
        for row_num, obj in enumerate(queryset, 2):
            # Precargar manualmente la relación de acuerdos si es necesario
            if 'acuerdos__' in ' '.join(campos_seleccionados):
                if not hasattr(obj, '_acuerdos_cargados'):
                    obj.acuerdos_list = list(obj.acuerdos.all())
                    obj._acuerdos_cargados = True
                # Usar el primer acuerdo si existe
                if hasattr(obj, 'acuerdos_list') and obj.acuerdos_list:
                    obj.acuerdo = obj.acuerdos_list[0]
                else:
                    obj.acuerdo = None
            
            for col_num, campo in enumerate(campos_seleccionados, 1):
                valor = get_valor(obj, campo)
                
                # Manejar valores nulos
                if valor is None:
                    valor = ''
                # Manejar fechas
                elif hasattr(valor, 'strftime'):
                    # Convertir a string directamente, lo que ignora la zona horaria
                    valor = valor.strftime('%Y-%m-%d %H:%M:%S')
                # Manejar booleanos
                elif isinstance(valor, bool):
                    valor = 'Sí' if valor else 'No'
                # Para relaciones, asegurarse de obtener el string
                elif hasattr(valor, '__str__') and not isinstance(valor, (str, int, float, bool)):
                    valor = str(valor)
                
                print(f"Fila {row_num}, Col {col_num} ({campo}): {valor}")
                ws.cell(row=row_num, column=col_num, value=valor)
    
    elif tipo_reporte == 'acuerdos':
        queryset = AcuerdoPago.objects.select_related('cliente').all()
        if fecha_inicio and fecha_fin:
            queryset = queryset.filter(
                fecha_creacion__date__range=[fecha_inicio, fecha_fin]
            )
        
        # Escribir encabezados
        for col_num, campo in enumerate(campos_seleccionados, 1):
            etiqueta = next((etq for c, etq in CAMPOS_DISPONIBLES[tipo_reporte] if c == campo), campo.replace('_', ' ').title())
            cell = ws.cell(row=1, column=col_num, value=etiqueta)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = alignment
        
        # Escribir datos
        for row_num, obj in enumerate(queryset, 2):
            for col_num, campo in enumerate(campos_seleccionados, 1):
                valor = get_valor(obj, campo)
                ws.cell(row=row_num, column=col_num, value=valor)
    
    elif tipo_reporte == 'pagos':
        queryset = CuotaAcuerdo.objects.select_related('acuerdo__cliente').all()
        if fecha_inicio and fecha_fin:
            queryset = queryset.filter(
                fecha_pago__date__range=[fecha_inicio, fecha_fin]
            )
        
        # Escribir encabezados
        for col_num, campo in enumerate(campos_seleccionados, 1):
            etiqueta = next((etq for c, etq in CAMPOS_DISPONIBLES[tipo_reporte] if c == campo), campo.replace('_', ' ').title())
            cell = ws.cell(row=1, column=col_num, value=etiqueta)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = alignment
        
        # Escribir datos
        for row_num, obj in enumerate(queryset, 2):
            for col_num, campo in enumerate(campos_seleccionados, 1):
                valor = get_valor(obj, campo)
                ws.cell(row=row_num, column=col_num, value=valor)
    
    # Ajustar ancho de columnas
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        
        adjusted_width = (max_length + 2) * 1.2
        ws.column_dimensions[column].width = adjusted_width if adjusted_width < 40 else 40
    
    # Crear respuesta HTTP con el archivo Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=reporte_{tipo_reporte}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    wb.save(response)
    
    return response
