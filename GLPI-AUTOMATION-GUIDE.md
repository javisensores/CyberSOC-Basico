# Guía de Automatización de GLPI - CyberSOC

## 📋 Cambios Realizados

### 1. **Integración de Automatización en Simulador de Ataques**

El script `simulate_attacks.ps1` ahora:
- Ejecuta cada ataque simulado
- **Automáticamente** crea tickets en GLPI después de cada ataque
- Espera 10 segundos para que los eventos lleguen a Elasticsearch
- Llama a `glpi_automation.py` en modo **one-shot**

### 2. **Nuevo Modo de Ejecución en `glpi_automation.py`**

Se han añadido **dos modos** de ejecución:

#### Modo Continuo (Polling)
```bash
python3 glpi_automation.py --mode continuous
```
- Busca eventos cada 30 segundos
- Crea tickets automáticamente
- Debe ejecutarse en un contenedor o servicio con `docker run`
- **Uso anterior (por defecto)**

#### Modo Una Sola Ejecución (One-Shot)
```bash
python3 glpi_automation.py --mode one-shot --minutes 15
```
- Busca eventos de los últimos 15 minutos
- Crea tickets automáticamente
- Se ejecuta una sola vez y sale
- **Llamado automáticamente por `simulate_attacks.ps1`**
- Parámetros:
  - `--minutes N`: Buscar eventos de los últimos N minutos (default: 5)

## 🎯 Flujo de Ejecución

### Antes (Comportamiento Antiguo)
```
1. Ejecutar: simulate_attacks.ps1
2. Simula ataques → Logs → Elasticsearch
3. Ejecutar (por separado): glpi_automation.py (polling continuo)
4. Cada 30 segundos crea tickets (incluso sin ataques nuevos)
```

### Ahora (Comportamiento Nuevo)
```
1. Ejecutar: simulate_attacks.ps1
2. Seleccionar ataque(s)
3. Simula ataques → Logs → Elasticsearch
4. ✅ AUTOMÁTICAMENTE: Crea tickets en GLPI
5. Tickets incluyen estructura de plantillas
```

## 🚀 Cómo Usar

### Opción 1: Demo Completa (Recomendado)
```powershell
cd C:\Users\Javier\Desktop\Ciber\Incidentes de Ciberseguridad\CyberSOC.Basico 2
.\simulate_attacks.ps1
# Seleccionar opción: 11
```

**Resultado:** 10 ataques simulados → 10 tickets creados en GLPI automáticamente

### Opción 2: Ataque Individual
```powershell
.\simulate_attacks.ps1
# Seleccionar opción: 1-10 (un ataque específico)
```

**Resultado:** 1 ataque simulado → 1 ticket creado en GLPI automáticamente

### Opción 3: Modo Manual (Continuo)
Para ejecutar el monitoreo continuo en un contenedor:
```bash
docker run -e ES_HOST=http://elasticsearch:9200 \
           -e GLPI_DB_HOST=mariadb \
           glpi-automation:latest \
           python3 glpi_automation.py --mode continuous
```

## 📊 Estructura de Tickets Generados

Cada ticket incluye:

### Información Básica
- **Título**: Severidad + Tipo de ataque + IP + Fecha
- **Descripción**: Estructura predefinida por tipo de ataque
- **Severidad**: LOW, MEDIUM, HIGH, CRITICAL

### Estructura de Contenido
```
TIPO DE ATAQUE (detectado)
Timestamp: DD/MM/YYYY HH:MM:SS
Host afectado: [hostname]
IP Origen: [IP]
Detalles específicos del ataque

DETECCIÓN:
- Regla Logstash aplicada
- Tags asignadas
- Relevancia

ACCIONES (según PLAYBOOK):
1. Acción inmediata 1
2. Acción inmediata 2
3. Acción de investigación
4. Acción de remediación
```

## 🎭 Tipos de Ataques y Tickets

| Ataque | Severidad | Urgencia | Acciones |
|--------|-----------|----------|----------|
| SSH Brute Force | MEDIUM | 3 | Bloquear IP, revisar logs auth |
| SQL Injection | HIGH | 4 | Bloquear IP, activar WAF |
| XSS Attack | HIGH | 4 | Sanitizar inputs, CSP |
| Path Traversal | MEDIUM | 3 | Revisar permisos, bloquear IP |
| Comando Destructivo | CRITICAL | 5 | Aislar host, análisis forense |
| Escalada Privilegios | CRITICAL | 5 | Bloquear usuario, auditar sudo |
| Escaneo Puertos | MEDIUM | 3 | Bloquear IP, revisar firewall |
| Proceso Sospechoso | HIGH | 4 | Matar proceso, aislar host |
| Exfiltración Datos | HIGH | 4 | Bloquear conexión destino |
| Software No Autorizado | MEDIUM | 3 | Desinstalar, revisar logs |

