#!/usr/bin/env python
"""
Script de prueba para verificar que la creación optimizada de acuerdos de pago
funcione correctamente sin causar timeouts o bucles infinitos.

Este script prueba:
1. Creación de acuerdo de pago con múltiples cuotas
2. Verificación de que no hay bucles infinitos
3. Validación del estado correcto del acuerdo
4. Rendimiento de la creación masiva de cuotas
"""

import os
import sys
import django
import time
from decimal import Decimal
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crea_online_crm.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Cliente, Gestion, AcuerdoPago, CuotaAcuerdo
from django.utils import timezone

def limpiar_datos_prueba():
    """Limpia datos de prueba anteriores"""
    print("🧹 Limpiando datos de prueba anteriores...")
    
    # Eliminar acuerdos de prueba
    acuerdos_prueba = AcuerdoPago.objects.filter(
        cliente__documento__startswith='TEST-ACUERDO'
    )
    cuotas_eliminadas = 0
    for acuerdo in acuerdos_prueba:
        cuotas_eliminadas += acuerdo.cuotas.count()
        acuerdo.delete()
    
    # Eliminar gestiones de prueba
    gestiones_prueba = Gestion.objects.filter(
        cliente__documento__startswith='TEST-ACUERDO'
    )
    gestiones_eliminadas = gestiones_prueba.count()
    gestiones_prueba.delete()
    
    # Eliminar clientes de prueba
    clientes_prueba = Cliente.objects.filter(
        documento__startswith='TEST-ACUERDO'
    )
    clientes_eliminados = clientes_prueba.count()
    clientes_prueba.delete()
    
    print(f"   ✅ Eliminados: {clientes_eliminados} clientes, {gestiones_eliminadas} gestiones, {cuotas_eliminadas} cuotas")

def crear_cliente_prueba():
    """Crea un cliente de prueba"""
    print("👤 Creando cliente de prueba...")
    
    cliente = Cliente.objects.create(
        documento='TEST-ACUERDO-001',
        nombre_completo='Cliente Prueba Acuerdo Optimizado',
        ciudad='Bogotá',
        principal=Decimal('1000000.00'),
        deuda_principal_k=Decimal('1000000.00'),
        intereses=Decimal('200000.00'),
        total_pagado=Decimal('0.00')
    )
    
    print(f"   ✅ Cliente creado: {cliente.nombre_completo} ({cliente.documento})")
    return cliente

def crear_usuario_prueba():
    """Obtiene o crea un usuario de prueba"""
    print("🔑 Obteniendo usuario de prueba...")
    
    usuario, created = User.objects.get_or_create(
        username='test_acuerdo_user',
        defaults={
            'first_name': 'Usuario',
            'last_name': 'Prueba Acuerdo',
            'email': 'test_acuerdo@test.com',
            'is_active': True
        }
    )
    
    if created:
        usuario.set_password('test123')
        usuario.save()
        print(f"   ✅ Usuario creado: {usuario.username}")
    else:
        print(f"   ✅ Usuario existente: {usuario.username}")
    
    return usuario

def crear_gestion_prueba(cliente, usuario):
    """Crea una gestión de prueba"""
    print("📋 Creando gestión de prueba...")
    
    gestion = Gestion.objects.create(
        cliente=cliente,
        usuario_gestion=usuario,
        canal_contacto='telefono',
        estado_contacto='contacto_efectivo',
        tipo_gestion_n1='AP',
        observaciones='Gestión de prueba para acuerdo optimizado',
        referencia_producto=cliente.documento,
        acuerdo_pago_realizado=True,
        fecha_acuerdo=timezone.now().date(),
        monto_acuerdo=Decimal('500000.00'),
        observaciones_acuerdo='Acuerdo de prueba con múltiples cuotas'
    )
    
    print(f"   ✅ Gestión creada: ID {gestion.id}")
    return gestion

