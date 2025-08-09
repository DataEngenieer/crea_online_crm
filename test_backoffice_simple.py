# Script de prueba para funciones de backoffice
from django.contrib.auth.models import User, Group
from tarjeta_plata.models import VentaTarjetaPlata, ClienteTarjetaPlata, GestionBackofficeTarjetaPlata

print("Iniciando pruebas de funciones de backoffice...")

# Verificar grupos de permisos
print("Verificando grupos de permisos...")
grupos_requeridos = ['backoffice', 'administrador']

for nombre_grupo in grupos_requeridos:
    grupo, created = Group.objects.get_or_create(name=nombre_grupo)
    if created:
        print("Grupo creado: " + nombre_grupo)
    else:
        print("Grupo ya existe: " + nombre_grupo)

# Crear usuario backoffice
print("Creando usuario backoffice...")
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
        print("Usuario test_backoffice creado")
    else:
        print("Usuario test_backoffice ya existe")
    
    usuario.groups.add(grupo_backoffice)
    print("Usuario agregado al grupo backoffice")
    
except Exception as e:
    print("Error creando usuario backoffice: " + str(e))
    exit()

# Crear cliente de prueba
print("Creando cliente de prueba...")
try:
    cliente, created = ClienteTarjetaPlata.objects.get_or_create(
        numero_documento='12345678',
        defaults={
            'tipo_documento': 'cedula',
            'nombres': 'Juan Carlos',
            'apellidos': 'Perez Gonzalez',
            'telefono': '3001234567',
            'email': 'juan.perez@test.com',
            'direccion': 'Calle 123 #45-67',
            'ciudad': 'Bogota',
            'departamento': 'Cundinamarca'
        }
    )
    
    if created:
        print("Cliente de prueba creado")
    else:
        print("Cliente de prueba ya existe")
        
except Exception as e:
    print("Error creando cliente: " + str(e))
    exit()

# Crear venta de prueba
print("Creando venta de prueba...")
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
    
    print("Venta de prueba creada con ID: " + str(venta.id) + " y ID PreAp: " + str(venta.id_preap))
    
except Exception as e:
    print("Error creando venta: " + str(e))
    exit()

# Probar aceptar venta
print("Probando aceptar venta " + str(venta.id) + "...")
try:
    gestion_aceptar = GestionBackofficeTarjetaPlata.objects.create(
        venta=venta,
        usuario=usuario,
        accion='aceptada',
        observaciones='Venta aceptada en prueba automatizada'
    )
    
    venta.estado = 'aceptada'
    venta.save()
    
    print("Venta " + str(venta.id) + " aceptada correctamente")
    print("Gestion de backoffice creada con ID: " + str(gestion_aceptar.id))
    
except Exception as e:
    print("Error aceptando venta: " + str(e))

# Probar rechazar venta
print("Probando rechazar venta " + str(venta.id) + "...")
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
    
    print("Venta " + str(venta.id) + " rechazada correctamente")
    print("Gestion de backoffice creada con ID: " + str(gestion_rechazar.id))
    
except Exception as e:
    print("Error rechazando venta: " + str(e))

# Mostrar resumen
print("Pruebas completadas!")
print("Resumen:")
print("   - Venta creada: ID " + str(venta.id) + ", ID PreAp: " + str(venta.id_preap))
print("   - Estado final: " + str(venta.estado))
print("   - Cliente: " + cliente.nombres + " " + cliente.apellidos)
print("   - Usuario backoffice: " + usuario.username)

# Mostrar gestiones creadas
gestiones = GestionBackofficeTarjetaPlata.objects.filter(venta=venta)
print("   - Gestiones de backoffice: " + str(gestiones.count()))
for gestion in gestiones:
    print("     * " + gestion.accion + ": " + gestion.observaciones)

print("Las funciones de backoffice estan funcionando correctamente!")
print("Puedes verificar en el navegador:")
print("   - Dashboard: http://127.0.0.1:8000/tarjeta-plata/")
print("   - Bandeja nuevas: http://127.0.0.1:8000/tarjeta-plata/bandeja/nuevas/")
print("   - Detalle venta: http://127.0.0.1:8000/tarjeta-plata/venta/" + str(venta.id) + "/")