## 🔍 Verificación

### 1. Ver tickets creados en GLPI
```
http://localhost:80
Usuario: glpi
Contraseña: glpi
Ir a: Asistencia → Tickets
```

### 2. Ver eventos en Kibana
```
http://localhost:5601
Discovery → Filtrar por: tags:security_event
```

### 3. Verificar ejecución de automatización
El script muestra en consola:
```
========================================================
GLPI Security Events Automation
========================================================
Modo: one-shot
Buscando eventos de los últimos 15 minutos
Elasticsearch: http://localhost:9200
GLPI Database: localhost

✅ Conectado a Elasticsearch: 8.x.x
✅ Conectado a base de datos GLPI

🔍 Buscando eventos de los últimos 15 minutos...

📊 Se encontraron 5 eventos de seguridad

✅ Ticket #123 creado en GLPI
   Título: CRITICAL: Comando destructivo detectado - 11/02/2026
   Severidad: critical

✅ 5 tickets creados

✅ Proceso completado
```

## ⚙️ Variables de Entorno

Para personalizar la creación de tickets:

```bash
# Base de datos GLPI
ES_HOST=http://elasticsearch:9200
GLPI_ES_INDEXES=syslog-*,correlations-*
GLPI_ES_IGNORE_UNAVAILABLE=true
GLPI_DB_HOST=localhost
GLPI_DB_USER=glpi_user
GLPI_DB_PASSWORD=glpi_password
GLPI_DB_NAME=glpidb

# IDs de configuración GLPI
GLPI_CATEGORY_ID=3           # Categoría de tickets (default: 0)
GLPI_ENTITY_ID=1             # Entidad/Organización (default: 0)
GLPI_REQUESTER_ID=1          # Usuario solicitante (default: 0)
GLPI_RECIPIENT_ID=1          # Usuario destinatario (default: 0)
GLPI_GROUP_ID=1              # Grupo responsable (default: 0)
GLPI_TEMPLATE_ID=1           # Plantilla de ticket (default: 0)
GLPI_REQUESTTYPE_ID=3        # Tipo de solicitud (default: 0)

# Correlacion (si usas Kibana rules)
GLPI_ENABLE_LOCAL_CORRELATION=false

# Correlacion local (si la activas)
GLPI_SSH_BRUTE_FORCE_THRESHOLD=10
GLPI_SSH_BRUTE_FORCE_WINDOW_MINUTES=5
GLPI_SSH_BRUTE_FORCE_COOLDOWN_MINUTES=5
```

## 🐛 Troubleshooting

### Los tickets no se crean
1. ✅ Verificar que Elasticsearch esté accesible
2. ✅ Verificar que los eventos llegaron a Elasticsearch
3. ✅ Verificar que GLPI DB esté accesible
4. ✅ Revisar credenciales en `glpi_automation.py`

### Los eventos no se detectan
1. ✅ Verificar que `logger` funciona en el contenedor
2. ✅ Verificar que syslog-ng está escuchando
3. ✅ Revisar en Kibana si los eventos están ahí

### Python no se encuentra
En Windows:
```powershell
# Instalar Python desde https://www.python.org/
# O usar WSL:
wsl python3 glpi_automation.py --mode one-shot
```

## 📝 Archivos Modificados

1. **`glpi_automation.py`**
   - Añadido argparse para CLI
   - Nuevo parámetro `--mode` (continuous/one-shot)
   - Nuevo parámetro `--minutes` (para one-shot)
   - Refactorizado main() para soportar ambos modos

2. **`simulate_attacks.ps1`**
   - Añadida función `Create-GLPITickets`
   - Llamar a esta función después de cada ataque
   - Mensajes informativos mejorados
   - Loop de espera para Elasticsearch

## 📞 Próximos Pasos

### Mejoras Futuras
- [ ] Integración con webhook de Elasticsearch
- [ ] Notificaciones por email
- [ ] Escala automática de severidad según contexto
- [ ] Correlación de eventos
- [ ] Dashboard en tiempo real

### Monitoreo Continuo
Para ejecutar el monitoreo en segundo plano:
```bash
# Linux/WSL
nohup python3 glpi_automation.py --mode continuous > /var/log/glpi-automation.log &

# Windows (opción 1): ejecutar en PowerShell como servicio
Start-Process -FilePath "python.exe" -ArgumentList "glpi_automation.py", "--mode", "continuous" -WindowStyle Hidden

# Windows (opción 2): crear tarea programada
# Tareas Programadas → Crear tarea → Ejecutar cada 30 segundos
```
