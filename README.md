# ASECOFIN

Sistema de gestión documental para la administración de comprobantes de pago y usuarios.

## 🚀 Características principales

- **Gestión de Usuarios**
  - Registro y autenticación de usuarios
  - Roles: Administrador y Empleado
  - Perfiles de usuario personalizables

- **Gestión de Comprobantes**
  - Carga y descarga de comprobantes
  - Visualización de historial de actividades
  - Separación automática de PDFs

- **Dashboard Interactivo**
  - Estadísticas de usuarios y actividad
  - Gráficos de tendencias
  - Resumen de acciones recientes

- **Seguridad**
  - Autenticación por correo electrónico
  - Control de acceso basado en roles
  - Registro de actividades

## 🛠️ Instalación

1. **Clonar el repositorio**
   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd asecofin_crm
   ```

2. **Configurar entorno virtual**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar base de datos**
   - Configura la base de datos en `asecofin_crm/settings.py`
   - SQLite viene configurado por defecto para desarrollo

5. **Aplicar migraciones**
   ```bash
   python manage.py migrate
   ```

6. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   ```

7. **Iniciar servidor**
   ```bash
   python manage.py runserver
   ```
   
   El sistema estará disponible en: http://127.0.0.1:8000/

## 🎨 Interfaz de Usuario

- Diseño responsivo con Bootstrap 5
- Paleta de colores corporativa (#006def)
- Navegación intuitiva con barra lateral
- Componentes modernos y accesibles

## 📊 Módulos Principales

### Para Administradores
- Gestión completa de usuarios
- Dashboard con estadísticas
- Herramientas de administración
- Separación de PDFs

### Para Empleados
- Visualización de comprobantes
- Historial de descargas
- Perfil de usuario

## 📋 Requisitos del Sistema

- Python 3.8+
- Django 4.2+
- Base de datos (SQLite, PostgreSQL o MySQL)
- Navegador web moderno

## 📂 Manejo de archivos media en producción (Railway)

- **Ruta persistente:** En Railway, los archivos subidos (por ejemplo, PDFs separados y originales) se almacenan en la ruta `/app/media`, que es persistente entre despliegues.
- **Configuración en Django:**
  ```python
  MEDIA_URL = '/media/'
  MEDIA_ROOT = '/app/media'
  ```
- **Creación automática:** El sistema crea la carpeta `/app/media` al iniciar si no existe.
- **Carga y acceso:** Todos los archivos subidos por los usuarios se guardan en subcarpetas dentro de `/app/media`.
- **Servir archivos media en producción:**
  - Railway **NO** sirve archivos media automáticamente. Se recomienda usar un almacenamiento externo (como S3) para proyectos de alta concurrencia.
  - Para proyectos pequeños, puedes servir archivos media desde Django agregando en `urls.py` (solo para desarrollo o pruebas):
    ```python
    from django.conf import settings
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    ```
  - **¡No usar en producción real!** Para producción, usa un servidor web (Nginx, etc.) o almacenamiento externo.
- **Importante:**
  - Asegúrate de que tus rutas de guardado y lectura de archivos usen siempre `settings.MEDIA_ROOT`.
  - Si necesitas acceso persistente a los archivos tras reinicios/despliegues, usa siempre la ruta `/app/media`.

## 📝 Licencia

Este proyecto es de uso interno de ASECOFIN. Todos los derechos reservados.

---

💡 **Nota:** Para soporte técnico, contactar al equipo de desarrollo jhonmoreno151@gmail.com whatsapp +573108647211.