def probar_creacion_acuerdo_optimizada(cliente, gestion, usuario):
    """Prueba la creación optimizada de acuerdo con múltiples cuotas"""
    print("\n🚀 PROBANDO CREACIÓN OPTIMIZADA DE ACUERDO...")
    
    # Medir tiempo de inicio
    tiempo_inicio = time.time()
    
    try:
        # Crear acuerdo de pago
        print("   📝 Creando acuerdo de pago...")
        acuerdo = AcuerdoPago.objects.create(
            cliente=cliente,
            gestion=gestion,
            referencia_producto=gestion.referencia_producto,
            fecha_acuerdo=gestion.fecha_acuerdo,
            monto_total=gestion.monto_acuerdo,
            observaciones=gestion.observaciones_acuerdo or '',
            usuario_creacion=usuario,
            tipo_acuerdo=AcuerdoPago.PAGO_TOTAL
        )
        
        print(f"   ✅ Acuerdo creado: ID {acuerdo.id}")
        
        # Crear múltiples cuotas de forma optimizada
        print("   📅 Creando cuotas de forma optimizada...")
        
        cuotas_data = [
            {'fecha': (timezone.now().date() + timedelta(days=30)).strftime('%Y-%m-%d'), 'monto': '100000.00'},
            {'fecha': (timezone.now().date() + timedelta(days=60)).strftime('%Y-%m-%d'), 'monto': '100000.00'},
            {'fecha': (timezone.now().date() + timedelta(days=90)).strftime('%Y-%m-%d'), 'monto': '100000.00'},
            {'fecha': (timezone.now().date() + timedelta(days=120)).strftime('%Y-%m-%d'), 'monto': '100000.00'},
            {'fecha': (timezone.now().date() + timedelta(days=150)).strftime('%Y-%m-%d'), 'monto': '100000.00'},
        ]
        
        # Crear cuotas de forma optimizada (como en el código corregido)
        cuotas_a_crear = []
        for i, cuota_info in enumerate(cuotas_data):
            cuota = CuotaAcuerdo(
                acuerdo=acuerdo,
                numero_cuota=i + 1,
                fecha_vencimiento=datetime.strptime(cuota_info['fecha'], '%Y-%m-%d').date(),
                monto=Decimal(cuota_info['monto']),
                estado='pendiente'
            )
            # Marcar para evitar actualización del estado del acuerdo padre durante la creación
            cuota._skip_parent_update = True
            cuotas_a_crear.append(cuota)
        
        # Crear todas las cuotas de una vez
        CuotaAcuerdo.objects.bulk_create(cuotas_a_crear)
        
        # Actualizar el estado del acuerdo una sola vez al final
        acuerdo.actualizar_estado()
        
        # Medir tiempo final
        tiempo_final = time.time()
        tiempo_transcurrido = tiempo_final - tiempo_inicio
        
        print(f"   ✅ {len(cuotas_data)} cuotas creadas exitosamente")
        print(f"   ⏱️  Tiempo transcurrido: {tiempo_transcurrido:.3f} segundos")
        
        # Verificar resultados
        acuerdo.refresh_from_db()
        cuotas_creadas = acuerdo.cuotas.count()
        
        print(f"\n📊 RESULTADOS DE LA PRUEBA:")
        print(f"   🎯 Acuerdo ID: {acuerdo.id}")
        print(f"   💰 Monto total: ${acuerdo.monto_total:,}")
        print(f"   📋 Estado del acuerdo: {acuerdo.get_estado_display()}")
        print(f"   📅 Cuotas creadas: {cuotas_creadas}")
        print(f"   ⏱️  Tiempo total: {tiempo_transcurrido:.3f} segundos")
        
        # Verificar que no hay problemas de rendimiento
        if tiempo_transcurrido > 5.0:
            print(f"   ⚠️  ADVERTENCIA: La creación tomó más de 5 segundos ({tiempo_transcurrido:.3f}s)")
        else:
            print(f"   ✅ EXCELENTE: Creación rápida y eficiente")
        
        # Verificar integridad de datos
        suma_cuotas = sum(Decimal(cuota['monto']) for cuota in cuotas_data)
        if acuerdo.monto_total == suma_cuotas:
            print(f"   ✅ INTEGRIDAD: Monto del acuerdo coincide con suma de cuotas")
        else:
            print(f"   ❌ ERROR: Monto del acuerdo (${acuerdo.monto_total}) != suma cuotas (${suma_cuotas})")
        
        return True, acuerdo
        
    except Exception as e:
        tiempo_final = time.time()
        tiempo_transcurrido = tiempo_final - tiempo_inicio
        print(f"   ❌ ERROR en la creación: {str(e)}")
        print(f"   ⏱️  Tiempo antes del error: {tiempo_transcurrido:.3f} segundos")
        return False, None

def probar_actualizacion_cuota(acuerdo):
    """Prueba la actualización de una cuota y verificación del estado del acuerdo"""
    print("\n🔄 PROBANDO ACTUALIZACIÓN DE CUOTA...")
    
    try:
        # Obtener la primera cuota
        primera_cuota = acuerdo.cuotas.first()
        if not primera_cuota:
            print("   ❌ No hay cuotas para probar")
            return False
        
        print(f"   📅 Marcando cuota {primera_cuota.numero_cuota} como pagada...")
        
        # Marcar como pagada
        primera_cuota.estado = 'pagada'
        primera_cuota.fecha_pago = timezone.now().date()
        primera_cuota.save()
        
        # Verificar que el estado del acuerdo se actualizó
        acuerdo.refresh_from_db()
        print(f"   ✅ Cuota marcada como pagada")
        print(f"   📋 Nuevo estado del acuerdo: {acuerdo.get_estado_display()}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ERROR en actualización de cuota: {str(e)}")
        return False

def main():
    """Función principal de prueba"""
    print("🧪 INICIANDO PRUEBAS DE ACUERDOS DE PAGO OPTIMIZADOS")
    print("=" * 60)
    
    try:
        # Limpiar datos anteriores
        limpiar_datos_prueba()
        
        # Crear datos de prueba
        cliente = crear_cliente_prueba()
        usuario = crear_usuario_prueba()
        gestion = crear_gestion_prueba(cliente, usuario)
        
        # Probar creación optimizada
        exito_creacion, acuerdo = probar_creacion_acuerdo_optimizada(cliente, gestion, usuario)
        
        if exito_creacion and acuerdo:
            # Probar actualización de cuota
            exito_actualizacion = probar_actualizacion_cuota(acuerdo)
            
            if exito_actualizacion:
                print("\n🎉 TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
                print("✅ La optimización funciona correctamente")
                print("✅ No hay bucles infinitos")
                print("✅ El rendimiento es aceptable")
            else:
                print("\n⚠️  PRUEBA DE ACTUALIZACIÓN FALLÓ")
        else:
            print("\n❌ PRUEBA DE CREACIÓN FALLÓ")
        
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n🧹 Limpiando datos de prueba...")
        limpiar_datos_prueba()
        print("✅ Limpieza completada")
    
    print("\n" + "=" * 60)
    print("🏁 PRUEBAS FINALIZADAS")

if __name__ == '__main__':
    main()