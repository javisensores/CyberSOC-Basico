# CyberSOC Básico - Proyecto Completo
Centro de Operaciones de Seguridad (SOC) con ELK Stack + GLPI

Estado del Proyecto: 100% COMPLETO Y FUNCIONAL
Última actualización: 04/02/2026

## Descripción del Proyecto

Sistema CyberSOC completo que implementa el ciclo de vida completo de eventos de seguridad, desde la detección hasta la gestión de incidentes.

### Componentes Implementados

| Requisito | Componente | Estado | Puerto | Descripción |
|-----------|-----------|--------|--------|-------------|
| **SIEM/Dashboards** | ELK Stack | OPERATIVO | 5601, 9200 | Elasticsearch + Logstash + Kibana |
| **Recolección** | syslog-ng + Filebeat | OPERATIVO | 514, 5044 | Captura de logs en tiempo real |
| **Gestión Incidentes** | GLPI + MySQL | OPERATIVO | 9000 | Sistema de ticketing |
| **Generación Tráfico** | simulate_attacks.ps1 | OPERATIVO | - | 11 escenarios de ataque |
| **Visualización** | Dashboard Kibana | OPERATIVO | 5601 | 3 visualizaciones configuradas |

### Reglas de Detección Activas (Logstash)

10 reglas de seguridad configuradas:
1. **SSH Brute Force** (severity: medium)
2. **SQL Injection** (severity: high)
3. **XSS Attack** (severity: high)
4. **Destructive Commands** (severity: critical)
5. **Privilege Escalation** (severity: critical)
6. **Port Scanning** (severity: medium)
7. **Suspicious Processes** (severity: high)
8. **Data Exfiltration** (severity: high)

### Política de Retención de Logs

| Severidad | Periodo Retención | Motivo | Storage |
|-----------|-------------------|--------|---------|
| **CRITICAL** | 90 días | Regulatorio, auditoría forense | Elasticsearch Hot |
| **HIGH** | 60 días | Investigación, patrones de ataque | Elasticsearch Warm |
| **MEDIUM** | 30 días | Análisis tendencias | Elasticsearch Warm |
| **Otros** | 7 días | Troubleshooting básico | Elasticsearch Cold |

Configuración Elasticsearch ILM (Index Lifecycle Management):
- **Hot Phase**: 0-7 días → Nodos rápidos SSD
- **Warm Phase**: 7-30 días → Nodos estándar
- **Cold Phase**: 30-90 días → Nodos económicos
- **Delete Phase**: >90 días → Eliminación automática

Cumplimiento Normativo:
- GDPR: Retención máxima justificada por seguridad
- Directiva NIS2: Logs de seguridad mínimo 90 días
- ISO 27001: Evidencia de controles de seguridad

### Taxonomía de Incidentes (VERIS/ENISA)

Framework VERIS utilizado para clasificación:

| Categoría | Subcategoría | Tags en Kibana | Severidad Típica |
|-----------|--------------|----------------|------------------|
| **Malware** | Cryptominer | `suspicious_process` | HIGH |
| **Malware** | Backdoor | `suspicious_process` | CRITICAL |
| **Hacking** | SQL Injection | `sql_injection` | HIGH |
| **Hacking** | XSS | `xss_attack` | HIGH |
| **Hacking** | Brute Force | `ssh_failed_login` | MEDIUM |
| **Hacking** | Scanning | `port_scan` | MEDIUM |
| **Misuse** | Privilege Abuse | `privilege_escalation` | CRITICAL |
| **Misuse** | Data Mishandling | `destructive_command` | CRITICAL |
| **Social** | Phishing | N/A | HIGH |
| **DoS** | Network Flood | `port_scan` | HIGH |
| **Error** | Misconfiguration | N/A | MEDIUM |

Categorización ENISA:
- **Availability**: DoS, Port Scanning
- **Confidentiality**: Data Exfiltration, SQL Injection
- **Integrity**: Destructive Commands, Privilege Escalation

### SLA (Service Level Agreement) por Severidad

