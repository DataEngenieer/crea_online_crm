from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from .models import UsuariosPlataformas, Campana


class RegistroUsuarioTests(TestCase):
    """Pruebas para el proceso de registro de usuario"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear grupo de asesores
        self.grupo_asesor = Group.objects.create(name='asesor')
        
        # Crear campañas para cada módulo
        self.campana_core = Campana.objects.create(
            nombre='Cartera y Soluciones',
            codigo='carysol',
            modulo='core',
            activa=True
        )
        
        self.campana_telefonica = Campana.objects.create(
            nombre='Telefonica',
            codigo='teleco',
            modulo='telefonica',
            activa=True
        )
        
        # Cliente para hacer peticiones HTTP
        self.client = Client()
        
        # URL de registro
        self.registro_url = reverse('core:registro')
        
        # Datos de usuario para las pruebas
        self.datos_usuario = {
            'first_name': 'Usuario',
            'last_name': 'Prueba',
            'email': 'usuario.prueba@example.com',
            'username': '12345678',
            'usuario_greta': 'usuario_greta_test',
            'password1': 'contraseña_segura_123',
            'password2': 'contraseña_segura_123',
        }
    
    def test_registro_usuario_modulo_core(self):
        """Prueba el registro de un usuario seleccionando el módulo core"""
        # Añadir el módulo seleccionado a los datos
        datos = self.datos_usuario.copy()
        datos['selected_module'] = 'core'
        
        # Hacer la petición POST al registro
        response = self.client.post(self.registro_url, datos)
        
        # Verificar redirección a login después del registro exitoso
        self.assertRedirects(response, reverse('core:login'))
        
        # Verificar que el usuario se creó correctamente
        self.assertTrue(User.objects.filter(username=datos['username']).exists())
        
        # Obtener el usuario creado
        usuario = User.objects.get(username=datos['username'])
        
        # Verificar que se creó el registro en UsuariosPlataformas
        self.assertTrue(UsuariosPlataformas.objects.filter(usuario=usuario).exists())
        
        # Verificar que el usuario_greta se guardó correctamente
        usuario_plataformas = UsuariosPlataformas.objects.get(usuario=usuario)
        self.assertEqual(usuario_plataformas.usuario_greta, datos['usuario_greta'])
        
        # Verificar que el usuario se asignó al grupo 'asesor'
        self.assertTrue(usuario.groups.filter(name='asesor').exists())
        
        # Verificar que el usuario se asignó a la campaña de core
        self.assertTrue(usuario.campanas.filter(codigo='carysol').exists())
        self.assertEqual(usuario.campanas.count(), 1)
    
    def test_registro_usuario_modulo_telefonica(self):
        """Prueba el registro de un usuario seleccionando el módulo telefonica"""
        # Añadir el módulo seleccionado a los datos
        datos = self.datos_usuario.copy()
        datos['username'] = '87654321'  # Cambiar username para que no haya conflicto
        datos['email'] = 'otro.usuario@example.com'  # Cambiar email para que no haya conflicto
        datos['selected_module'] = 'telefonica'
        
        # Hacer la petición POST al registro
        response = self.client.post(self.registro_url, datos)
        
        # Verificar redirección a login después del registro exitoso
        self.assertRedirects(response, reverse('core:login'))
        
        # Verificar que el usuario se creó correctamente
        self.assertTrue(User.objects.filter(username=datos['username']).exists())
        
        # Obtener el usuario creado
        usuario = User.objects.get(username=datos['username'])
        
        # Verificar que se creó el registro en UsuariosPlataformas
        self.assertTrue(UsuariosPlataformas.objects.filter(usuario=usuario).exists())
        
        # Verificar que el usuario_greta se guardó correctamente
        usuario_plataformas = UsuariosPlataformas.objects.get(usuario=usuario)
        self.assertEqual(usuario_plataformas.usuario_greta, datos['usuario_greta'])
        
        # Verificar que el usuario se asignó al grupo 'asesor'
        self.assertTrue(usuario.groups.filter(name='asesor').exists())
        
        # Verificar que el usuario se asignó a la campaña de telefonica
        self.assertTrue(usuario.campanas.filter(codigo='teleco').exists())
        self.assertEqual(usuario.campanas.count(), 1)
    
    def test_registro_usuario_sin_modulo(self):
        """Prueba el registro de un usuario sin especificar módulo (debería usar 'core' por defecto)"""
        # Usar datos sin especificar módulo
        datos = self.datos_usuario.copy()
        datos['username'] = '11223344'  # Cambiar username para que no haya conflicto
        datos['email'] = 'tercer.usuario@example.com'  # Cambiar email para que no haya conflicto
        # No incluimos selected_module
        
        # Hacer la petición POST al registro
        response = self.client.post(self.registro_url, datos)
        
        # Verificar redirección a login después del registro exitoso
        self.assertRedirects(response, reverse('core:login'))
        
        # Verificar que el usuario se creó correctamente
        self.assertTrue(User.objects.filter(username=datos['username']).exists())
        
        # Obtener el usuario creado
        usuario = User.objects.get(username=datos['username'])
        
        # Verificar que el usuario se asignó a la campaña de core (por defecto)
        self.assertTrue(usuario.campanas.filter(codigo='carysol').exists())
        self.assertEqual(usuario.campanas.count(), 1)
    
    def test_registro_usuario_sin_usuario_greta(self):
        """Prueba el registro de un usuario sin especificar usuario_greta"""
        # Usar datos sin usuario_greta
        datos = self.datos_usuario.copy()
        datos['username'] = '99887766'  # Cambiar username para que no haya conflicto
        datos['email'] = 'cuarto.usuario@example.com'  # Cambiar email para que no haya conflicto
        datos['usuario_greta'] = ''  # Usuario greta vacío
        datos['selected_module'] = 'core'
        
        # Hacer la petición POST al registro
        response = self.client.post(self.registro_url, datos)
        
        # Verificar redirección a login después del registro exitoso
        self.assertRedirects(response, reverse('core:login'))
        
        # Verificar que el usuario se creó correctamente
        self.assertTrue(User.objects.filter(username=datos['username']).exists())
        
        # Obtener el usuario creado
        usuario = User.objects.get(username=datos['username'])
        
        # Verificar que se creó el registro en UsuariosPlataformas
        self.assertTrue(UsuariosPlataformas.objects.filter(usuario=usuario).exists())
        
        # Verificar que el usuario_greta está vacío
        usuario_plataformas = UsuariosPlataformas.objects.get(usuario=usuario)
        self.assertEqual(usuario_plataformas.usuario_greta, '')
        
        # Verificar que el usuario se asignó a la campaña de core
        self.assertTrue(usuario.campanas.filter(codigo='carysol').exists())
