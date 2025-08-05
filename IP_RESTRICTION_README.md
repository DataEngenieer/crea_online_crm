# Sistema de Restricción de IPs - CREA Online CRM

Este documento describe el sistema avanzado de restricción de acceso por IP implementado en el CRM, que utiliza la API de ipquery.io para obtener información detallada de las direcciones IP y proporciona análisis de riesgo en tiempo real.

## Características Principales

### 🔒 Restricción de Acceso
- **Middleware Global**: Controla el acceso al CRM en producción basado en IPs permitidas
- **Excepciones Inteligentes**: Superusuarios y administradores tienen acceso sin restricciones
- **URLs Exentas**: Admin de Django, archivos estáticos, media y APIs están exentos
- **Detección de Proxies**: Manejo inteligente de headers de proxy y CDN
- **Activación Condicional**: Solo se activa en producción (DEBUG=False)

### 📊 Monitoreo y Registro Avanzado
- **Registro Completo**: Todos los accesos se registran con información detallada de IP
- **Integración con ipquery.io**: Obtiene país, ciudad, ISP, y análisis de riesgo completo
- **Tipos de Registro**: Login exitoso, login fallido, IP bloqueada, acceso permitido, acceso denegado
- **Análisis de Riesgo**: Detección de VPN, proxies, y conexiones sospechosas
- **Métricas de Seguridad**: Puntuación de riesgo de 0-100 para cada acceso
- **Geolocalización**: Información precisa de ubicación geográfica

### 🛠️ Gestión Completa de IPs
- **Panel Web Avanzado**: Interfaz moderna para gestionar IPs permitidas con filtros y búsqueda
- **Comandos CLI Completos**: Herramientas de línea de comandos para administración completa
- **API REST**: Endpoints para consultar información de IPs y estadísticas
- **Gestión Masiva**: Importación y exportación de listas de IPs
- **Activación/Desactivación**: Control granular del estado de cada IP
- **Auditoría Completa**: Registro de todos los cambios en la configuración

## Modelos de Base de Datos

### IPPermitida
- `ip_address`: Dirección IP permitida
- `descripcion`: Descripción de la IP (ej: "Oficina principal")
- `activa`: Estado de la IP (activa/inactiva)
- `usuario_creacion`: Usuario que creó el registro
- `ultimo_acceso`: Fecha del último acceso desde esta IP

### RegistroAccesoIP
- `ip_address`: Dirección IP del acceso
- `usuario`: Usuario que intentó acceder (si aplica)
- `tipo_acceso`: Tipo de acceso (login_exitoso, login_fallido, etc.)
- `pais`, `ciudad`, `isp`: Información geográfica y de proveedor
- `es_vpn`, `es_proxy`: Indicadores de riesgo
- `puntuacion_riesgo`: Puntuación de riesgo (0-100)

## Configuración

### 1. Variable de Control
El sistema incluye una variable de configuración para activar/desactivar la restricción de IPs:

```python
# En settings.py
IP_RESTRICTION_ENABLED = os.getenv('IP_RESTRICTION_ENABLED', 'False') == 'True'
```

**En archivo .env:**
```bash
# Para activar el sistema de restricción de IPs
IP_RESTRICTION_ENABLED=True

# Para desactivar el sistema de restricción de IPs (por defecto)
IP_RESTRICTION_ENABLED=False
```

### 2. Middleware
El middleware `IPRestrictionMiddleware` está configurado en `settings.py`:

```python
MIDDLEWARE = [
    # ... otros middlewares
    'core.ip_middleware.IPRestrictionMiddleware',
    # ... más middlewares
]
```

**Nota:** El middleware solo se ejecuta cuando `IP_RESTRICTION_ENABLED=True` y `DEBUG=False`

### 3. Dependencias
Asegúrese de que las dependencias estén instaladas:

```bash
pip install requests>=2.25.0
pip install django>=5.2.1
pip install psycopg2-binary  # Para PostgreSQL en producción
```

### 4. Migraciones
Ejecute las migraciones para crear las tablas:

```bash
python manage.py migrate
```

## Uso del Sistema

### Gestión Web

#### Acceder al Panel de Gestión
1. Vaya a `/admin/ips-permitidas/` (requiere permisos de administrador)
2. Desde aquí puede:
   - Ver todas las IPs permitidas
   - Agregar nuevas IPs
   - Activar/desactivar IPs
   - Consultar información detallada de IPs

#### Ver Registros de Acceso
1. Vaya a `/admin/registros-acceso-ip/`
2. Filtre por tipo de acceso, fecha, IP, etc.
3. Vea estadísticas de acceso y análisis de riesgo