| Severidad | Tiempo Detección | Tiempo Respuesta | Tiempo Resolución | Escalado Obligatorio |
|-----------|------------------|------------------|-------------------|---------------------|
| **CRITICAL** | Tiempo real (<1 min) | 15 minutos | 4 horas | CISO + Dirección |
| **HIGH** | <5 minutos | 1 hora | 24 horas | Supervisor SOC |
| **MEDIUM** | <15 minutos | 4 horas | 3 días | No requerido |
| **LOW** | <1 hora | 24 horas | 7 días | No requerido |

Penalizaciones por incumplimiento SLA:
- CRITICAL: Revisión inmediata del incidente + informe ejecutivo
- HIGH: Análisis de causa raíz
- MEDIUM/LOW: Seguimiento en próxima reunión SOC

Métricas de Rendimiento (KPI):
- MTTD (Mean Time To Detect): < 5 minutos
- MTTR (Mean Time To Respond): Según tabla SLA
- Tasa de falsos positivos: < 10%
- Cobertura de detección: > 95% de ataques conocidos

## Inicio Rápido (5 minutos)

### 1. Iniciar el Sistema
```powershell
.\start.ps1
```

Espera 30-60 segundos hasta que todos los contenedores estén healthy.

### 2. Acceder a las Interfaces

**Kibana (SIEM Dashboard)** - INTERFAZ PRINCIPAL
-  URL: **http://localhost:5601**
-  Sin credenciales
- Menú → Analytics → Discover

**GLPI (Gestión de Tickets)**
-  URL: **http://localhost:9000**
-  Usuario: `glpi` / Contraseña: `glpi`
- Ver [guía completa de instalación](glpi/GUIA-GLPI.md)

**IMPORTANTE**: NO acceder a `http://localhost:9200` (Elasticsearch no tiene interfaz web)

### 3. Configurar Kibana (Primera Vez)

1. Ir a: **Menú → Stack Management → Data Views**
2. Clic en **"Create data view"**
3. Configurar:
   - **Name**: `Syslog Security Events`
   - **Index pattern**: `syslog-*`
   - **Timestamp field**: `@timestamp`
4. Guardar

### 4. Generar Eventos de Prueba
```powershell
.\simulate_attacks.ps1
```
- Selecciona **opción 11** (Todos los ataques)
- O selecciona ataques individuales (1-10)

### 5. Visualizar Eventos en Kibana

**En Discover:**
- Buscar: `tags:"security_event"` → Ver todos los eventos
- Buscar: `severity:"critical"` → Solo eventos críticos
- Buscar: `severity:"high"` → Eventos de alta severidad
- Buscar: `event_type:"SSH Brute Force"` → Ataques SSH

**En Dashboard:**
- Ir a: **Analytics → Dashboard → "CyberSOC - Security Dashboard"**
- Ver 3 visualizaciones:
  - Eventos por Severidad (Pie Chart)
  - Timeline de Eventos (Area Chart)
  - Top Eventos de Seguridad (Bar Chart)

### 6. Crear Tickets en GLPI

1. Identificar un evento crítico en Kibana
2. Copiar detalles (timestamp, tipo, mensaje)
3. Ir a GLPI → **Asistencia → Crear ticket**
4. Completar:
   - **Título**: Descripción del incidente
   - **Descripción**: Detalles del evento de Kibana
   - **Prioridad**: Según severidad (6-Major para critical)
   - **Categoría**: Incident

## Arquitectura del Stack

### Arquitectura inicial (Primera versión)

