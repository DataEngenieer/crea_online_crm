from django.core.mail import EmailMessage
from django.conf import settings
import os
import logging

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
        logger.error(f"Error al enviar correo: {str(e)}")
        return False

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
