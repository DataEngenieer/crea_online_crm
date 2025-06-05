from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from .models import AcuerdoPago, CuotaAcuerdo, Cliente, Gestion
import json

@login_required
def registrar_pago_cuota(request, cuota_id):
    """Vista para registrar el pago de una cuota de acuerdo"""
    try:
        cuota = CuotaAcuerdo.objects.get(id=cuota_id)
    except CuotaAcuerdo.DoesNotExist:
        messages.error(request, 'La cuota especificada no existe.')
        return redirect('core:clientes')
    
    # Verificar que la cuota no esté ya pagada
    if cuota.estado == 'pagada':
        messages.warning(request, 'Esta cuota ya ha sido pagada anteriormente.')
        return redirect('core:detalle_cliente', documento_cliente=cuota.acuerdo.cliente.documento)
    
    if request.method == 'POST':
        fecha_pago = request.POST.get('fecha_pago')
        monto_pagado = request.POST.get('monto_pagado')
        observaciones = request.POST.get('observaciones')
        comprobante = request.FILES.get('comprobante')
        
        if not fecha_pago or not monto_pagado:
            messages.error(request, 'Debe proporcionar la fecha y el monto del pago.')
            return redirect('core:detalle_cliente', documento_cliente=cuota.acuerdo.cliente.documento)
        
        try:
            # Actualizar la cuota
            cuota.fecha_pago = fecha_pago
            cuota.monto_pagado = monto_pagado
            if observaciones:
                cuota.observaciones = observaciones
            if comprobante:
                cuota.comprobante = comprobante
            
            # Marcar como pagada y guardar
            cuota.estado = 'pagada'
            cuota.save()
            
            # Verificar si todas las cuotas del acuerdo están pagadas
            acuerdo = cuota.acuerdo
            if not acuerdo.cuotas.exclude(estado='pagada').exists():
                acuerdo.estado = 'completado'
                acuerdo.save()
                messages.success(request, f'¡Acuerdo de pago completado! Todas las cuotas han sido pagadas.')
            else:
                messages.success(request, f'Pago de cuota registrado correctamente.')
                
            # Registrar una gestión automática por el pago
            Gestion.objects.create(
                cliente=acuerdo.cliente,
                usuario_gestion=request.user,
                canal_contacto='sistema',
                estado_contacto='contacto_efectivo',
                tipo_gestion_n1='pagado',
                acuerdo_pago_realizado=True,
                fecha_pago_efectivo=fecha_pago,
                monto_acuerdo=monto_pagado,
                observaciones_generales=f"Pago registrado para cuota {cuota.numero_cuota} del acuerdo del {acuerdo.fecha_acuerdo}. {observaciones if observaciones else ''}"
            )
            
        except Exception as e:
            messages.error(request, f'Error al registrar el pago: {str(e)}')
        
        return redirect('core:detalle_cliente', documento_cliente=cuota.acuerdo.cliente.documento)
    
    # Si es GET, redirigir a la página de detalle del cliente
    return redirect('core:detalle_cliente', documento_cliente=cuota.acuerdo.cliente.documento)