``` 
┌─────────────────────────────────────────────────────────────────┐
│                 CyberSOC - Arquitectura Inicial                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Syslog Client  ───────►  Syslog Server (514/TCP)               │
│                              │                                  │
│  Filebeat  ──────────────────┘                                  │
│                              ▼                                  │
│                        Logstash (8 reglas)                      │
│                              ▼                                  │
│                      Elasticsearch (:9200)                      │
│                         ├──────────► Kibana (:5601)             │
│                         └──────────► GLPI (:9000) + MySQL       │
│                                                                 │
│  Flujo de tickets: principalmente manual desde analista SOC     │
│  (Kibana/Playbook → creación de ticket en GLPI).                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Arquitectura actual (Versión operativa final)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CyberSOC Stack COMPLETO                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐         ┌─────────────────┐                   │
│  │ Syslog Client│────────>│  Syslog Server  │                   │
│  │   (Logs)     │         │   (514/TCP)     │                   │
│  └──────────────┘         └────────┬────────┘                   │
│                                    │                            │
│  ┌──────────────┐                  │                            │
│  │   Filebeat   │──────────────────┘                            │
│  │  (Collector) │                                               │
│  └───────┬──────┘                                               │
│          v                                                      │
│  ┌──────────────────┐                                           │
│  │    Logstash      │                                           │
│  │  (Processing)    │                                           │
│  │  10 reglas       │                                           │
│  └────────┬─────────┘                                           │
│           v                                                     │
│  ┌──────────────────┐        ┌──────────────────────┐           │
│  │  Elasticsearch   │<───────│   GLPI Automation    │           │
│  │   (Storage)      │        │ (Poll + Correlation) │           │
│  │  Port: 9200      │        └──────────┬───────────┘           │
│  └────┬────────┬────┘                   │                       │
│       │        │                        │                       │
│       v        v                        v                       │
│  ┌──────────┐  ┌─────────────────┐  ┌──────────────┐            │
│  │  Kibana  │  │      GLPI       │  │    MySQL     │            │
│  │Dashboard │  │   (Ticketing)   │  │  (GLPI DB)   │            │
│  │  :5601   │  │      :9000      │  │              │            │
│  └──────────┘  └─────────────────┘  └──────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Comparación rápida (Antes vs Ahora)

| Elemento | Antes (Inicial) | Ahora (Actual) |
|----------|------------------|----------------|
| Reglas en Logstash | 8 reglas | 10 reglas |
| Ticketing | Predominio manual | Automatizado con `glpi-automation` + validación manual |
| Correlación | Básica (eventos directos) | Correlación adicional (`syslog-*` y `correlations-*`) |
| Servicios Docker | 8 servicios | 9 servicios |
| Flujo SOC | Ataque → Detección → Ticket manual | Ataque → Detección → Correlación → Ticket automático |

## Componentes del Stack

### 1. **Recolección de Logs (Agents)**
- **syslog-ng**: Cliente y servidor para agregación de logs (Puerto 514/TCP)
- **Filebeat 8.11.0**: Recolector avanzado de logs con procesamiento

### 2. **SIEM (ELK Stack)**
- **Elasticsearch 8.11.0**: Motor de búsqueda y almacenamiento (Puerto 9200)
  - **IMPORTANTE**: Elasticsearch es la API/backend (puerto 9200) - NO accedas directamente
- **Logstash 8.11.0**: Procesamiento con 10 reglas de detección (Puerto 5000)
- **Kibana 8.11.0**: **INTERFAZ VISUAL** - Dashboard web para análisis (Puerto 5601)
  - **ACCEDE AQUÍ**: http://localhost:5601 - Esta es la interfaz gráfica donde verás todo

### 3. **Gestión de Incidentes (Ticketing)**
- **GLPI**: Sistema de ticketing y gestión de incidentes (Puerto 9000)
  - **ACCEDE AQUÍ**: http://localhost:9000 - Login: glpi / glpi
  - Crea, asigna y hace seguimiento de tickets de seguridad
- **MySQL 8.0**: Base de datos para GLPI

### 4. **Automatización de Incidentes**
- **glpi-automation**: Servicio Python que consulta eventos en Elasticsearch y crea tickets automáticamente en GLPI (vía MySQL)
- Soporta correlación local y lectura de índices `syslog-*` y `correlations-*`

### 5. **Generación de Tráfico**
- **simulate_attacks.ps1**: Script con 11 tipos de ataques simulados

## ¿Qué es cada componente?

### Kibana vs Elasticsearch - ¿Cuál uso?

**Kibana (http://localhost:5601)** - **USA ESTE**
- Es la **interfaz visual** (dashboard web)
- Aquí ves gráficos, tablas, eventos de seguridad
- Es como el "Windows Explorer" del sistema
- **Accede SIEMPRE a Kibana para ver tus datos**

**� Elasticsearch (http://localhost:9200)** - NO accedas directamente
- Es el "motor" backend que almacena datos
- Solo muestra JSON crudo sin interfaz bonita
- Kibana usa Elasticsearch internamente
- Piensa en él como el "disco duro" del sistema

**Logstash** - Procesa logs automáticamente
- Recibe logs → Aplica reglas de detección → Envía a Elasticsearch
- NO tiene interfaz web
- Aplica 10 reglas de seguridad en tiempo real

## � Inicio Rápido

### Opción 1: Usar el script automatizado (Recomendado)

**PowerShell (Windows):**
```powershell
.\start.ps1
```

Este script:
- Verifica que Docker esté corriendo
- Inicia todos los servicios
- Espera a que estén listos
- Muestra las URLs de acceso

### Opción 2: Manual

```bash
docker-compose up -d
```

## � Requisitos Previos

- **Docker**: versión 20.10 o superior
- **Docker Compose**: versión 2.0 o superior
- **RAM**: Mínimo 8GB (recomendado 16GB)
- **Disco**: Mínimo 20GB libres
- **Sistema Operativo**: Windows 10/11, Linux, macOS

## Instalación y Despliegue

### 1. Clonar o descargar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd syslog-ng-ejemplo
```

