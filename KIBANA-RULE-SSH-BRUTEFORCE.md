# Kibana Rule - SSH Brute Force (correlacion)

## Objetivo
Crear una regla en Kibana que detecte 10 fallos de login SSH en 5 minutos por IP y escriba un evento de correlacion en Elasticsearch para que GLPI cree el ticket.

## Requisitos
- Kibana y Elasticsearch levantados
- Logstash ya agrega el tag `ssh_failed_login` y el campo `src_ip`

## Pasos en Kibana (UI)
1) Ir a **Stack Management** -> **Rules and Connectors** -> **Rules** -> **Create rule**
2) Rule type: **Elasticsearch query**
3) Indices: `syslog-*`
4) Query (KQL): `tags: "ssh_failed_login"`
5) Time window: **5 minutes**, check every **1 minute**
6) Group by: `src_ip` (top 100)
7) Threshold: **count >= 10**

## Action - Indexar correlacion
1) Crear un connector tipo **Index** (si no existe)
2) Index name: `correlations-ssh`
3) Document (usar variables desde **Action Variables** en la UI):

```json
{
  "@timestamp": "{{context.date}}",
  "event_type": "SSH Brute Force (correlacion)",
  "severity": "medium",
  "tags": ["ssh_brute_force", "security_event"],
  "host": { "ip": ["{{alert.id}}"] },
  "attempts": "{{context.value}}",
  "window_minutes": 5
}
```

Si la UI muestra variables con otros nombres, usa el panel **Action variables** para insertar los correctos. En esta regla, la IP del grupo se obtiene con `alert.id`.

## GLPI automation
- El servicio `glpi-automation` lee `syslog-*` y `correlations-*`.
- La correlacion local esta desactivada por defecto en `docker-compose.yml` con `GLPI_ENABLE_LOCAL_CORRELATION=false` para evitar duplicados.