### Gestión por Línea de Comandos

#### Listar IPs Permitidas
```bash
# Listar todas las IPs
python manage.py manage_ips list

# Listar solo IPs activas
python manage.py manage_ips list --active-only
```

#### Agregar IP Permitida
```bash
# Agregar IP con descripción
python manage.py manage_ips add 192.168.1.100 "Oficina principal"

# Agregar IP especificando usuario creador
python manage.py manage_ips add 192.168.1.101 "Casa del gerente" --user admin
```

#### Activar/Desactivar IP
```bash
# Cambiar estado de una IP
python manage.py manage_ips toggle 192.168.1.100
```

#### Eliminar IP
```bash
# Eliminar IP del sistema
python manage.py manage_ips remove 192.168.1.100
```

#### Consultar Información de IP
```bash
# Obtener información detallada usando ipquery.io
python manage.py manage_ips info 186.86.110.237
```

#### Ver Estadísticas
```bash
# Estadísticas de los últimos 7 días
python manage.py manage_ips stats

# Estadísticas de los últimos 30 días
python manage.py manage_ips stats --days 30
```

#### Limpiar Registros Antiguos
```bash
# Eliminar registros más antiguos que 90 días
python manage.py manage_ips cleanup

# Eliminar registros más antiguos que 30 días sin confirmación
python manage.py manage_ips cleanup --days 30 --confirm
```

## API Endpoints

### Consultar Información de IP
```
GET /api/consultar-ip-info/?ip=186.86.110.237
```

Respuesta:
```json
{
  "success": true,
  "data": {
    "ip": "186.86.110.237",
    "pais": "Colombia",
    "ciudad": "Bogotá",
    "isp": "Telmex Colombia S.A.",
    "es_vpn": false,
    "es_proxy": false,
    "puntuacion_riesgo": 0
  }
}
```

### Obtener IP Actual
```
GET /api/obtener-mi-ip/
```

Respuesta:
```json
{
  "success": true,
  "ip": "186.86.110.237"
}
```

## Funcionamiento en Producción

### Activación Automática
- El middleware **solo se activa en producción** (`DEBUG = False`)
- En desarrollo, el sistema no restringe el acceso pero registra información
- Integración completa con MinIO para almacenamiento de logs
- Compatible con Railway y otros servicios de hosting

### Flujo de Verificación Avanzado
1. Usuario intenta acceder al CRM
2. Middleware obtiene la IP real (considerando proxies/CDN/Railway)
3. Verifica si el usuario es superusuario/administrador
4. Consulta caché de IPs para optimizar rendimiento
5. Si no es admin, consulta si la IP está en la lista de permitidas
6. Si la IP no está permitida:
   - Consulta información detallada con ipquery.io
   - Analiza riesgo de seguridad (VPN, proxy, etc.)
   - Registra el intento de acceso bloqueado con métricas completas
   - Redirige al login con mensaje de error personalizado
7. Si la IP está permitida:
   - Registra el acceso exitoso con geolocalización
   - Actualiza la fecha de último acceso
   - Permite continuar con el flujo normal

### Manejo Robusto de Errores
- Si ipquery.io no responde, el sistema continúa funcionando normalmente
- Los errores se registran en los logs de Django con detalles completos
- El acceso no se bloquea por errores de la API externa
- Sistema de reintentos automáticos para consultas fallidas
- Fallback a información básica de IP cuando la API no está disponible
- Notificaciones automáticas a administradores en caso de errores críticos

## Seguridad

### Consideraciones Importantes
1. **Proxies y CDN**: El sistema detecta la IP real considerando headers como `X-Forwarded-For` y `CF-Connecting-IP`
2. **Análisis de Riesgo**: Identifica VPNs, proxies y conexiones sospechosas
3. **Registro Completo**: Todos los intentos de acceso quedan registrados
4. **Acceso de Emergencia**: Superusuarios siempre tienen acceso

### Recomendaciones de Seguridad
1. **Monitoreo Continuo**: Revise regularmente los registros de acceso y estadísticas
2. **Gestión Proactiva**: Mantenga actualizada la lista de IPs permitidas
3. **Respaldos Regulares**: Mantenga respaldos de la configuración de IPs
4. **Análisis de Riesgo**: Preste atención a puntuaciones de riesgo altas (>50)
5. **Alertas Automáticas**: Configure notificaciones para accesos sospechosos
6. **Auditoría Periódica**: Revise y limpie IPs inactivas mensualmente
7. **Integración con MinIO**: Use almacenamiento seguro para logs críticos
8. **Documentación**: Mantenga documentadas las razones de cada IP permitida