### 2. Ajustar configuraciones (opcional)

Revisa y modifica los archivos de configuración según tus necesidades:

- `logstash/pipeline/logstash.conf` - Reglas de detección de Logstash (10 reglas personalizadas)
- `server/syslog-ng.conf` - Configuración del servidor syslog-ng
- `client/syslog-ng.conf` - Configuración del cliente syslog-ng

### 3. Levantar el entorno completo

```bash
docker-compose up -d
```

Este comando descargará todas las imágenes necesarias y levantará los contenedores en modo background.

**Tiempo de inicio**: 
- **ELK Stack**: ~1-2 minutos
- **GLPI + MySQL**: ~30-60 segundos adicionales

### 4. Verificar el estado de los contenedores

```bash
docker-compose ps
```

Debes ver **9 servicios** en estado `Up`:
```
syslog-server         Up
syslog-client         Up
elasticsearch-siem    Up
logstash-siem         Up
kibana-siem           Up
filebeat-collector    Up
glpi-mysql            Up
glpi-incidentes       Up
glpi-automation       Up
```

### 5. Ver logs de los servicios

```bash
# Ver todos los logs
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f logstash-siem
docker-compose logs -f glpi-incidentes
docker-compose logs -f glpi-automation
```

##  Acceso a las Interfaces Web

Una vez levantado el entorno, accede a:

| Servicio | URL | Usuario | Contraseña | Descripción |
|----------|-----|---------|------------|-------------|
| **Kibana (SIEM)** ⭐ | http://localhost:5601 | - | - | **Dashboard principal** - Accede aquí para ver eventos |
| **Elasticsearch API** | http://localhost:9200 | - | - | API backend (no accedas, usa Kibana) |

> **IMPORTANTE**: 
> - **Para ver eventos**: Usa **Kibana** (puerto 5601)
> - No accedas directamente a Elasticsearch (puerto 9200) - no tiene interfaz visual
> - Todos los eventos detectados aparecen en Kibana Discover automáticamente

> **Nota**: Kibana puede tardar 1-2 minutos en estar completamente disponible tras el inicio. No requiere usuario ni contraseña.

### 5. **Simulación de Ataques**

Usa el script de simulación para generar eventos de prueba:

**PowerShell (Windows):**
```powershell
.\simulate_attacks.ps1
```

**Bash (Linux/Mac):**
```bash
./simulate_attacks.sh
```

