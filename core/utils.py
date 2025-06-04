from django.core.mail import EmailMessage
from django.conf import settings
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def enviar_correo(asunto, mensaje, destinatarios, archivos_adjuntos=None, html_content=None):
    """
    Función para enviar correos electrónicos utilizando la configuración SMTP definida en settings.
    
    Args:
        asunto (str): Asunto del correo electrónico
        mensaje (str): Contenido del mensaje en texto plano
        destinatarios (list): Lista de direcciones de correo electrónico de los destinatarios
        archivos_adjuntos (list, optional): Lista de rutas a archivos para adjuntar
        html_content (str, optional): Contenido HTML del mensaje
    
    Returns:
        bool: True si el correo se envió correctamente, False en caso contrario
    """
    try:
        # Crear el email
        email = EmailMessage(
            subject=asunto,
            body=mensaje,
            from_email=settings.EMAIL_HOST_USER,
            to=destinatarios,
        )
        
        # Si hay contenido HTML, establecerlo
        if html_content:
            email.content_subtype = "html"
            email.body = html_content
        
        # Adjuntar archivos si existen
        if archivos_adjuntos:
            for archivo in archivos_adjuntos:
                if os.path.exists(archivo):
                    email.attach_file(archivo)
                else:
                    logger.warning(f"No se pudo adjuntar el archivo {archivo} porque no existe")
        
        # Enviar el email
        email.send(fail_silently=False)
        logger.info(f"Correo enviado correctamente a {', '.join(destinatarios)}")
        return True
    
    except Exception as e:
        logger.error(f"Error al enviar correo electrónico: {str(e)}")
        return False


def determinar_estado_cliente(cliente, gestiones=None, today=None):
    """
    Determina el estado de negociación de un cliente basado en sus gestiones y acuerdos.
    
    Args:
        cliente: Instancia del modelo Cliente
        gestiones: QuerySet de gestiones del cliente. Si es None, se considera que no hay gestiones
        today: Fecha actual. Si es None, se utiliza la fecha del sistema
        
    Returns:
        dict: Diccionario con información del estado del cliente:
            - nombre: Nombre del estado (string)
            - color: Color Bootstrap para el badge (string)
            - icono: Clase de Bootstrap Icons (string)
            - descripcion: Descripción detallada del estado (string)
    """
    # Si no se proporciona una fecha, se utiliza la fecha actual del sistema
    if today is None:
        today = datetime.now().date()
    
    # Valores por defecto
    estado = {
        'nombre': 'N/A',
        'color': 'secondary',
        'icono': 'bi-question-circle',
        'descripcion': 'Estado no definido'
    }
    
    # Si no hay gestiones, se verifica solo el estado base del cliente
    if not gestiones or gestiones.count() == 0:
        if cliente.estado == 'Activo':
            estado = {
                'nombre': 'Sin Gestión',
                'color': 'primary',
                'icono': 'bi-person-check',
                'descripcion': 'Cliente activo, sin gestión'
            }
        else:
            estado = {
                'nombre': cliente.estado,
                'color': 'success' if cliente.estado == 'Activo' else ('danger' if cliente.estado == 'Inactivo' else 'secondary'),
                'icono': 'bi-person',
                'descripcion': f'Cliente en estado {cliente.estado}'
            }
        return estado
    
    # Si hay gestiones, se obtiene la más reciente
    ultima_gestion = gestiones.order_by('-fecha_hora_gestion', '-id').first()
    
    # Si la última gestión tiene un acuerdo de pago
    if ultima_gestion and ultima_gestion.acuerdo_pago_realizado:
        if ultima_gestion.fecha_acuerdo and ultima_gestion.fecha_acuerdo < today:
            estado = {
                'nombre': 'Acuerdo Vencido',
                'color': 'warning',
                'icono': 'bi-exclamation-triangle',
                'descripcion': 'Acuerdo de pago vencido'
            }
        else:
            estado = {
                'nombre': 'Con Acuerdo',
                'color': 'success',
                'icono': 'bi-check-circle',
                'descripcion': 'Acuerdo de pago vigente'
            }
    # Si hay gestiones pero sin acuerdo
    else:
        estado = {
            'nombre': 'En Negociación',
            'color': 'info',
            'icono': 'bi-arrow-repeat',
            'descripcion': 'En proceso de negociación'
        }
    
    return estado

def enviar_correo_prueba(destinatario, nombre_cliente=None):
    """
    Envía un correo electrónico de prueba al destinatario especificado.
    
    Args:
        destinatario (str): Dirección de correo electrónico del destinatario
        nombre_cliente (str, optional): Nombre del cliente para personalizar el mensaje
    
    Returns:
        bool: True si el correo se envió correctamente, False en caso contrario
    """
    asunto = "Correo de prueba desde CREA ONLINE CRM"
    
    # Personalizar el mensaje si se proporciona el nombre del cliente
    if nombre_cliente:
        mensaje = f"""
        Hola {nombre_cliente},
        
        Este es un correo de prueba enviado desde el sistema CREA ONLINE CRM.
        
        Saludos,
        El equipo de CREA ONLINE
        """
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #BB2BA3; color: white; padding: 10px 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f5f5f5; padding: 10px 20px; text-align: center; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>CREA ONLINE CRM</h2>
                </div>
                <div class="content">
                    <p>Hola <strong>{nombre_cliente}</strong>,</p>
                    <p>Este es un correo de prueba enviado desde el sistema CREA ONLINE CRM.</p>
                    <p>Gracias por utilizar nuestros servicios.</p>
                </div>
                <div class="footer">
                    <p>Este es un correo automático, por favor no responda a este mensaje.</p>
                    <p>&copy; {2025} CREA ONLINE. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        mensaje = """
        Hola,
        
        Este es un correo de prueba enviado desde el sistema CREA ONLINE CRM.
        
        Saludos,
        El equipo de CREA ONLINE
        """
        
        html_content = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #BB2BA3; color: white; padding: 10px 20px; text-align: center; }
                .content { padding: 20px; }
                .footer { background-color: #f5f5f5; padding: 10px 20px; text-align: center; font-size: 12px; color: #777; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>CREA ONLINE CRM</h2>
                </div>
                <div class="content">
                    <p>Hola,</p>
                    <p>Este es un correo de prueba enviado desde el sistema CREA ONLINE CRM.</p>
                    <p>Gracias por utilizar nuestros servicios.</p>
                </div>
                <div class="footer">
                    <p>Este es un correo automático, por favor no responda a este mensaje.</p>
                    <p>&copy; 2025 CREA ONLINE. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    return enviar_correo(asunto, mensaje, [destinatario], html_content=html_content)
