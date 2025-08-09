#!/usr/bin/env python
"""
Script de prueba para verificar el funcionamiento del formulario de VentaTarjetaPlata
con todos los campos llenos.

Este script simula el envío de un formulario completo para verificar que
todos los campos se guarden correctamente en la base de datos.
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crea_online_crm.settings')
django.setup()

from django.contrib.auth.models import User
from tarjeta_plata.models import VentaTarjetaPlata
from tarjeta_plata.forms import VentaTarjetaPlataForm

def test_formulario_completo():
    """
    Prueba el formulario con todos los campos llenos para verificar
    que se guarden correctamente.
    """
    print("=== PRUEBA DEL FORMULARIO TARJETA PLATA ===")
    print("Probando formulario con todos los campos llenos...\n")
    
    # Datos de prueba completos
    datos_prueba = {
        'item': 'TEST-001',
        'nombre': 'JUAN CARLOS PÉREZ GONZÁLEZ',
        'ine': '1234567890123456',
        'rfc': 'PEGJ850315ABC',
        'telefono': '5551234567',
        'correo': 'juan.perez@ejemplo.com',
        'direccion': 'Calle Falsa 123, Colonia Centro, Ciudad de México',
        'codigo_postal': '06000',
        'usuario_c8': 'usuario_test_c8',
        'entrega': 'domicilio',
        'dn': 'DN123456',
        'estado_republica': 'Ciudad de México',
        'ingreso_mensual_cliente': '25000.00',
        'resultado': 'venta_bbd',
        'observaciones': 'Cliente interesado, llamar en horario matutino'
    }
    
    # Crear el formulario con los datos
    form = VentaTarjetaPlataForm(data=datos_prueba)
    
    print("1. Validando formulario...")
    if form.is_valid():
        print("   ✓ Formulario válido")
        
        # Obtener o crear un usuario de prueba
        try:
            usuario_test = User.objects.get(username='test_agent')
        except User.DoesNotExist:
            usuario_test = User.objects.create_user(
                username='test_agent',
                email='test@ejemplo.com',
                password='test123'
            )
            print("   ✓ Usuario de prueba creado")
        
        print("\n2. Guardando venta...")
        try:
            # Simular el guardado como en la vista
            venta = form.save(commit=False)
            venta.agente = usuario_test
            venta.save()
            
            print(f"   ✓ Venta guardada exitosamente con ID: {venta.id}")
            print(f"   ✓ ID PreAp generado: {venta.id_preap}")
            
            # Verificar que todos los campos se guardaron
            print("\n3. Verificando campos guardados:")
            campos_verificar = [
                ('item', venta.item),
                ('nombre', venta.nombre),
                ('ine', venta.ine),
                ('rfc', venta.rfc),
                ('telefono', venta.telefono),
                ('correo', venta.correo),
                ('direccion', venta.direccion),
                ('codigo_postal', venta.codigo_postal),
                ('usuario_c8', venta.usuario_c8),
                ('entrega', venta.entrega),
                ('dn', venta.dn),
                ('estado_republica', venta.estado_republica),
                ('ingreso_mensual_cliente', str(venta.ingreso_mensual_cliente) if venta.ingreso_mensual_cliente else None),
                ('resultado', venta.resultado),
                ('observaciones', venta.observaciones),
                ('agente', venta.agente.username),
                ('estado_venta', venta.estado_venta)
            ]
            
            todos_correctos = True
            for campo, valor in campos_verificar:
                if campo in datos_prueba:
                    esperado = datos_prueba[campo]
                    if str(valor) == str(esperado):
                        print(f"   ✓ {campo}: {valor}")
                    else:
                        print(f"   ✗ {campo}: esperado '{esperado}', obtenido '{valor}'")
                        todos_correctos = False
                else:
                    print(f"   ✓ {campo}: {valor} (campo automático)")
            
            if todos_correctos:
                print("\n🎉 ¡PRUEBA EXITOSA! Todos los campos se guardaron correctamente.")
            else:
                print("\n❌ Algunos campos no se guardaron correctamente.")
            
            # Limpiar: eliminar la venta de prueba
            print("\n4. Limpiando datos de prueba...")
            venta.delete()
            print("   ✓ Venta de prueba eliminada")
            
            return todos_correctos
            
        except Exception as e:
            print(f"   ✗ Error al guardar: {str(e)}")
            return False
    else:
        print("   ✗ Formulario inválido")
        print("   Errores encontrados:")
        for campo, errores in form.errors.items():
            print(f"     - {campo}: {', '.join(errores)}")
        return False

def test_campos_requeridos():
    """
    Prueba que los campos requeridos funcionen correctamente.
    """
    print("\n=== PRUEBA DE CAMPOS REQUERIDOS ===")
    
    # Datos incompletos (sin campos requeridos)
    datos_incompletos = {
        'usuario_c8': 'usuario_test',
        'observaciones': 'Solo campos opcionales'
    }
    
    form = VentaTarjetaPlataForm(data=datos_incompletos)
    
    if not form.is_valid():
        print("✓ Formulario correctamente rechazado por campos faltantes")
        campos_requeridos = ['item', 'nombre', 'ine', 'rfc', 'telefono', 'correo', 'direccion', 'codigo_postal']
        errores_encontrados = list(form.errors.keys())
        
        for campo in campos_requeridos:
            if campo in errores_encontrados:
                print(f"   ✓ Campo requerido '{campo}' validado correctamente")
            else:
                print(f"   ⚠ Campo '{campo}' debería ser requerido pero no se validó")
        
        return True
    else:
        print("✗ El formulario debería haber sido rechazado por campos faltantes")
        return False

if __name__ == '__main__':
    try:
        # Ejecutar pruebas
        resultado1 = test_formulario_completo()
        resultado2 = test_campos_requeridos()
        
        print("\n" + "="*50)
        if resultado1 and resultado2:
            print("🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
            print("El formulario de tarjeta plata funciona correctamente.")
        else:
            print("❌ ALGUNAS PRUEBAS FALLARON")
            print("Revisar los errores mostrados arriba.")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()