## Troubleshooting

### Problemas Comunes

#### "Mi IP está bloqueada"
1. Verifique su IP actual: `python manage.py manage_ips info <su_ip>`
2. Agregue su IP: `python manage.py manage_ips add <su_ip> "Descripción"`
3. O desactive temporalmente: Acceda como superusuario

#### "Error al consultar ipquery.io"
1. Verifique la conexión a internet
2. Confirme que la API esté disponible
3. Los errores no bloquean el funcionamiento del sistema

#### "No puedo acceder al panel de gestión"
1. Confirme que tiene permisos de administrador
2. Verifique que esté autenticado
3. Acceda directamente a `/admin/` de Django

### Logs y Debugging
- Los errores se registran en los logs de Django
- Use `DEBUG = True` en desarrollo para ver detalles
- Revise los registros de acceso en la base de datos

## Mantenimiento y Optimización

### Tareas Regulares
1. **Limpieza Automática**: Ejecute cleanup mensualmente para optimizar rendimiento
2. **Auditoría de IPs**: Verifique y remueva IPs inactivas o no utilizadas
3. **Análisis de Patrones**: Revise estadísticas para detectar patrones sospechosos
4. **Actualización de Configuración**: Mantenga actualizada la configuración según necesidades
5. **Verificación de Conectividad**: Pruebe regularmente la conectividad con ipquery.io
6. **Respaldo de Datos**: Exporte configuraciones importantes regularmente
7. **Monitoreo de Rendimiento**: Verifique que el middleware no afecte el rendimiento

## Publicación sin Restricciones

### Para Publicar sin Activar las Restricciones de IP

Si desea publicar el CRM en producción pero **no activar** las restricciones de IP todavía, simplemente:

1. **No configure la variable** `IP_RESTRICTION_ENABLED` en su archivo `.env` (o déjela en `False`)
2. **O configure explícitamente**:
   ```bash
   IP_RESTRICTION_ENABLED=False
   ```

### Comportamiento con IP_RESTRICTION_ENABLED=False
- ✅ **El middleware está presente** pero no aplica restricciones
- ✅ **Todas las funcionalidades del CRM funcionan normalmente**
- ✅ **Los registros de acceso siguen funcionando** (para monitoreo)
- ✅ **El panel de gestión de IPs está disponible** para configuración futura
- ✅ **Los comandos de gestión funcionan** para preparar la configuración

### Para Activar las Restricciones Más Tarde
Cuando esté listo para activar las restricciones:

1. **Configure las IPs permitidas**:
   ```bash
   python manage.py manage_ips add <ip_oficina> "Oficina principal"
   python manage.py manage_ips add <ip_casa> "Casa del administrador"
   ```

2. **Active el sistema**:
   ```bash
   # En su archivo .env
   IP_RESTRICTION_ENABLED=True
   ```

3. **Reinicie la aplicación** para que tome la nueva configuración

### Ventajas de este Enfoque
- **Implementación gradual**: Puede configurar todo sin afectar el acceso actual
- **Pruebas seguras**: Puede probar la funcionalidad sin riesgo de bloqueos
- **Configuración previa**: Puede preparar las IPs permitidas antes de activar
- **Rollback fácil**: Puede desactivar rápidamente si hay problemas
- **Actualizar Descripciones**: Mantenga descripciones claras y actualizadas

### Comandos de Mantenimiento
```bash
# Limpieza mensual de registros
python manage.py manage_ips cleanup --days 90 --confirm

# Revisión de estadísticas
python manage.py manage_ips stats --days 30

# Verificación de IPs activas
python manage.py manage_ips list --active-only
```

## Integración con Otros Módulos

### Compatibilidad
- **Módulo Calidad**: Protege acceso a auditorías y análisis de IA
- **Módulo Tarjeta Plata**: Asegura gestión de clientes y documentos
- **Módulo Telefónica**: Protege datos de clientes y gestiones
- **Sistema de Tickets**: Controla acceso a soporte interno
- **Chat Interno**: Protege comunicaciones entre usuarios
- **MinIO**: Integración para almacenamiento seguro de logs

### APIs Protegidas
- Todas las APIs REST respetan las restricciones de IP
- Endpoints de consulta de información de IP
- APIs de exportación de datos
- Servicios de integración con IA

---

**Desarrollado para CREA Online CRM**  
**Versión**: 2.0.0  
**Fecha**: Enero 2025  
**Soporte**: jhonmoreno151@gmail.com | +573108647211