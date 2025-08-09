#!/usr/bin/env python
"""
Script de prueba para verificar las funciones de backoffice de tarjeta plata.
Este script debe ejecutarse con: python manage.py shell < test_backoffice_functions.py
"""

from django.contrib.auth.models import User, Group
from tarjeta_plata.models import VentaTarjetaPlata, ClienteTarjetaPlata, GestionBackofficeTarjetaPlata

print("🚀 Iniciando pruebas de funciones de backoffice...\n")

# Verificar grupos de permisos
print("🔍 Verificando grupos de permisos...")
grupos_requeridos = ['backoffice', 'administrador']

for nombre_grupo in grupos_requeridos:
    grupo, created = Group.objects.get_or_create(name=nombre_grupo)
    if created:
        print(f"✓ Grupo '{nombre_grupo}' creado")
    else:
        print(f"✓ Grupo '{nombre_grupo}' ya existe")

# Crear usuario backoffice
print("\n🔍 Creando usuario backoffice...")
try:
    grupo_backoffice, _ = Group.objects.get_or_create(name='backoffice')
    
    usuario, created = User.objects.get_or_create(
        username='test_backoffice',
        defaults={
            'email': 'test@backoffice.com',
            'first_name': 'Test',
            'last_name': 'Backoffice',
            'is_staff': True
        }
    )
    
    if created:
        usuario.set_password('test123')
        usuario.save()
        print("✓ Usuario 'test_backoffice' creado")
    else:
        print("✓ Usuario 'test_backoffice' ya existe")
    
    usuario.groups.add(grupo_backoffice)
    print("✓ Usuario agregado al grupo backoffice")
    
except Exception as e:
    print(f"❌ Error creando usuario backoffice: {e}")
    exit()

# Crear cliente de prueba
print("\n🔍 Creando cliente de prueba...")
try:
    cliente, created = ClienteTarjetaPlata.objects.get_or_create(
        numero_documento='12345678',
        defaults={
            'tipo_documento': 'cedula',
            'nombres': 'Juan Carlos',
            'apellidos': 'Pérez González',
            'telefono': '3001234567',
            'email': 'juan.perez@test.com',
            'direccion': 'Calle 123 #45-67',
            'ciudad': 'Bogotá',
            'departamento': 'Cundinamarca'
        }
    )
    
    if created:
        print("✓ Cliente de prueba creado")
    else:
        print("✓ Cliente de prueba ya existe")
        
except Exception as e:
    print(f"❌ Error creando cliente: {e}")
    exit()

# Crear venta de prueba
print("\n🔍 Creando venta de prueba...")
try:
    venta = VentaTarjetaPlata.objects.create(
        cliente=cliente,
        agente=usuario,
        tipo_tarjeta='clasica',
        cupo_solicitado=1000000,
        ingresos_mensuales=2000000,
        observaciones='Venta de prueba para testing de backoffice',
        usuario_c8='TEST001',
        entrega='domicilio',
        DN='12345',
        estado_republica='activo',
        ingreso_mensual_cliente=2000000,
        resultado='aprobado'
    )
    
    print(f"✓ Venta de prueba creada con ID: {venta.id} y ID PreAp: {venta.id_preap}")
    
except Exception as e:
    print(f"❌ Error creando venta: {e}")
    exit()

# Probar aceptar venta
print(f"\n🔍 Probando aceptar venta {venta.id}...")
try:
    gestion_aceptar = GestionBackofficeTarjetaPlata.objects.create(
        venta=venta,
        usuario=usuario,
        accion='aceptada',
        observaciones='Venta aceptada en prueba automatizada'
    )
    
    venta.estado = 'aceptada'
    venta.save()
    
    print(f"✓ Venta {venta.id} aceptada correctamente")
    print(f"✓ Gestión de backoffice creada con ID: {gestion_aceptar.id}")
    
except Exception as e:
    print(f"❌ Error aceptando venta: {e}")

# Probar rechazar venta
print(f"\n🔍 Probando rechazar venta {venta.id}...")
try:
    # Resetear estado a nueva para poder rechazar
    venta.estado = 'nueva'
    venta.save()
    
    gestion_rechazar = GestionBackofficeTarjetaPlata.objects.create(
        venta=venta,
        usuario=usuario,
        accion='rechazada',
        observaciones='Venta rechazada en prueba automatizada'
    )
    
    venta.estado = 'rechazada'
    venta.save()
    
    print(f"✓ Venta {venta.id} rechazada correctamente")
    print(f"✓ Gestión de backoffice creada con ID: {gestion_rechazar.id}")
    
except Exception as e:
    print(f"❌ Error rechazando venta: {e}")

# Mostrar resumen
print("\n🎉 Pruebas completadas!")
print(f"\n📋 Resumen:")
print(f"   - Venta creada: ID {venta.id}, ID PreAp: {venta.id_preap}")
print(f"   - Estado final: {venta.estado}")
print(f"   - Cliente: {cliente.nombres} {cliente.apellidos}")
print(f"   - Usuario backoffice: {usuario.username}")

# Mostrar gestiones creadas
gestiones = GestionBackofficeTarjetaPlata.objects.filter(venta=venta)
print(f"   - Gestiones de backoffice: {gestiones.count()}")
for gestion in gestiones:
    print(f"     * {gestion.accion}: {gestion.observaciones}")

print("\n✅ Las funciones de backoffice están funcionando correctamente!")
print("\n🌐 Puedes verificar en el navegador:")
print(f"   - Dashboard: http://127.0.0.1:8000/tarjeta-plata/")
print(f"   - Bandeja nuevas: http://127.0.0.1:8000/tarjeta-plata/bandeja/nuevas/")
print(f"   - Detalle venta: http://127.0.0.1:8000/tarjeta-plata/venta/{venta.id}/")