@login_required
def registrar_multiple_pagos(request, acuerdo_id):
    """Vista para registrar múltiples pagos de cuotas en un acuerdo"""
    try:
        acuerdo = AcuerdoPago.objects.get(id=acuerdo_id)
    except AcuerdoPago.DoesNotExist:
        messages.error(request, 'El acuerdo especificado no existe.')
        return redirect('core:clientes')
    
    if request.method == 'POST':
        fecha_pago = request.POST.get('fecha_pago')
        comprobante = request.FILES.get('comprobante')
        observaciones = request.POST.get('observaciones')
        
        # Obtener las cuotas seleccionadas y sus montos
        cuotas_pagadas = []
        monto_total_pagado = 0
        
        try:
            cuotas_data = json.loads(request.POST.get('cuotas_data', '[]'))
            
            if not cuotas_data:
                messages.error(request, 'Debe seleccionar al menos una cuota para registrar el pago.')
                return redirect('core:detalle_cliente', documento_cliente=acuerdo.cliente.documento)
            
            if not fecha_pago:
                messages.error(request, 'Debe proporcionar la fecha del pago.')
                return redirect('core:detalle_cliente', documento_cliente=acuerdo.cliente.documento)
            
            # Procesar cada cuota seleccionada
            for cuota_data in cuotas_data:
                cuota_id = cuota_data.get('id')
                monto_pagado = cuota_data.get('monto')
                
                if not cuota_id or not monto_pagado:
                    continue
                
                try:
                    cuota = CuotaAcuerdo.objects.get(id=cuota_id, acuerdo=acuerdo)
                    
                    # Verificar que la cuota no esté ya pagada
                    if cuota.estado == 'pagada':
                        continue
                    
                    # Actualizar la cuota
                    cuota.fecha_pago = fecha_pago
                    cuota.monto_pagado = monto_pagado
                    if comprobante:
                        cuota.comprobante = comprobante
                    
                    # Marcar como pagada y guardar
                    cuota.estado = 'pagada'
                    cuota.save()
                    
                    cuotas_pagadas.append(cuota.numero_cuota)
                    monto_total_pagado += float(monto_pagado)
                    
                except CuotaAcuerdo.DoesNotExist:
                    continue
            
            # Verificar si se pagó alguna cuota
            if not cuotas_pagadas:
                messages.warning(request, 'No se registró ningún pago. Verifique que las cuotas seleccionadas sean válidas y no estén ya pagadas.')
                return redirect('core:detalle_cliente', documento_cliente=acuerdo.cliente.documento)
            
            # Verificar si todas las cuotas del acuerdo están pagadas
            if not acuerdo.cuotas.exclude(estado='pagada').exists():
                acuerdo.estado = 'completado'
                acuerdo.save()
                messages.success(request, f'¡Acuerdo de pago completado! Todas las cuotas han sido pagadas.')
            else:
                messages.success(request, f'Se registraron correctamente los pagos para {len(cuotas_pagadas)} cuota(s).')
            
            # Registrar una gestión automática por los pagos
            cuotas_str = ", ".join([f"#{num}" for num in cuotas_pagadas])
            Gestion.objects.create(
                cliente=acuerdo.cliente,
                usuario_gestion=request.user,
                canal_contacto='sistema',
                estado_contacto='contacto_efectivo',
                tipo_gestion_n1='pagado',
                acuerdo_pago_realizado=True,
                fecha_pago_efectivo=fecha_pago,
                monto_acuerdo=monto_total_pagado,
                observaciones_generales=f"Pago múltiple registrado para cuotas {cuotas_str} del acuerdo del {acuerdo.fecha_acuerdo}. {observaciones if observaciones else ''}"
            )
            
        except Exception as e:
            messages.error(request, f'Error al registrar los pagos: {str(e)}')
        
        return redirect('core:detalle_cliente', documento_cliente=acuerdo.cliente.documento)
    
    # Si es GET, obtener las cuotas pendientes del acuerdo
    cuotas_pendientes = acuerdo.cuotas.exclude(estado='pagada').order_by('numero_cuota')
    
    return render(request, 'core/modal_multiple_pagos.html', {
        'acuerdo': acuerdo,
        'cuotas_pendientes': cuotas_pendientes
    })

@login_required
def obtener_cuotas_acuerdo(request, acuerdo_id):
    """Obtiene las cuotas de un acuerdo y renderiza la plantilla modal_multiple_pagos.html"""
    try:
        acuerdo = AcuerdoPago.objects.get(id=acuerdo_id)
        cuotas = acuerdo.cuotas.exclude(estado='PAGADA').order_by('numero_cuota')
        
        # Si se solicita en formato JSON (para API)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            data = {
                'acuerdo': {
                    'id': acuerdo.id,
                    'fecha': acuerdo.fecha_acuerdo.strftime('%Y-%m-%d'),
                    'monto_total': float(acuerdo.monto_total),
                    'estado': acuerdo.get_estado_display(),
                },
                'cuotas': [
                    {
                        'id': cuota.id,
                        'numero': cuota.numero_cuota,
                        'monto': float(cuota.monto),
                        'fecha_vencimiento': cuota.fecha_vencimiento.strftime('%Y-%m-%d'),
                        'estado': cuota.get_estado_display()
                    }
                    for cuota in cuotas
                ]
            }
            return JsonResponse(data)
        
        # Si es una solicitud normal, renderizar la plantilla
        context = {
            'acuerdo': acuerdo,
            'cuotas': cuotas,
            'cliente': acuerdo.cliente,
            'titulo_pagina': f"Registrar Múltiples Pagos - {acuerdo.cliente.nombre_completo}"
        }
        
        return render(request, 'core/modal_multiple_pagos.html', context)
        
    except AcuerdoPago.DoesNotExist:
        messages.error(request, 'El acuerdo especificado no existe')
        # Redirigir a la página anterior o a la lista de acuerdos
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('core:acuerdos_pago')
    
    except Exception as e:
        messages.error(request, f'Error al procesar la solicitud: {str(e)}')
        # Redirigir a la página anterior o a la lista de acuerdos
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('core:acuerdos_pago')
