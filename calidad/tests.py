from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
import pytest
from calidad.models import MatrizCalidad, Auditoria, Speech, UsoProcesamientoAudio, validate_audio_file_extension
from core.models import Empleado


@pytest.mark.unit
class MatrizCalidadModelTest(TestCase):
    """Tests para el modelo MatrizCalidad"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='calidad_user',
            email='calidad@asecofin.com',
            password='testpass123'
        )
        
        # Crear grupo de Calidad
        self.grupo_calidad, created = Group.objects.get_or_create(name='Calidad')
        self.user.groups.add(self.grupo_calidad)
        
        self.matriz_data = {
            'tipologia': 'atencion_telefonica',
            'categoria': 'Saludo y Presentación',
            'indicador': 'El asesor se presenta correctamente',
            'ponderacion': Decimal('15.50'),
            'usuario_creacion': self.user
        }
    
    def test_creacion_matriz_calidad(self):
        """Test creación de matriz de calidad"""
        matriz = MatrizCalidad.objects.create(**self.matriz_data)
        self.assertEqual(matriz.tipologia, 'atencion_telefonica')
        self.assertEqual(matriz.categoria, 'Saludo y Presentación')
        self.assertEqual(matriz.ponderacion, Decimal('15.50'))
        self.assertTrue(matriz.activo)
    
    def test_str_representation(self):
        """Test representación string de la matriz"""
        matriz = MatrizCalidad.objects.create(**self.matriz_data)
        expected = "Saludo y Presentación - El asesor se presenta correctamente"
        self.assertEqual(str(matriz), expected)
    
    def test_ponderacion_validation(self):
        """Test validación de ponderación"""
        # Test ponderación válida
        matriz_data_valid = self.matriz_data.copy()
        matriz_data_valid['ponderacion'] = Decimal('50.00')
        matriz = MatrizCalidad.objects.create(**matriz_data_valid)
        self.assertEqual(matriz.ponderacion, Decimal('50.00'))
        
        # Test ponderación inválida (mayor a 100)
        matriz_data_invalid = self.matriz_data.copy()
        matriz_data_invalid['ponderacion'] = Decimal('150.00')
        with self.assertRaises(ValidationError):
            matriz = MatrizCalidad(**matriz_data_invalid)
            matriz.full_clean()


@pytest.mark.unit
class AuditoriaModelTest(TestCase):
    """Tests para el modelo Auditoria"""
    
    def setUp(self):
        self.user_calidad = User.objects.create_user(
            username='auditor',
            email='auditor@asecofin.com',
            password='testpass123'
        )
        
        self.user_asesor = User.objects.create_user(
            username='12345678',
            email='asesor@asecofin.com',
            password='testpass123'
        )
        
        # Crear grupos
        grupo_calidad, _ = Group.objects.get_or_create(name='Calidad')
        self.user_calidad.groups.add(grupo_calidad)
        
        self.auditoria_data = {
            'agente': self.user_asesor,
            'evaluador': self.user_calidad,
            'fecha_llamada': timezone.now().date(),
            'numero_telefono': '3001234567',
            'tipo_monitoreo': 'speech',
            'observaciones': 'Llamada de prueba para auditoría'
        }
    
    def test_creacion_auditoria(self):
        """Test creación de auditoría"""
        auditoria = Auditoria.objects.create(**self.auditoria_data)
        self.assertEqual(auditoria.agente, self.user_asesor)
        self.assertEqual(auditoria.evaluador, self.user_calidad)
        self.assertEqual(auditoria.numero_telefono, '3001234567')
        self.assertEqual(auditoria.tipo_monitoreo, 'speech')
    
    def test_get_absolute_url(self):
        """Test URL absoluta de la auditoría"""
        auditoria = Auditoria.objects.create(**self.auditoria_data)
        expected_url = f'/calidad/auditorias/{auditoria.id}/'
        self.assertEqual(auditoria.get_absolute_url(), expected_url)


@pytest.mark.unit
class SpeechModelTest(TestCase):
    """Tests para el modelo Speech"""
    
    def setUp(self):
        self.user_calidad = User.objects.create_user(
            username='auditor',
            email='auditor@asecofin.com',
            password='testpass123'
        )
        
        self.user_asesor = User.objects.create_user(
            username='12345678',
            email='asesor@asecofin.com',
            password='testpass123'
        )
        
        self.auditoria = Auditoria.objects.create(
            agente=self.user_asesor,
            evaluador=self.user_calidad,
            fecha_llamada=timezone.now().date(),
            numero_telefono='3001234567',
            tipo_monitoreo='speech'
        )
    
    def test_validate_audio_file_extension_valid(self):
        """Test validación de extensiones de audio válidas"""
        # Crear archivos de prueba con extensiones válidas
        valid_files = [
            SimpleUploadedFile("test.mp3", b"fake audio content", content_type="audio/mpeg"),
            SimpleUploadedFile("test.wav", b"fake audio content", content_type="audio/wav"),
            SimpleUploadedFile("test.ogg", b"fake audio content", content_type="audio/ogg"),
            SimpleUploadedFile("test.m4a", b"fake audio content", content_type="audio/mp4")
        ]
        
        for audio_file in valid_files:
            try:
                validate_audio_file_extension(audio_file)
            except ValidationError:
                self.fail(f"ValidationError raised for valid file: {audio_file.name}")
    
    def test_validate_audio_file_extension_invalid(self):
        """Test validación de extensiones de audio inválidas"""
        invalid_file = SimpleUploadedFile("test.txt", b"fake content", content_type="text/plain")
        
        with self.assertRaises(ValidationError):
            validate_audio_file_extension(invalid_file)
    
    @patch('calidad.utils.audio_utils.obtener_duracion_audio')
    @patch('calidad.utils.audio_utils.obtener_tamano_archivo_mb')
    def test_speech_creation_with_audio_processing(self, mock_tamano, mock_duracion):
        """Test creación de Speech con procesamiento de audio"""
        # Configurar mocks
        mock_duracion.return_value = 120.5  # 2 minutos y 30 segundos
        mock_tamano.return_value = 5.2  # 5.2 MB
        
        audio_file = SimpleUploadedFile(
            "test_audio.mp3", 
            b"fake audio content", 
            content_type="audio/mpeg"
        )
        
        speech = Speech.objects.create(
            auditoria=self.auditoria,
            audio=audio_file
        )
        
        self.assertEqual(speech.auditoria, self.auditoria)
        self.assertTrue(speech.audio.name.endswith('.mp3'))
    
    def test_crear_registro_uso(self):
        """Test creación de registro de uso"""
        audio_file = SimpleUploadedFile(
            "test_audio.mp3", 
            b"fake audio content", 
            content_type="audio/mpeg"
        )
        
        speech = Speech.objects.create(
            auditoria=self.auditoria,
            audio=audio_file,
            duracion_segundos=120.0,
            tamano_archivo_mb=5.0
        )
        
        # Crear registro de uso
        uso = speech.crear_registro_uso(self.user_calidad)
        
        self.assertEqual(uso.auditoria, self.auditoria)
        self.assertEqual(uso.speech, speech)
        self.assertEqual(uso.usuario, self.user_calidad)
        self.assertEqual(uso.duracion_audio_segundos, 120.0)
        self.assertEqual(uso.tamano_archivo_mb, 5.0)
    
    def test_actualizar_estadisticas_transcripcion(self):
        """Test actualización de estadísticas de transcripción"""
        audio_file = SimpleUploadedFile(
            "test_audio.mp3", 
            b"fake audio content", 
            content_type="audio/mpeg"
        )
        
        speech = Speech.objects.create(
            auditoria=self.auditoria,
            audio=audio_file
        )
        
        # Actualizar estadísticas
        speech.actualizar_estadisticas_transcripcion(
            tiempo_procesamiento=15.5,
            tokens_usados=1500
        )
        
        speech.refresh_from_db()
        self.assertEqual(speech.tiempo_procesamiento, 15.5)
        self.assertEqual(speech.tokens_procesados, 1500)


@pytest.mark.unit
class AnalizadorTranscripcionesTest(TestCase):
    """Tests para la clase AnalizadorTranscripciones"""
    
    def setUp(self):
        self.api_key = "test_api_key"
        self.analizador = AnalizadorTranscripciones(api_key=self.api_key)
    
    def test_inicializacion_con_api_key(self):
        """Test inicialización del analizador con API key"""
        self.assertEqual(self.analizador.api_key, self.api_key)
        self.assertEqual(self.analizador.model, "deepseek-chat")
    
    def test_inicializacion_sin_api_key(self):
        """Test inicialización sin API key debe fallar"""
        with self.assertRaises(ValueError):
            AnalizadorTranscripciones(api_key=None)
    
    @patch('calidad.utils.analisis_de_calidad.requests.post')
    def test_evaluar_calidad_llamada_exitoso(self, mock_post):
        """Test evaluación exitosa de calidad de llamada"""
        # Configurar respuesta mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'puntuacion_total': 85.5,
                        'evaluaciones': [
                            {
                                'categoria': 'Saludo',
                                'puntuacion': 90,
                                'observaciones': 'Excelente saludo'
                            }
                        ],
                        'observaciones_generales': 'Buena llamada en general'
                    })
                }
            }]
        }
        mock_post.return_value = mock_response
        
        transcripcion = "Hola, buenos días, mi nombre es Juan y lo voy a atender hoy."
        resultado = self.analizador.evaluar_calidad_llamada(transcripcion)
        
        self.assertIn('puntuacion_total', resultado)
        self.assertEqual(resultado['puntuacion_total'], 85.5)
        self.assertIn('evaluaciones', resultado)
    
    @patch('calidad.utils.analisis_de_calidad.requests.post')
    def test_evaluar_calidad_llamada_error_api(self, mock_post):
        """Test manejo de error en la API"""
        # Configurar respuesta de error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        transcripcion = "Hola, buenos días"
        resultado = self.analizador.evaluar_calidad_llamada(transcripcion)
        
        self.assertIn('error', resultado)
        self.assertIn('500', resultado['error'])


@pytest.mark.unit
class CalidadViewsTest(TestCase):
    """Tests para las vistas de calidad"""
    
    def setUp(self):
        self.client = Client()
        
        # Crear usuarios
        self.user_calidad = User.objects.create_user(
            username='calidad_user',
            email='calidad@asecofin.com',
            password='testpass123'
        )
        
        self.user_normal = User.objects.create_user(
            username='normal_user',
            email='normal@asecofin.com',
            password='testpass123'
        )
        
        # Crear grupos
        self.grupo_calidad, _ = Group.objects.get_or_create(name='Calidad')
        self.grupo_admin, _ = Group.objects.get_or_create(name='Administrador')
        
        # Asignar usuario a grupo de calidad
        self.user_calidad.groups.add(self.grupo_calidad)
    
    def test_acceso_sin_autenticacion(self):
        """Test acceso sin autenticación debe redirigir"""
        response = self.client.get(reverse('calidad:dashboard_calidad'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_acceso_usuario_sin_permisos(self):
        """Test acceso de usuario sin permisos de calidad"""
        self.client.force_login(self.user_normal)
        response = self.client.get(reverse('calidad:dashboard_calidad'))
        self.assertEqual(response.status_code, 403)
    
    def test_acceso_usuario_calidad(self):
        """Test acceso exitoso de usuario de calidad"""
        self.client.force_login(self.user_calidad)
        response = self.client.get(reverse('calidad:dashboard_calidad'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard de Calidad')
    
    def test_acceso_administrador(self):
        """Test acceso exitoso de administrador"""
        self.user_normal.groups.add(self.grupo_admin)
        self.client.force_login(self.user_normal)
        response = self.client.get(reverse('calidad:dashboard_calidad'))
        self.assertEqual(response.status_code, 200)


@pytest.mark.unit
class UsoProcesamientoAudioTest(TestCase):
    """Tests para el modelo UsoProcesamientoAudio"""
    
    def setUp(self):
        self.user_calidad = User.objects.create_user(
            username='auditor',
            email='auditor@asecofin.com',
            password='testpass123'
        )
        
        self.user_asesor = User.objects.create_user(
            username='12345678',
            email='asesor@asecofin.com',
            password='testpass123'
        )
        
        self.auditoria = Auditoria.objects.create(
            agente=self.user_asesor,
            evaluador=self.user_calidad,
            fecha_llamada=timezone.now().date(),
            numero_telefono='3001234567',
            tipo_monitoreo='speech'
        )
        
        audio_file = SimpleUploadedFile(
            "test_audio.mp3", 
            b"fake audio content", 
            content_type="audio/mpeg"
        )
        
        self.speech = Speech.objects.create(
            auditoria=self.auditoria,
            audio=audio_file,
            duracion_segundos=120.0,
            tamano_archivo_mb=5.0
        )
    
    def test_creacion_uso_procesamiento(self):
        """Test creación de registro de uso de procesamiento"""
        uso = UsoProcesamientoAudio.objects.create(
            auditoria=self.auditoria,
            speech=self.speech,
            usuario=self.user_calidad,
            duracion_audio_segundos=120.0,
            tamano_archivo_mb=5.0
        )
        
        self.assertEqual(uso.auditoria, self.auditoria)
        self.assertEqual(uso.speech, self.speech)
        self.assertEqual(uso.usuario, self.user_calidad)
        self.assertEqual(uso.duracion_audio_segundos, 120.0)
    
    def test_calcular_costo_transcripcion(self):
        """Test cálculo de costo de transcripción"""
        uso = UsoProcesamientoAudio.objects.create(
            auditoria=self.auditoria,
            speech=self.speech,
            usuario=self.user_calidad,
            duracion_audio_segundos=120.0,
            tamano_archivo_mb=5.0
        )
        
        # Llamar método de cálculo
        uso.calcular_costo_transcripcion()
        
        # Verificar que se calculó el costo correcto (120 segundos * 0.0014 = 0.168)
        from decimal import Decimal
        costo_esperado = Decimal('120.0') * Decimal('0.0014')
        self.assertEqual(uso.costo_transcripcion, costo_esperado)
    
    def test_costo_total(self):
        """Test cálculo de costo total"""
        uso = UsoProcesamientoAudio.objects.create(
            auditoria=self.auditoria,
            speech=self.speech,
            usuario=self.user_calidad,
            duracion_audio_segundos=120.0,
            tamano_archivo_mb=5.0,
            costo_transcripcion=Decimal('2.50'),
            costo_analisis=Decimal('1.75')
        )
        
        costo_total = uso.costo_total()
        self.assertEqual(costo_total, Decimal('4.25'))