El script muestra un menú interactivo con 11 tipos de ataques:
1.  SSH Brute Force
2. � SQL Injection  
3.  Cross-Site Scripting (XSS)
4.  Path Traversal
5.  Comandos Destructivos
6. Escalada de Privilegios
7. Port Scanning
8.  Procesos Sospechosos
9.  Exfiltración de Datos
10.  Instalación No Autorizada
11.  Todos los ataques

Los eventos aparecen en **Kibana** en 5-10 segundos.

## Flujo de Trabajo Completo

### Flujo: Ataque → Detección → Visualización → Gestión

```
1. Generar Ataque
   └─> simulate_attacks.ps1
   
2. Captura de Logs
   └─> syslog-ng recibe eventos
   
3. Procesamiento
   └─> Logstash aplica reglas de detección
   └─> Clasifica: severity (critical/high/medium)
   └─> Añade tags: security_event, sql_injection, etc.
   
4. Almacenamiento
   └─> Elasticsearch indexa en syslog-*
   
5. Visualización
   └─> Kibana muestra en Dashboard
   └─> 3 gráficos: Severidad, Timeline, Top Eventos
   
6. Gestión de Incidentes
   └─> Crear ticket en GLPI
   └─> Asignar, priorizar, resolver
```

### Ejemplo Práctico Completo

**1. Generar ataque SQL Injection:**
```powershell
.\simulate_attacks.ps1  # Seleccionar opción 2
```

**2. Ver en Kibana (5-10 segundos después):**
- Ir a Dashboard: http://localhost:5601
- Buscar: `event_type:"SQL Injection Attempt"`
- Ver evento con `severity:"high"`

**3. Crear ticket en GLPI:**
- Abrir: http://localhost:9000
- **Asistencia → Crear ticket**
- **Título**: "ALTA: Intento de SQL Injection detectado"
- **Descripción**: Copiar detalles del evento de Kibana
- **Prioridad**: 5 - High
- **Categoría**: Incident

##  Dashboard de Kibana

El dashboard "CyberSOC - Security Dashboard" incluye:

### 1. Eventos por Severidad (Pie Chart)
- Distribución porcentual: critical, high, medium
- Permite identificar tendencias de riesgo

### 2. Timeline de Eventos (Area Chart)
- Evolución temporal de eventos
- Separado por colores según severidad
- Permite detectar picos de actividad

### 3. Top Eventos de Seguridad (Bar Horizontal)
- Los 10 tipos de eventos más frecuentes
- Ayuda a priorizar respuesta

### Auto-refresh
- Configurar en Kibana: Selector de tiempo → "Refresh every"
- Recomendado: 30 seconds o 1 minute
- Los eventos aparecen automáticamente

## � Comandos Útiles

### Gestión de Contenedores

```powershell
# Iniciar todos los servicios
docker-compose up -d

# Detener todos los servicios
docker-compose down

# Ver estado de servicios
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f logstash-siem
docker-compose logs -f kibana-siem

# Reiniciar un servicio específico
docker-compose restart logstash-siem

# Ver logs del servidor syslog
docker exec syslog-server tail -f /var/log/syslog-ng/messages
```

### Verificación de Eventos

```powershell
# Ver archivos de log en el servidor
docker exec syslog-server ls -lh /var/log/syslog-ng/syslog-client/

# Ver últimas líneas de un log específico
docker exec syslog-server tail -20 /var/log/syslog-ng/syslog-client/sshd.log

# Contar eventos en Elasticsearch
Invoke-RestMethod -Uri "http://localhost:9200/syslog-*/_count" -Method GET

# Buscar eventos específicos
Invoke-RestMethod -Uri "http://localhost:9200/syslog-*/_search?q=severity:critical" -Method GET
```

### Generar Eventos Manualmente

```powershell
# SSH Failed Login
docker exec syslog-client logger -t sshd "Failed password for admin from 192.168.1.100 port 22 ssh2"

# SQL Injection
docker exec syslog-client logger -t apache2 "SQL Injection: SELECT * FROM users WHERE id=1 OR 1=1"

# Comando Destructivo (CRITICAL)
docker exec syslog-client logger -t sudo "ROOT command: rm -rf /var/log/*"

# Proceso Sospechoso
docker exec syslog-client logger -t kernel "Suspicious process: /tmp/.hidden/cryptominer"
```

