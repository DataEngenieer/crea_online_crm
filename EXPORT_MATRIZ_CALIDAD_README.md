# Exportación de Datos - MatrizCalidad

Este documento describe cómo usar los scripts para exportar todos los datos del modelo `MatrizCalidad` a formato JSON.

## 📁 Archivos Disponibles

### 1. Management Command de Django
**Archivo:** `calidad/management/commands/export_matriz_calidad.py`

### 2. Script Independiente
**Archivo:** `export_matriz_calidad_script.py`

---

## 🚀 Métodos de Ejecución

### Método 1: Management Command (Recomendado)

```bash
# Exportación básica
python manage.py export_matriz_calidad

# Especificar archivo de salida
python manage.py export_matriz_calidad --output mi_export.json

# Usar formato nativo de Django
python manage.py export_matriz_calidad --format django

# Usar formato personalizado (por defecto)
python manage.py export_matriz_calidad --format custom
```

### Método 2: Script Independiente

```bash
# Exportación básica
python export_matriz_calidad_script.py

# Especificar archivo de salida
python export_matriz_calidad_script.py mi_archivo_personalizado.json
```

---

## 📊 Estructura del JSON Exportado

### Formato Personalizado (Recomendado)

```json
{
  "metadata": {
    "export_date": "2025-01-XX...",
    "total_records": 50,
    "model": "calidad.MatrizCalidad",
    "version": "1.0"
  },
  "data": [
    {
      "id": 1,
      "tipologia": "ECUF",
      "categoria": "Saludo y Presentación",
      "indicador": "El agente se presenta correctamente",
      "ponderacion": 15.50,
      "activo": true,
      "usuario_creacion": {
        "id": 1,
        "username": "admin",
        "first_name": "Administrador",
        "last_name": "Sistema",
        "email": "admin@empresa.com"
      },
      "fecha_creacion": "2025-01-XX...",
      "fecha_actualizacion": "2025-01-XX..."
    }
  ]
}
```

### Formato Django Nativo

Utiliza el serializer nativo de Django con toda la información del modelo.

---

## 📈 Información Incluida

### Campos del Modelo MatrizCalidad
- **id**: Identificador único
- **tipologia**: Tipo de interacción (ECUF, ECN, Estadistico)
- **categoria**: Categoría del indicador
- **indicador**: Descripción del indicador de calidad
- **ponderacion**: Peso del indicador (0.01 - 100)
- **activo**: Estado del registro (true/false)
- **fecha_creacion**: Fecha de creación del registro
- **fecha_actualizacion**: Última actualización

### Información del Usuario Creador
- **id**: ID del usuario
- **username**: Nombre de usuario
- **first_name**: Nombre
- **last_name**: Apellido
- **email**: Correo electrónico

---

## 📊 Estadísticas Incluidas

Ambos scripts proporcionan estadísticas detalladas:

- **Total de registros exportados**
- **Distribución por tipología**
- **Registros activos vs inactivos**
- **Número de categorías únicas**
- **Tamaño del archivo generado**
- **Fecha y hora de exportación**

---

## 🔧 Opciones Avanzadas

### Management Command

| Parámetro | Descripción | Valores | Por Defecto |
|-----------|-------------|---------|-------------|
| `--output` | Nombre del archivo de salida | Cualquier nombre | `matriz_calidad_export.json` |
| `--format` | Formato de exportación | `django`, `custom` | `custom` |

### Ejemplos de Uso Avanzado

```bash
# Exportar con nombre específico y formato Django
python manage.py export_matriz_calidad --output backup_matrices_2025.json --format django

# Exportar solo con formato personalizado
python manage.py export_matriz_calidad --output matrices_custom.json --format custom
```

---

## 🛠️ Requisitos

- **Django**: Configurado y funcionando
- **Modelo MatrizCalidad**: Debe existir en la base de datos
- **Permisos**: Acceso de lectura a la base de datos
- **Python**: 3.8 o superior

---

## 🚨 Consideraciones Importantes

1. **Tamaño del archivo**: Para grandes volúmenes de datos, el archivo JSON puede ser considerable
2. **Memoria**: El script carga todos los registros en memoria
3. **Codificación**: Los archivos se guardan en UTF-8 para soportar caracteres especiales
4. **Relaciones**: Se incluye información completa del usuario creador
5. **Fechas**: Se exportan en formato ISO 8601

---

## 🔍 Solución de Problemas

### Error: "No module named 'calidad'"
- Asegúrate de ejecutar el script desde el directorio raíz del proyecto Django
- Verifica que `DJANGO_SETTINGS_MODULE` esté configurado correctamente

### Error: "No se encontraron registros"
- Verifica que existan registros en el modelo MatrizCalidad
- Comprueba la conexión a la base de datos

### Error de permisos
- Asegúrate de tener permisos de escritura en el directorio de salida
- Verifica permisos de lectura en la base de datos

---

## 📝 Ejemplo de Salida del Script

```
🚀 Script de Exportación de MatrizCalidad
==================================================
📄 Archivo de salida: matriz_calidad_export.json
Iniciando exportación de MatrizCalidad...
Procesando 25 registros...
Procesados: 10/25 registros
Procesados: 20/25 registros
Procesados: 25/25 registros
Escribiendo archivo: matriz_calidad_export.json

==================================================
✅ EXPORTACIÓN COMPLETADA EXITOSAMENTE
==================================================
📁 Archivo: matriz_calidad_export.json
📊 Registros exportados: 25
💾 Tamaño del archivo: 0.05 MB
🕒 Fecha de exportación: 2025-01-XX 10:30:45

📈 ESTADÍSTICAS:
   • Por Tipología: {'ECUF': 10, 'ECN': 8, 'Estadistico': 7}
   • Activos: 23 | Inactivos: 2
   • Categorías únicas: 8
==================================================

🎉 Exportación finalizada correctamente
```

---

## 📞 Soporte

Para problemas o mejoras, contacta al equipo de desarrollo.