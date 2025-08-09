#!/usr/bin/env python
"""
Script de prueba para verificar el funcionamiento del formulario VentaTarjetaPlataForm
con todos los campos llenos.
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crea_online_crm.settings')
django.setup()

from tarjeta_plata.models import VentaTarjetaPlata
from tarjeta_plata.forms import VentaTarjetaPlataForm

def test_formulario_completo():
    """
    Prueba el formulario con todos los campos llenos
    """
    print("=== PRUEBA DE FORMULARIO COMPLETO ===")
    
    # Datos de prueba completos
    datos_completos = {
        'item': 'ITEM001',
        'nombre': 'JUAN PÉREZ GARCÍA',
        'ine': '1234567890123456',
        'rfc': 'PEGJ850101ABC',
        'telefono': '5551234567',
        'correo': 'juan.perez@email.com',
        'direccion': 'CALLE FALSA 123, COLONIA CENTRO',
        'codigo_postal': '12345',
        'usuario_c8': 'USER001',
        'entrega': 'domicilio',
        'dn': 'DN001',
        'estado_republica': 'CDMX',
        'ingreso_mensual_cliente': '15000.00',
        'resultado': 'aprobado',
        'observaciones': 'Cliente con buen historial crediticio'
    }
    
    print("\n1. Creando formulario con datos completos...")
    form = VentaTarjetaPlataForm(data=datos_completos)
    
    print("\n2. Validando formulario...")
    if form.is_valid():
        print("✅ Formulario válido")
        print("\n3. Datos limpios del formulario:")
        for campo, valor in form.cleaned_data.items():
            print(f"   {campo}: {valor}")
        
        # Simular guardado
        print("\n4. Simulando guardado...")
        try:
            # No guardamos realmente, solo validamos que se puede crear
            venta = form.save(commit=False)
            print(f"✅ Venta creada exitosamente (simulación)")
            print(f"   ID PREAP generado: {venta.generar_id_preap()}")
            print(f"   Nombre: {venta.nombre}")
            print(f"   RFC: {venta.rfc}")
            print(f"   Teléfono: {venta.telefono}")
            print(f"   Correo: {venta.correo}")
            
        except Exception as e:
            print(f"❌ Error al crear venta: {str(e)}")
            
    else:
        print("❌ Formulario inválido")
        print("\nErrores encontrados:")
        for campo, errores in form.errors.items():
            print(f"   {campo}: {errores}")
    
    print("\n5. Verificando campos requeridos en HTML...")
    form_html = VentaTarjetaPlataForm()
    campos_requeridos = ['item', 'nombre', 'ine', 'rfc', 'telefono', 'correo', 'direccion', 'codigo_postal']
    
    for campo in campos_requeridos:
        widget = form_html.fields[campo].widget
        attrs = widget.attrs
        if 'required' in attrs and attrs['required']:
            print(f"   ✅ {campo}: tiene atributo required")
        else:
            print(f"   ❌ {campo}: NO tiene atributo required")
    
    print("\n=== FIN DE PRUEBA ===")

def test_validacion_javascript():
    """
    Simula la validación que hace el JavaScript
    """
    print("\n=== PRUEBA DE VALIDACIÓN JAVASCRIPT ===")
    
    # Datos que simularían venir del formulario web
    datos_web = {
        'item': 'ITEM001',
        'nombre': 'JUAN PÉREZ GARCÍA',
        'ine': '1234567890123456',
        'rfc': 'PEGJ850101ABC',
        'telefono': '5551234567',
        'correo': 'juan.perez@email.com',
        'direccion': 'CALLE FALSA 123, COLONIA CENTRO',
        'codigo_postal': '12345',
        'usuario_c8': 'USER001',
        'entrega': 'domicilio',
        'dn': 'DN001',
        'estado_republica': 'CDMX',
        'ingreso_mensual_cliente': '15000.00',
        'resultado': 'aprobado',
        'observaciones': 'Cliente con buen historial crediticio'
    }
    
    print("\n1. Simulando validación JavaScript...")
    
    # Validar RFC (como lo hace el JavaScript)
    rfc = datos_web['rfc']
    import re
    rfc_pattern = r'^[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}$'
    if re.match(rfc_pattern, rfc):
        print(f"   ✅ RFC válido: {rfc}")
    else:
        print(f"   ❌ RFC inválido: {rfc}")
    
    # Validar código postal (como lo hace el JavaScript)
    cp = datos_web['codigo_postal']
    if len(cp) == 5 and cp.isdigit():
        print(f"   ✅ Código postal válido: {cp}")
    else:
        print(f"   ❌ Código postal inválido: {cp}")
    
    # Verificar campos requeridos
    campos_requeridos = ['item', 'nombre', 'ine', 'rfc', 'telefono', 'correo', 'direccion', 'codigo_postal']
    todos_llenos = True
    
    for campo in campos_requeridos:
        valor = datos_web.get(campo, '').strip()
        if not valor:
            print(f"   ❌ Campo requerido vacío: {campo}")
            todos_llenos = False
        else:
            print(f"   ✅ Campo requerido lleno: {campo} = {valor}")
    
    if todos_llenos:
        print("\n   ✅ Todos los campos requeridos están llenos")
        print("   ✅ El formulario debería enviarse correctamente")
    else:
        print("\n   ❌ Faltan campos requeridos")
        print("   ❌ El JavaScript debería prevenir el envío")
    
    print("\n=== FIN DE VALIDACIÓN JAVASCRIPT ===")

if __name__ == '__main__':
    test_formulario_completo()
    test_validacion_javascript()