##  Escenarios de Prueba

### Escenario 1: SSH Brute Force Attack
```powershell
.\simulate_attacks.ps1  # Opción 1
```
**Resultado esperado:**
- Severity: medium
- Tag: ssh_failed_login
- Event Type: SSH Failed Authentication

### Escenario 2: SQL Injection
```powershell
.\simulate_attacks.ps1  # Opción 2
```
**Resultado esperado:**
- Severity: high
- Tag: sql_injection
- Event Type: SQL Injection Attempt

### Escenario 3: Comando Destructivo (CRITICAL)
```powershell
.\simulate_attacks.ps1  # Opción 5
```
**Resultado esperado:**
- Severity: **critical**
- Tag: destructive_command
- Event Type: Destructive Command

### Escenario 4: Ataque Completo
```powershell
.\simulate_attacks.ps1  # Opción 11 (Todos)
```
**Resultado esperado:**
- Genera todos los tipos de eventos
- Severidades: critical, high, medium
- Perfecto para demostración completa

##  Guías y Documentación

### Documentación Incluida

- **README.md** (este archivo) - Guía completa del proyecto
- **glpi/GUIA-GLPI.md** - Instalación y uso de GLPI
- **logstash/pipeline/logstash.conf** - Reglas de detección comentadas
- **docker-compose.yml** - Arquitectura de servicios

### Recursos Externos

- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Logstash Documentation](https://www.elastic.co/guide/en/logstash/current/index.html)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/index.html)
- [GLPI Documentation](https://glpi-project.org/documentation/)
- [Syslog-ng Documentation](https://www.syslog-ng.com/technical-documents/doc/syslog-ng-open-source-edition/)

**Resultado esperado**: Evento etiquetado con `ssh_failed_login` y `security_event` en Kibana.

### Ataque 2: SQL Injection

**PowerShell y Bash:**
```powershell
docker exec syslog-client logger -t apache "GET /login.php?id=1 OR 1=1 HTTP/1.1"
```

**Resultado esperado**: Evento etiquetado con `sql_injection` y severidad `high` en Kibana.

### Ataque 3: Comando Destructivo

**PowerShell y Bash:**
```powershell
docker exec syslog-client logger -t bash "User executed: rm -rf /important/data"
```

**Resultado esperado**: Evento etiquetado con `destructive_command` y severidad `critical` en Kibana.

### Ataque 4: Escalada de Privilegios

**PowerShell y Bash:**
```powershell
docker exec syslog-client logger -t su "User changed to root"
```

**Resultado esperado**: Evento etiquetado con `privilege_escalation` y severidad `high` en Kibana.

##  Demostración del Ciclo Completo

### Escenario: Detección y Gestión de Ataque de Fuerza Bruta

1. **Generación del ataque**:
   
   **PowerShell (Windows):**
   ```powershell
   for ($i = 1; $i -le 15; $i++) {
     docker exec syslog-client logger -p auth.warning -t sshd "Failed password for admin from 10.0.0.50 port 22 ssh2"
     Start-Sleep -Seconds 2
   }
   ```
   
   **Bash (Linux/Mac):**
   ```bash
   for i in {1..15}; do
     docker exec syslog-client logger -p auth.warning -t sshd "Failed password for admin from 10.0.0.50 port 22 ssh2"
     sleep 2
   done
   ```

2. **Detección en Kibana**:
   - Ve a Kibana → Discover
   - Busca: `tags:"ssh_failed_login"`
   - Observa los eventos con severidad `medium` y tipo `SSH Failed Authentication`

3. **Análisis del Incidente**:
   - Revisa el campo `message` para ver detalles completos
   - Verifica el campo `severity` → debe mostrar `medium`
   - Comprueba los tags: `ssh_failed_login` y `security_event`
   - Examina la IP de origen en el mensaje

4. **Documentación y Respuesta**:
   - **En entorno real**: Se crearía ticket en sistema ITSM
   - **Acciones sugeridas**:
     - [ ] Verificar si IP es interna o externa
     - [ ] Revisar logs completos del periodo
     - [ ] Bloquear IP en firewall
     - [ ] Notificar al equipo de red
   - **Para la demo**: Exporta eventos a CSV desde Kibana (botón "Share" → "CSV Reports")

## Comandos Útiles

### Gestión de Contenedores

```bash
# Iniciar todos los servicios
docker-compose up -d

# Detener todos los servicios
docker-compose down

# Reiniciar un servicio específico
docker restart logstash-siem

# Ver logs en tiempo real
docker-compose logs -f logstash-siem

# Acceder a un contenedor
docker exec -it logstash-siem bash

# Ver recursos utilizados
docker stats
```

### Limpieza y Mantenimiento

```bash
# Detener y eliminar contenedores + volúmenes
docker-compose down -v

# Limpiar sistema Docker
docker system prune -a

# Ver espacio utilizado
docker system df
```

### Backup de Datos

## � Solución de Problemas

### Problema: Kibana muestra "No results"

**Causa**: Rango de tiempo incorrecto o Data View sin crear

**Solución:**
1. Cambiar rango a "Last 24 hours" o "Last 7 days"
2. Verificar que existe el Data View `syslog-*`
3. Haz clic en "Refresh" en Kibana
4. Generar eventos nuevos con `simulate_attacks.ps1`

### Problema: Contenedores no inician

```powershell
# Ver logs detallados
docker-compose logs logstash-siem
docker-compose logs elasticsearch-siem

# Verificar estado
docker-compose ps

# Reiniciar todos
docker-compose down
docker-compose up -d
```

### Problema: Dashboard vacío

**Causa**: No hay eventos generados o Data View mal configurado

**Solución:**
1. Generar eventos: `.\simulate_attacks.ps1` (Opción 11)
2. Esperar 10-20 segundos
3. Refrescar Kibana
4. Verificar eventos: `Invoke-RestMethod -Uri "http://localhost:9200/syslog-*/_count"`

### Problema: GLPI no carga

**Causa**: MySQL no está listo o instalación incompleta

**Solución:**
1. Verificar MySQL: `docker-compose logs glpi-mysql`
2. Esperar 30 segundos adicionales
3. Completar instalación web en primer acceso
4. Seguir guía: [glpi/GUIA-GLPI.md](glpi/GUIA-GLPI.md)

## Requisitos del Proyecto Cumplidos

### Requisito 1: SIEM y Dashboards (ELK Stack)
- Elasticsearch 8.11.0 para almacenamiento
- Logstash 8.11.0 con 10 reglas de detección
- Kibana 8.11.0 con dashboard operativo
- 3 visualizaciones configuradas

### Requisito 2: Recolección de Logs (Agents)
- syslog-ng (cliente/servidor)
- Filebeat 8.11.0
- Captura en tiempo real

### Requisito 3: Gestión de Incidentes (Ticketing)
- GLPI con MySQL 8.0
- Sistema completo de tickets
- Taxonomía VERIS/ENISA implementada
- SLA definidos por severidad

### Requisito 4: Generación de Tráfico
- Script `simulate_attacks.ps1`
- 11 escenarios de ataque
- Clasificación por severidad

### Requisito 5: Playbook de Operación
- **PLAYBOOK.md** con 8 procedimientos completos
- Tiempos de respuesta y resolución definidos
- Comandos técnicos de contención
- Flujos de escalado documentados

### Requisito 6: Memoria Técnica
- Arquitectura de red documentada
- Política de retención de logs (90/60/30 días)
- Justificación técnica de herramientas
- Evidencias visuales en docs/screenshots/

### Bonus: Visualización Avanzada
- Dashboard interactivo
- Auto-refresh configurable
- Filtros por severidad y tipo

##  Documentación Completa

### � Archivos de Documentación

| Archivo | Propósito | Estado |
|---------|-----------|--------|
| **README.md** | Guía completa del proyecto | COMPLETO |
| **PLAYBOOK.md** | Manual de procedimientos SOC | COMPLETO |
| **glpi/GUIA-GLPI.md** | Instalación y uso de GLPI | COMPLETO |
| **docs/screenshots/README.md** | Guía para evidencias visuales | COMPLETO |
| **logstash/pipeline/logstash.conf** | Reglas comentadas | COMPLETO |
| **docker-compose.yml** | Arquitectura desplegable | COMPLETO |

### � Playbook de Respuesta a Incidentes

**[PLAYBOOK.md](PLAYBOOK.md)** incluye:
- 8 procedimientos de respuesta detallados
- SLA: 15 min (CRITICAL) a 3 días (MEDIUM)
- Taxonomía VERIS completa
- Contactos de escalado
- Comandos técnicos de PowerShell/Bash
- Flujos de trabajo ilustrados

###  Evidencias Visuales

**[docs/screenshots/README.md](docs/screenshots/README.md)** incluye:
- Guía para 13 capturas de pantalla
- Checklist de documentación visual
- Comandos específicos para cada captura
- Formato profesional para memoria

###  Política de Retención de Logs
- **CRITICAL**: 90 días (Elasticsearch Hot)
- **HIGH**: 60 días (Elasticsearch Warm)
- **MEDIUM**: 30 días (Elasticsearch Warm)
- **Otros**: 7 días (Elasticsearch Cold)

Cumplimiento: GDPR, Directiva NIS2, ISO 27001

### Taxonomía VERIS/ENISA
- **Malware**: Cryptominers, Backdoors
- **Hacking**: SQLi, XSS, Brute Force
- **Misuse**: Privilege Abuse, Destructive Commands
- **DoS**: Port Scanning

##  Créditos

Proyecto desarrollado para demostración de CyberSOC básico utilizando tecnologías open source.

**Tecnologías utilizadas:**
- ELK Stack (Elasticsearch, Logstash, Kibana) 8.11.0
- GLPI + MySQL 8.0
- syslog-ng
- Filebeat 8.11.0
- Docker & Docker Compose

##  Licencia

Este proyecto es de código abierto con fines educativos.

##  Soporte

Para consultas sobre el proyecto:
- Revisar [glpi/GUIA-GLPI.md](glpi/GUIA-GLPI.md) para configuración de GLPI
- Revisar logs: `docker-compose logs -f [servicio]`
- Verificar arquitectura en sección "Arquitectura del Stack"



**¡Proyecto CyberSOC 100% Completo y Operativo!**

##  Equipo y Contribuciones

Este proyecto ha sido desarrollado como parte de la **UD 4 - Construcción de un CyberSOC**.

## Licencia

Este proyecto es de código abierto bajo licencia MIT.

##  Notas para la Demo

### Puntos Clave a Demostrar:

1. **Infraestructura Docker** (3 min)
   - Ejecutar `.\start.ps1` para levantar todo
   - Mostrar `docker-compose ps` con servicios funcionando
   - Explicar flujo: syslog-ng → Logstash → Elasticsearch → Kibana

2. **Detección Automatizada** (4 min)
   - Ejecutar `.\simulate_attacks.ps1` opción 11
   - Mostrar en Kibana Discover: `tags:"security_event"`
   - Filtrar por severidad: `severity:"critical"` y `severity:"high"`
   - Mostrar campos: event_type, severity, message

3. **Análisis Visual** (3 min)
   - Crear visualización rápida (gráfico de barras por event_type)
   - Mostrar timeline de ataques
   - Exportar eventos a CSV
   - Explicar: "Sistema completo de detección y clasificación"

## Próximos Pasos (Mejoras Futuras)

- [ ] Integración con plataforma SOAR para respuesta automatizada
- [ ] Conexión con MISP para threat intelligence
- [ ] Alertas por email/Slack mediante Kibana Alerts
- [ ] Implementación de machine learning para detección de anomalías
- [ ] Dashboard personalizado con métricas KPI del SOC
- [ ] Integración con sistemas ITSM (JIRA, ServiceNow)



**¡Buena suerte con la demo! **
