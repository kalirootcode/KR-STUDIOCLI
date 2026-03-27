# Terminal de Kali Linux — Guía Completa para IA

## Metadatos del Conocimiento
- **Dominio**: Línea de comandos, shell scripting y administración de sistemas en Kali Linux
- **Shell por defecto**: Zsh (zsh) con Oh My Zsh — anteriormente Bash
- **Versión de referencia**: Kali Linux 2024.x / Zsh 5.x / Bash 5.x
- **Alcance**: Navegación, gestión de archivos, procesos, redes, usuarios, scripting y productividad en terminal

---

## 1. La Shell en Kali Linux

### Shells disponibles
```bash
cat /etc/shells                        # Ver shells instaladas
echo $SHELL                            # Shell activa
chsh -s /bin/bash                      # Cambiar shell a Bash
chsh -s /bin/zsh                       # Cambiar shell a Zsh
bash                                   # Abrir sesión bash dentro de zsh
zsh                                    # Abrir sesión zsh dentro de bash
```

### Archivos de configuración
```
Bash:
  ~/.bashrc          → Configuración interactiva (aliases, funciones, PS1)
  ~/.bash_profile    → Ejecutado al login
  ~/.bash_logout     → Ejecutado al cerrar sesión
  ~/.bash_history    → Historial de comandos
  /etc/bash.bashrc   → Configuración global de bash

Zsh:
  ~/.zshrc           → Configuración principal
  ~/.zprofile        → Equivalente a .bash_profile
  ~/.zhistory        → Historial de comandos
  /etc/zsh/zshrc     → Configuración global de zsh
```
```bash
source ~/.bashrc                       # Recargar configuración sin cerrar terminal
source ~/.zshrc
exec bash                              # Reiniciar shell completamente
```

---

## 2. Navegación del Sistema de Archivos

### Comandos básicos de navegación
```bash
pwd                                    # Directorio actual (Print Working Directory)
ls                                     # Listar archivos
ls -l                                  # Formato largo (permisos, dueño, tamaño, fecha)
ls -la                                 # Incluir archivos ocultos
ls -lh                                 # Tamaños legibles (KB, MB, GB)
ls -lt                                 # Ordenar por fecha de modificación
ls -lS                                 # Ordenar por tamaño
ls -R                                  # Recursivo (subdirectorios)
ls -1                                  # Un archivo por línea
ls --color=auto                        # Con colores
ls *.txt                               # Solo archivos .txt

cd /ruta/absoluta                      # Ir a ruta absoluta
cd ruta/relativa                       # Ir a ruta relativa
cd ..                                  # Subir un directorio
cd ../..                               # Subir dos directorios
cd ~                                   # Ir al home
cd -                                   # Volver al directorio anterior
cd /                                   # Ir a la raíz

tree                                   # Árbol de directorios
tree -L 2                              # Solo 2 niveles de profundidad
tree -a                                # Incluir ocultos
tree -d                                # Solo directorios
tree -h                                # Con tamaños legibles
```

### Estructura del sistema de archivos Linux
```
/                   → Raíz del sistema
├── /bin            → Binarios esenciales del sistema
├── /sbin           → Binarios del sistema para root
├── /usr            → Programas de usuario
│   ├── /usr/bin    → Binarios de usuario
│   ├── /usr/sbin   → Binarios del sistema (usuario)
│   └── /usr/share  → Archivos compartidos, wordlists, datos
├── /etc            → Archivos de configuración
├── /home           → Directorios de usuarios
├── /root           → Home del usuario root
├── /var            → Datos variables (logs, bases de datos)
│   └── /var/log    → Logs del sistema
├── /tmp            → Archivos temporales (se limpia al reiniciar)
├── /dev            → Dispositivos como archivos
├── /proc           → Información de procesos (virtual)
├── /sys            → Información del kernel (virtual)
├── /mnt            → Puntos de montaje manuales
├── /media          → Montaje automático (USB, CD)
├── /opt            → Software de terceros
├── /lib            → Librerías del sistema
└── /boot           → Archivos de arranque
```

---

## 3. Gestión de Archivos y Directorios

### Crear, copiar, mover, eliminar
```bash
# Crear
touch archivo.txt                      # Crear archivo vacío (o actualizar timestamp)
touch archivo1.txt archivo2.txt        # Múltiples archivos
touch archivo_{1..5}.txt               # Expansión: archivo_1.txt a archivo_5.txt
mkdir carpeta                          # Crear directorio
mkdir -p ruta/profunda/nueva           # Crear estructura de directorios completa
mkdir -p proyecto/{src,bin,docs,tests} # Crear múltiples subdirectorios

# Copiar
cp origen.txt destino.txt              # Copiar archivo
cp -r carpeta/ destino/                # Copiar directorio recursivamente
cp -p archivo.txt copia.txt            # Preservar permisos, timestamps
cp -i origen destino                   # Preguntar antes de sobreescribir
cp -v origen destino                   # Verbose (mostrar lo que copia)
cp -u origen destino                   # Copiar solo si origen es más nuevo
cp archivo.txt /ruta/destino/          # Copiar a otro directorio

# Mover / Renombrar
mv viejo.txt nuevo.txt                 # Renombrar
mv archivo.txt /ruta/destino/          # Mover
mv -i origen destino                   # Preguntar antes de sobreescribir
mv -v origen destino                   # Verbose
mv carpeta1/ carpeta2/                 # Renombrar directorio

# Eliminar
rm archivo.txt                         # Eliminar archivo
rm -f archivo.txt                      # Forzar (sin confirmación)
rm -r carpeta/                         # Eliminar directorio recursivamente
rm -rf carpeta/                        # ⚠️ Forzar eliminación recursiva
rm -i archivo.txt                      # Pedir confirmación
rm -v archivo.txt                      # Verbose
rmdir carpeta/                         # Eliminar directorio VACÍO

# Renombrado masivo
rename 's/.txt/.bak/' *.txt            # Renombrar extensiones (Perl rename)
rename 's/foo/bar/g' *                 # Reemplazar texto en nombres
for f in *.jpg; do mv "$f" "${f%.jpg}.png"; done  # Con bucle
```

### Buscar archivos
```bash
# find — El más poderoso
find / -name "archivo.txt"             # Buscar por nombre (toda la raíz)
find . -name "*.log"                   # Buscar por extensión en directorio actual
find . -iname "*.LOG"                  # Insensible a mayúsculas
find /home -type f                     # Solo archivos
find /home -type d                     # Solo directorios
find /home -type l                     # Solo enlaces simbólicos
find . -size +100M                     # Archivos mayores a 100MB
find . -size -10k                      # Archivos menores a 10KB
find . -newer archivo.txt              # Más nuevos que archivo.txt
find . -mtime -7                       # Modificados en los últimos 7 días
find . -mtime +30                      # Modificados hace más de 30 días
find . -atime -1                       # Accedidos en las últimas 24h
find / -perm -4000                     # Archivos con SUID
find / -perm -2000                     # Archivos con SGID
find / -perm /o+w                      # Archivos escribibles por todos
find / -user root                      # Pertenecientes a root
find / -group www-data                 # Pertenecientes a un grupo
find . -empty                          # Archivos/directorios vacíos
find . -name "*.txt" -exec cat {} \;   # Ejecutar comando en cada resultado
find . -name "*.log" -exec rm {} +     # Eliminar todos los .log encontrados
find . -name "*.conf" | xargs grep "password"  # Buscar texto en resultados

# locate — Más rápido (usa base de datos)
locate archivo.txt                     # Búsqueda rápida
locate -i ARCHIVO.TXT                  # Case insensitive
locate "*.conf"                        # Con comodín
updatedb                               # Actualizar base de datos de locate

# which / whereis — Encontrar ejecutables
which python3                          # Ruta del ejecutable en uso
which -a python3                       # Todas las rutas disponibles
whereis python3                        # Binario + man pages + código fuente
type ls                                # Ver tipo de comando (alias, builtin, etc.)
```

---

## 4. Visualización y Edición de Archivos

### Ver contenido
```bash
cat archivo.txt                        # Mostrar contenido completo
cat -n archivo.txt                     # Con números de línea
cat -A archivo.txt                     # Mostrar caracteres especiales
cat archivo1.txt archivo2.txt          # Concatenar dos archivos
tac archivo.txt                        # Mostrar al revés (última línea primero)

less archivo.txt                       # Paginador (recomendado para archivos grandes)
# Dentro de less:
# j/k o flechas → navegar línea a línea
# f/b           → avanzar/retroceder página
# g / G         → ir al inicio / final
# /texto        → buscar hacia adelante
# ?texto        → buscar hacia atrás
# n / N         → siguiente/anterior resultado
# q             → salir

more archivo.txt                       # Paginador simple (solo avanza)

head archivo.txt                       # Primeras 10 líneas
head -n 20 archivo.txt                 # Primeras 20 líneas
head -c 100 archivo.txt                # Primeros 100 bytes

tail archivo.txt                       # Últimas 10 líneas
tail -n 20 archivo.txt                 # Últimas 20 líneas
tail -f /var/log/syslog                # Seguir archivo en tiempo real
tail -F /var/log/auth.log              # Seguir y reabrir si rota

wc archivo.txt                         # Contar líneas, palabras, bytes
wc -l archivo.txt                      # Solo líneas
wc -w archivo.txt                      # Solo palabras
wc -c archivo.txt                      # Solo bytes

# Archivos binarios
xxd archivo.bin                        # Vista hexadecimal + ASCII
xxd -l 64 archivo.bin                  # Solo primeros 64 bytes
hexdump -C archivo.bin                 # Alternativa
od -An -tx1 archivo.bin                # Octal dump en hex
strings archivo.bin                    # Extraer strings legibles
file archivo.desconocido               # Identificar tipo de archivo
```

### Editores de texto en terminal
```bash
# Nano — El más sencillo
nano archivo.txt
# Atajos: Ctrl+O guardar, Ctrl+X salir, Ctrl+K cortar, Ctrl+U pegar
# Ctrl+W buscar, Ctrl+\ reemplazar, Ctrl+G ayuda

# Vim — El más poderoso
vim archivo.txt
vi archivo.txt
# Modos:
# Normal (Esc)   → navegación y comandos
# Insert (i/a/o) → escribir texto
# Visual (v/V)   → selección
# Command (:)    → comandos de vim

# Comandos Vim esenciales
# :w              → guardar
# :q              → salir
# :wq o :x        → guardar y salir
# :q!             → salir sin guardar
# :set nu         → mostrar números de línea
# /texto          → buscar
# :s/viejo/nuevo/g → reemplazar en línea actual
# :%s/viejo/nuevo/g → reemplazar en todo el archivo
# dd              → eliminar línea
# yy              → copiar línea
# p               → pegar
# u               → deshacer
# Ctrl+r          → rehacer
# gg / G          → inicio / final del archivo
# :n              → ir a línea n

# Micro — Moderno e intuitivo
micro archivo.txt
# Ctrl+S guardar, Ctrl+Q salir, Ctrl+F buscar

# Gedit — GUI (si hay entorno gráfico)
gedit archivo.txt &
```

---

## 5. Permisos y Propietarios

### Entender permisos
```
Formato: -rwxrwxrwx
         │└──┬──┘└──┬──┘└──┬──┘
         │  dueño  grupo  otros
         │
         └ tipo: - archivo, d directorio, l symlink, b bloque, c char

r = read    (4) — Leer el archivo / listar directorio
w = write   (2) — Escribir el archivo / crear en directorio
x = execute (1) — Ejecutar el archivo / entrar al directorio

Notación octal:
7 = rwx, 6 = rw-, 5 = r-x, 4 = r--, 3 = -wx, 2 = -w-, 1 = --x, 0 = ---
755 = rwxr-xr-x (típico para directorios)
644 = rw-r--r-- (típico para archivos)
600 = rw------- (archivos privados, ej: claves SSH)
777 = rwxrwxrwx (todos los permisos ⚠️)
```

### chmod, chown, chgrp
```bash
# chmod — Cambiar permisos
chmod 755 archivo.sh                   # Octal
chmod 644 archivo.txt
chmod +x script.sh                     # Agregar ejecución a todos
chmod -x script.sh                     # Quitar ejecución
chmod u+x script.sh                    # Agregar ejecución solo al dueño
chmod g-w archivo.txt                  # Quitar escritura al grupo
chmod o-r archivo.txt                  # Quitar lectura a otros
chmod a+r archivo.txt                  # Agregar lectura a todos
chmod -R 755 carpeta/                  # Recursivo

# Permisos especiales
chmod 4755 binario                     # SUID: ejecutar como dueño
chmod 2755 carpeta/                    # SGID: heredar grupo
chmod 1777 /tmp                        # Sticky bit: solo dueño elimina

# chown — Cambiar propietario
chown usuario archivo.txt
chown usuario:grupo archivo.txt
chown -R usuario:grupo carpeta/        # Recursivo
chown :grupo archivo.txt               # Solo cambiar grupo

# chgrp — Cambiar grupo
chgrp grupo archivo.txt
chgrp -R grupo carpeta/

# Ver permisos detallados
ls -la
stat archivo.txt                       # Info completa incluyendo inodo
getfacl archivo.txt                    # ACL (listas de control de acceso)
setfacl -m u:usuario:rwx archivo.txt   # Establecer ACL
```

---

## 6. Gestión de Procesos
```bash
# Ver procesos
ps                                     # Procesos del usuario en terminal actual
ps aux                                 # TODOS los procesos del sistema
ps aux | grep python                   # Filtrar procesos
ps -ef                                 # Formato completo
ps -p PID                              # Proceso específico
ps --forest                            # Árbol de procesos
pstree                                 # Árbol visual
pstree -p                              # Con PIDs

# Monitoreo en tiempo real
top                                    # Monitor interactivo
# Dentro de top: q salir, k matar proceso, r renice, M ordenar por memoria
htop                                   # Versión mejorada (recomendado)
# htop: F6 ordenar, F9 matar, F10 salir
btop                                   # Moderno con gráficas
glances                                # Monitor todo-en-uno

# Información de procesos
pidof firefox                          # PID por nombre
pgrep ssh                              # PIDs que coinciden con patrón
pgrep -l ssh                           # Con nombres
lsof                                   # Archivos abiertos por procesos
lsof -p PID                            # Archivos de un proceso específico
lsof -i :80                            # Proceso usando puerto 80
lsof -u usuario                        # Archivos del usuario

# Matar procesos
kill PID                               # Señal SIGTERM (terminar limpiamente)
kill -9 PID                            # SIGKILL (forzar, inmediato)
kill -15 PID                           # SIGTERM (por defecto)
kill -HUP PID                          # SIGHUP (recargar configuración)
killall firefox                        # Matar por nombre
killall -9 firefox                     # Forzar
pkill proceso                          # Matar por patrón
pkill -u usuario                       # Matar todos los procesos de un usuario

# Jobs (procesos en background)
comando &                              # Ejecutar en background
Ctrl+Z                                 # Suspender proceso actual
jobs                                   # Listar jobs
jobs -l                                # Con PIDs
fg                                     # Traer último job al frente
fg %1                                  # Traer job #1 al frente
bg                                     # Continuar último job en background
bg %2                                  # Continuar job #2 en background
disown %1                              # Desconectar job del terminal (sigue corriendo)
nohup comando &                        # Ejecutar ignorando hangup (sigue tras cerrar terminal)

# Prioridad de procesos
nice -n 10 comando                     # Iniciar con prioridad baja (10)
nice -n -20 comando                    # Iniciar con máxima prioridad (root)
renice 10 -p PID                       # Cambiar prioridad de proceso corriendo
renice -n 5 -u usuario                 # Cambiar prioridad de todos los procesos del usuario

# Información de uso de recursos
free -h                                # Memoria RAM y swap
vmstat 1 5                             # Estadísticas de VM cada 1 seg, 5 veces
iostat                                 # Estadísticas de I/O
mpstat                                 # Estadísticas por CPU
sar -u 1 5                             # CPU usage histórico
```

---

## 7. Redirección y Pipes

### Redirección de entrada/salida
```bash
# Descriptores estándar
# 0 = stdin  (entrada estándar)
# 1 = stdout (salida estándar)
# 2 = stderr (error estándar)

# Redirección de salida
comando > archivo.txt                  # stdout → archivo (sobreescribe)
comando >> archivo.txt                 # stdout → archivo (agrega al final)
comando 2> errores.txt                 # stderr → archivo
comando 2>> errores.txt                # stderr → archivo (agrega)
comando > salida.txt 2>&1             # stdout y stderr → mismo archivo
comando &> todo.txt                    # Shorthand: stdout+stderr → archivo
comando > /dev/null                    # Descartar stdout
comando 2>/dev/null                    # Descartar stderr
comando &>/dev/null                    # Descartar todo

# Redirección de entrada
comando < archivo.txt                  # stdin desde archivo
comando << EOF                         # Here document
Texto multilínea
EOF
comando <<< "texto"                    # Here string

# Ejemplos prácticos
nmap -sS 192.168.1.0/24 > escaneo.txt 2>/dev/null
cat /etc/passwd > copia_passwd.txt
echo "nueva linea" >> archivo.txt
sort < desordenado.txt > ordenado.txt
```

### Pipes (|)
```bash
# Encadenar comandos: salida de uno → entrada del siguiente
ls -la | grep ".txt"
ps aux | grep -v grep | grep python
cat /etc/passwd | cut -d: -f1 | sort
cat archivo.txt | wc -l
cat /var/log/auth.log | grep "Failed" | tail -20
echo "TEXTO" | tr 'A-Z' 'a-z'
ls | head -5
netstat -tulpn | grep :80

# tee — Redirigir a archivo Y mostrar en pantalla
nmap 192.168.1.1 | tee resultado.txt
ls -la | tee -a archivo.txt            # -a para agregar (no sobreescribir)

# xargs — Pasar resultados como argumentos
find . -name "*.tmp" | xargs rm
cat ips.txt | xargs -I {} ping -c 1 {}
ls *.txt | xargs -n 1 wc -l
find . -name "*.log" | xargs grep "ERROR"
echo "uno dos tres" | xargs -n 1 echo  # Separar en argumentos individuales
```

---

## 8. Procesamiento de Texto

### grep — Buscar patrones
```bash
grep "patrón" archivo.txt              # Buscar texto
grep -i "PATRÓN" archivo.txt           # Case insensitive
grep -v "patrón" archivo.txt           # Inverso (líneas que NO coinciden)
grep -n "patrón" archivo.txt           # Con número de línea
grep -c "patrón" archivo.txt           # Contar coincidencias
grep -l "patrón" *.txt                 # Archivos que contienen el patrón
grep -r "patrón" /carpeta/             # Recursivo en directorio
grep -R "patrón" /carpeta/             # Recursivo siguiendo symlinks
grep -w "palabra" archivo.txt          # Coincidencia de palabra completa
grep -x "línea exacta" archivo.txt     # Coincidencia de línea exacta
grep -A 3 "patrón" archivo.txt         # 3 líneas DESPUÉS del match
grep -B 3 "patrón" archivo.txt         # 3 líneas ANTES del match
grep -C 3 "patrón" archivo.txt         # 3 líneas antes y después
grep -m 5 "patrón" archivo.txt         # Máximo 5 resultados
grep -o "patrón" archivo.txt           # Solo mostrar la parte que coincide
grep --color=auto "patrón" archivo.txt # Resaltar coincidencias

# Expresiones regulares con grep
grep -E "patrón1|patrón2" archivo.txt  # OR (Extended regex)
grep -E "^inicio" archivo.txt          # Líneas que empiezan con "inicio"
grep -E "final$" archivo.txt           # Líneas que terminan con "final"
grep -E "[0-9]{3}" archivo.txt         # Exactamente 3 dígitos
grep -E "\b\w{5}\b" archivo.txt        # Palabras de exactamente 5 caracteres
grep -P "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}" archivo.txt  # IPs (Perl regex)
grep -oP "(?<=password=)\S+" config.txt  # Lookahead (Perl regex)
```

### sed — Editor de flujo (stream editor)
```bash
sed 's/viejo/nuevo/' archivo.txt       # Reemplazar primera ocurrencia por línea
sed 's/viejo/nuevo/g' archivo.txt      # Reemplazar todas las ocurrencias
sed 's/viejo/nuevo/gi' archivo.txt     # Case insensitive + global
sed -i 's/viejo/nuevo/g' archivo.txt   # Modificar archivo en lugar (in-place)
sed -i.bak 's/viejo/nuevo/g' arch.txt  # Con backup .bak
sed '/patrón/d' archivo.txt            # Eliminar líneas que coincidan
sed -n '/patrón/p' archivo.txt         # Imprimir solo líneas que coincidan
sed '3d' archivo.txt                   # Eliminar línea 3
sed '1,5d' archivo.txt                 # Eliminar líneas 1 a 5
sed 'Nd' archivo.txt                   # Eliminar cada N líneas
sed -n '5,10p' archivo.txt             # Imprimir líneas 5 a 10
sed 's/^/    /' archivo.txt            # Agregar 4 espacios al inicio de cada línea
sed 's/ *$//' archivo.txt              # Eliminar espacios al final de línea
sed '/^$/d' archivo.txt                # Eliminar líneas vacías
sed 'G' archivo.txt                    # Agregar línea en blanco después de cada línea
```

### awk — Procesamiento de columnas y datos
```bash
awk '{print $1}' archivo.txt           # Imprimir primera columna
awk '{print $1,$3}' archivo.txt        # Columnas 1 y 3
awk -F: '{print $1}' /etc/passwd       # Separador personalizado (:)
awk -F, '{print $2}' datos.csv         # CSV: segunda columna
awk 'NR==5' archivo.txt                # Solo la línea 5
awk 'NR>=5 && NR<=10' archivo.txt      # Líneas 5 a 10
awk '/patrón/{print}' archivo.txt      # Líneas que coincidan con patrón
awk '$3 > 100' datos.txt               # Columna 3 mayor a 100
awk '{sum += $1} END {print sum}' nums.txt  # Sumar columna 1
awk 'END {print NR}' archivo.txt       # Contar líneas
awk '{print NF}' archivo.txt           # Número de campos por línea
awk '{print toupper($0)}' archivo.txt  # Convertir a mayúsculas
awk -F: '{printf "%-20s %s\n", $1, $7}' /etc/passwd  # Printf formateado

# Ejemplos prácticos
ps aux | awk '{print $2, $11}' | head  # PID y comando
cat /etc/passwd | awk -F: '$3 > 1000 {print $1}' # Usuarios con UID > 1000
df -h | awk 'NR>1 {print $5, $6}' | sort -rn  # Uso de disco ordenado
```

### cut, sort, uniq, tr
```bash
# cut — Extraer columnas/campos
cut -d: -f1 /etc/passwd                # Campo 1 con delimitador :
cut -d, -f1,3 datos.csv                # Campos 1 y 3 de CSV
cut -c1-10 archivo.txt                 # Caracteres 1 al 10 de cada línea
cut -d' ' -f2- archivo.txt             # Desde el campo 2 en adelante

# sort — Ordenar
sort archivo.txt                       # Alfabético ascendente
sort -r archivo.txt                    # Inverso
sort -n archivo.txt                    # Numérico
sort -rn archivo.txt                   # Numérico inverso
sort -k2 archivo.txt                   # Por columna 2
sort -k2 -t: /etc/passwd               # Por columna 2 con separador :
sort -u archivo.txt                    # Ordenar y eliminar duplicados
sort -h archivo.txt                    # Ordenar tamaños legibles (1K, 2M, 3G)

# uniq — Eliminar/contar duplicados (requiere input ordenado)
uniq archivo.txt                       # Eliminar líneas duplicadas contiguas
uniq -c archivo.txt                    # Contar ocurrencias
uniq -d archivo.txt                    # Solo mostrar duplicadas
uniq -u archivo.txt                    # Solo mostrar únicas
sort archivo.txt | uniq -c | sort -rn  # Contar y ordenar por frecuencia

# tr — Traducir/transformar caracteres
tr 'a-z' 'A-Z' < archivo.txt          # Minúsculas a mayúsculas
tr 'A-Z' 'a-z' < archivo.txt          # Mayúsculas a minúsculas
tr -d '\n' < archivo.txt               # Eliminar saltos de línea
tr -d ' ' < archivo.txt                # Eliminar espacios
tr -s ' ' < archivo.txt                # Reducir espacios múltiples a uno
tr ':' '\n' <<< "$PATH"                # Reemplazar : por newline
echo "hola mundo" | tr ' ' '_'         # Reemplazar espacios con guion bajo
```

---

## 9. Gestión de Usuarios y Grupos
```bash
# Información de usuarios
whoami                                 # Usuario actual
id                                     # UID, GID y grupos del usuario actual
id usuario                             # Info de otro usuario
who                                    # Usuarios conectados actualmente
w                                      # Usuarios conectados con actividad
last                                   # Historial de logins
lastlog                                # Último login de cada usuario
finger usuario                         # Info detallada del usuario

# Crear y gestionar usuarios
sudo useradd -m -s /bin/bash usuario   # Crear usuario con home y bash
sudo useradd -m -G sudo,www-data -s /bin/bash -c "Nombre Completo" usuario
sudo passwd usuario                    # Establecer/cambiar contraseña
sudo usermod -aG sudo usuario          # Agregar a grupo sudo
sudo usermod -aG grupo1,grupo2 usuario # Agregar a múltiples grupos
sudo usermod -l nuevo_nombre viejo     # Renombrar usuario
sudo usermod -d /nuevo/home usuario    # Cambiar directorio home
sudo usermod -s /bin/zsh usuario       # Cambiar shell
sudo userdel usuario                   # Eliminar usuario (mantiene home)
sudo userdel -r usuario                # Eliminar usuario y su home

# Grupos
sudo groupadd nombre_grupo             # Crear grupo
sudo groupdel nombre_grupo             # Eliminar grupo
sudo groupmod -n nuevo viejo           # Renombrar grupo
groups                                 # Grupos del usuario actual
groups usuario                         # Grupos de otro usuario
cat /etc/group                         # Todos los grupos del sistema

# Cambiar de usuario
su usuario                             # Cambiar a usuario (mantiene env)
su - usuario                           # Cambiar a usuario (nuevo env de login)
su -                                   # Cambiar a root
sudo comando                           # Ejecutar como root
sudo -i                                # Shell interactiva como root
sudo -u usuario comando                # Ejecutar como otro usuario
sudo -l                                # Ver permisos sudo del usuario actual

# Archivos importantes
cat /etc/passwd                        # Usuarios del sistema
cat /etc/shadow                        # Hashes de contraseñas (solo root)
cat /etc/group                         # Grupos
cat /etc/sudoers                       # Configuración sudo
sudo visudo                            # Editar sudoers (forma segura)
```

---

## 10. Gestión de Paquetes (APT)
```bash
# Actualizar
sudo apt update                        # Actualizar lista de repositorios
sudo apt upgrade                       # Actualizar paquetes instalados
sudo apt full-upgrade                  # Actualizar incluyendo cambios de dependencias
sudo apt dist-upgrade                  # Actualizar distribución
sudo apt autoremove                    # Eliminar paquetes huérfanos
sudo apt autoclean                     # Limpiar cache de paquetes viejos
sudo apt clean                         # Limpiar toda la cache

# Instalar y eliminar
sudo apt install paquete               # Instalar paquete
sudo apt install paquete1 paquete2     # Múltiples paquetes
sudo apt install -y paquete            # Sin confirmación
sudo apt install --reinstall paquete   # Reinstalar
sudo apt remove paquete                # Eliminar (mantiene config)
sudo apt purge paquete                 # Eliminar + configs
sudo apt autoremove paquete            # Eliminar + dependencias huérfanas

# Buscar e información
apt search nombre                      # Buscar paquetes
apt show paquete                       # Info detallada del paquete
apt list --installed                   # Paquetes instalados
apt list --upgradable                  # Paquetes con actualización disponible
dpkg -l | grep paquete                 # Buscar paquetes instalados con dpkg
dpkg -L paquete                        # Archivos de un paquete instalado
dpkg -S /ruta/al/archivo               # Qué paquete provee ese archivo
dpkg --get-selections                  # Todos los paquetes instalados

# dpkg — Instalar .deb directamente
sudo dpkg -i paquete.deb               # Instalar .deb
sudo dpkg -r paquete                   # Remover
sudo apt install -f                    # Arreglar dependencias rotas tras dpkg

# Repositorios
cat /etc/apt/sources.list              # Lista de repositorios
ls /etc/apt/sources.list.d/            # Repos adicionales
sudo add-apt-repository ppa:nombre/repo  # Agregar PPA
sudo add-apt-repository --remove ppa:nombre/repo

# Snap y otros gestores
snap install paquete                   # Instalar snap
snap list                              # Snaps instalados
snap refresh                           # Actualizar snaps
pip install paquete                    # Python pip
pip3 install paquete
pip install -r requirements.txt        # Instalar desde archivo
gem install paquete                    # Ruby gems
```

---

## 11. Gestión de Servicios (systemd)
```bash
# Controlar servicios
sudo systemctl start servicio          # Iniciar
sudo systemctl stop servicio           # Detener
sudo systemctl restart servicio        # Reiniciar
sudo systemctl reload servicio         # Recargar configuración (sin reiniciar)
sudo systemctl status servicio         # Ver estado detallado
sudo systemctl enable servicio         # Habilitar al inicio
sudo systemctl disable servicio        # Deshabilitar del inicio
sudo systemctl enable --now servicio   # Habilitar e iniciar ahora
sudo systemctl is-active servicio      # ¿Está activo?
sudo systemctl is-enabled servicio     # ¿Está habilitado?

# Ver servicios
systemctl list-units --type=service            # Servicios activos
systemctl list-units --type=service --all      # Todos (incluyendo inactivos)
systemctl list-unit-files --type=service       # Estado de habilitación
systemctl list-units --failed                  # Servicios con fallo

# Logs de servicios
journalctl -u servicio                 # Logs del servicio
journalctl -u servicio -f              # Seguir logs en tiempo real
journalctl -u servicio --since today   # Logs de hoy
journalctl -u servicio -n 50           # Últimas 50 líneas
journalctl -p err                      # Solo errores
journalctl --since "2024-01-01 00:00:00"
journalctl --disk-usage                # Espacio usado por logs

# Servicios comunes en Kali
sudo systemctl start ssh               # SSH server
sudo systemctl start apache2           # Apache web server
sudo systemctl start mysql             # MySQL
sudo systemctl start postgresql        # PostgreSQL (para Metasploit)
sudo systemctl start NetworkManager    # Gestor de red
```

---

## 12. Redes desde la Terminal
```bash
# Información de red
ip a                                   # Ver interfaces y IPs
ip addr show eth0                      # Interfaz específica
ip link show                           # Ver interfaces (solo estado)
ip route                               # Tabla de rutas
ip route show                          # Misma tabla
ip neigh                               # Tabla ARP
ifconfig                               # Clásico (puede no estar instalado)
ifconfig eth0                          # Info de interfaz específica

# Configurar interfaces
sudo ip addr add 192.168.1.100/24 dev eth0     # Asignar IP
sudo ip addr del 192.168.1.100/24 dev eth0     # Quitar IP
sudo ip link set eth0 up                       # Levantar interfaz
sudo ip link set eth0 down                     # Bajar interfaz
sudo ip route add default via 192.168.1.1     # Agregar gateway
sudo ip route add 10.0.0.0/8 via 192.168.1.1  # Agregar ruta estática
sudo ip route del 10.0.0.0/8                   # Eliminar ruta

# DNS
cat /etc/resolv.conf                   # Servidores DNS configurados
sudo nano /etc/resolv.conf             # Editar DNS
cat /etc/hosts                         # Resolución local de nombres
sudo nano /etc/hosts                   # Editar hosts locales

# Conectividad
ping 8.8.8.8                           # Test ICMP
ping -c 4 google.com                   # 4 pings
ping -i 0.2 -c 10 192.168.1.1          # Intervalo 0.2s, 10 pings
ping -s 1000 192.168.1.1               # Tamaño de paquete 1000 bytes
traceroute google.com                  # Ruta de paquetes
traceroute -I google.com               # Usando ICMP
mtr google.com                         # Traceroute continuo
curl -I http://dominio.com             # Solo cabeceras HTTP
curl http://dominio.com                # GET request
wget http://dominio.com/archivo        # Descargar archivo

# Puertos y conexiones
ss -tulpn                              # Puertos TCP/UDP abiertos con procesos
ss -an                                 # Todas las conexiones
ss -s                                  # Estadísticas de sockets
netstat -tulpn                         # Alternativa clásica
netstat -an | grep ESTABLISHED         # Conexiones establecidas
lsof -i                                # Archivos de red abiertos
lsof -i :80                            # Proceso usando puerto 80
fuser 80/tcp                           # PID usando puerto 80

# Transferencia de archivos
scp archivo.txt usuario@192.168.1.1:/ruta/         # Copiar a remoto
scp usuario@192.168.1.1:/ruta/archivo.txt .        # Copiar desde remoto
scp -r carpeta/ usuario@192.168.1.1:/ruta/         # Directorio completo
rsync -avz carpeta/ usuario@192.168.1.1:/ruta/     # Sync eficiente
rsync -avz --progress archivo usuario@host:/ruta/  # Con progreso
sftp usuario@192.168.1.1                           # FTP seguro interactivo

# curl avanzado
curl -X POST -d "user=admin&pass=test" http://dominio.com/login
curl -X POST -H "Content-Type: application/json" -d '{"key":"val"}' http://api.com
curl -b "cookie=valor" http://dominio.com
curl -u usuario:contraseña http://dominio.com
curl -k https://dominio.com                        # Ignorar SSL
curl -L http://dominio.com                         # Seguir redirecciones
curl -o archivo.zip http://dominio.com/file.zip    # Guardar con nombre
curl --proxy http://127.0.0.1:8080 http://dominio.com  # Usar proxy (Burp)

# wget
wget http://dominio.com/archivo.zip
wget -r http://dominio.com/                        # Descargar sitio completo
wget -q http://url/archivo                         # Silencioso
wget --no-check-certificate https://dominio.com/archivo
wget -c http://url/archivo                         # Reanudar descarga interrumpida
```

---

## 13. Variables de Entorno y Shell
```bash
# Ver variables
env                                    # Todas las variables de entorno
printenv                               # Igual que env
printenv PATH                          # Variable específica
echo $HOME                             # Expandir variable
echo $USER
echo $SHELL
echo $TERM
echo $PWD
echo $OLDPWD                           # Directorio anterior
echo $HOSTNAME
echo $RANDOM                           # Número aleatorio
echo $LINENO                           # Número de línea actual
echo $?                                # Código de salida del último comando
echo $$                                # PID del shell actual
echo $!                                # PID del último proceso en background

# Definir variables
MI_VAR="valor"                         # Variable local (solo en shell actual)
export MI_VAR="valor"                  # Variable de entorno (disponible en subprocesos)
export PATH="$PATH:/nueva/ruta"        # Agregar al PATH
unset MI_VAR                           # Eliminar variable

# Variables especiales en scripts
$0                                     # Nombre del script
$1, $2, $3...                          # Argumentos posicionales
$#                                     # Número de argumentos
$@                                     # Todos los argumentos (como lista)
$*                                     # Todos los argumentos (como string)
$?                                     # Código de salida del último comando (0=éxito)
$$                                     # PID del script

# Hacer variables persistentes
echo 'export MI_VAR="valor"' >> ~/.bashrc
echo 'export MI_VAR="valor"' >> ~/.zshrc
source ~/.bashrc                       # Recargar sin cerrar terminal
```

---

## 14. Aliases y Funciones
```bash
# Aliases
alias                                  # Ver todos los alias definidos
alias ll='ls -la'                      # Definir alias
alias gs='git status'
alias update='sudo apt update && sudo apt upgrade -y'
alias cls='clear'
alias ..='cd ..'
alias ...='cd ../..'
alias grep='grep --color=auto'
alias df='df -h'
alias free='free -h'
alias myip='curl -s ipinfo.io/ip'
unalias ll                             # Eliminar alias

# Alias persistentes (agregar a ~/.bashrc o ~/.zshrc)
echo "alias ll='ls -la'" >> ~/.bashrc
source ~/.bashrc

# Funciones
mkcd() {
  mkdir -p "$1" && cd "$1"
}

extract() {
  case "$1" in
    *.tar.gz)  tar xzf "$1" ;;
    *.tar.bz2) tar xjf "$1" ;;
    *.zip)     unzip "$1" ;;
    *.7z)      7z x "$1" ;;
    *.rar)     unrar x "$1" ;;
    *)         echo "Formato no soportado" ;;
  esac
}

# Usar funciones
mkcd nueva-carpeta                     # Crea y entra al directorio
extract archivo.tar.gz                 # Extrae cualquier formato
```

---

## 15. Scripting Bash

### Estructura básica
```bash
#!/bin/bash
# Descripción del script
# Autor: nombre
# Fecha: 2024

# Variables
VARIABLE="valor"
readonly CONSTANTE="inmutable"
NUMERO=42

# Lectura de usuario
read -p "Ingresa tu nombre: " NOMBRE
read -sp "Contraseña: " PASS            # -s: ocultar input
echo ""

echo "Hola, $NOMBRE"
```

### Condicionales
```bash
# if/elif/else
if [ "$variable" == "valor" ]; then
    echo "Es igual"
elif [ "$variable" == "otro" ]; then
    echo "Es otro"
else
    echo "Es diferente"
fi

# Operadores de comparación de strings
# == o = → igual
# !=      → distinto
# -z      → string vacío
# -n      → string no vacío

# Operadores numéricos
# -eq → igual         -ne → no igual
# -lt → menor que     -le → menor o igual
# -gt → mayor que     -ge → mayor o igual

# Operadores de archivos
# -f → es archivo regular   -d → es directorio
# -e → existe               -r → es legible
# -w → es escribible        -x → es ejecutable
# -s → no está vacío        -L → es symlink

if [ -f "/etc/passwd" ]; then
    echo "El archivo existe"
fi

if [ $NUMERO -gt 10 ]; then
    echo "Mayor que 10"
fi

# Doble corchete (bash extended)
if [[ "$string" =~ ^[0-9]+$ ]]; then   # Regex
    echo "Es un número"
fi

if [[ -f "$file" && -r "$file" ]]; then  # AND
    echo "Existe y es legible"
fi

# Operador ternario
resultado=$( [ $x -gt 0 ] && echo "positivo" || echo "no positivo" )
```

### Bucles
```bash
# for — Iterar sobre lista
for i in 1 2 3 4 5; do
    echo "Número: $i"
done

for archivo in *.txt; do
    echo "Procesando: $archivo"
done

for i in {1..10}; do
    echo $i
done

for i in {0..100..10}; do             # Con paso de 10
    echo $i
done

# for estilo C
for ((i=0; i<10; i++)); do
    echo $i
done

# while
CONTADOR=0
while [ $CONTADOR -lt 10 ]; do
    echo "Contador: $CONTADOR"
    ((CONTADOR++))
done

# until — Hasta que la condición sea verdadera
until [ $CONTADOR -ge 10 ]; do
    echo $CONTADOR
    ((CONTADOR++))
done

# Leer líneas de archivo
while IFS= read -r linea; do
    echo "Línea: $linea"
done < archivo.txt

# Leer output de comando
while read -r linea; do
    echo "$linea"
done <<< "$(ls -la)"

# break y continue
for i in {1..10}; do
    [ $i -eq 5 ] && continue          # Saltar el 5
    [ $i -eq 8 ] && break             # Parar en el 8
    echo $i
done
```

### Funciones en scripts
```bash
# Definición
mi_funcion() {
    local variable_local="solo dentro"  # Variable local
    echo "Argumento 1: $1"
    echo "Argumento 2: $2"
    return 0                            # Código de retorno
}

# Llamar función
mi_funcion "valor1" "valor2"
RESULTADO=$(mi_funcion "arg")          # Capturar output
echo "Retornó: $?"                     # Verificar código de retorno

# Manejo de errores
set -e                                 # Salir si cualquier comando falla
set -u                                 # Error si variable no definida
set -o pipefail                        # Error si cualquier parte del pipe falla
set -euo pipefail                      # Los tres juntos (recomendado en scripts)

# Trap — Manejo de señales
trap 'echo "Script interrumpido"; exit 1' INT TERM
trap 'rm -f /tmp/archivo_temporal.txt' EXIT  # Limpiar al salir
```

### Arrays
```bash
# Definir arrays
FRUTAS=("manzana" "pera" "banana")
NUMEROS=(1 2 3 4 5)

# Acceder elementos
echo ${FRUTAS[0]}                      # Primer elemento
echo ${FRUTAS[-1]}                     # Último elemento
echo ${FRUTAS[@]}                      # Todos los elementos
echo ${#FRUTAS[@]}                     # Cantidad de elementos

# Modificar
FRUTAS+=("uva")                        # Agregar elemento
FRUTAS[1]="naranja"                    # Modificar elemento
unset FRUTAS[2]                        # Eliminar elemento

# Iterar
for fruta in "${FRUTAS[@]}"; do
    echo "$fruta"
done

# Arrays asociativos (diccionarios)
declare -A PERSONA
PERSONA[nombre]="Juan"
PERSONA[edad]=30
PERSONA[ciudad]="Bogotá"
echo ${PERSONA[nombre]}
echo ${!PERSONA[@]}                    # Ver todas las claves
```

---

## 16. Compresión y Archivado
```bash
# tar
tar -czf archivo.tar.gz carpeta/       # Comprimir con gzip
tar -cjf archivo.tar.bz2 carpeta/      # Comprimir con bzip2
tar -cJf archivo.tar.xz carpeta/       # Comprimir con xz (mejor ratio)
tar -czf backup.tar.gz -C /ruta .      # Comprimir desde directorio específico
tar -tzf archivo.tar.gz                # Ver contenido sin extraer
tar -xzf archivo.tar.gz                # Extraer en directorio actual
tar -xzf archivo.tar.gz -C /destino/   # Extraer en directorio específico
tar -xzf archivo.tar.gz archivo.txt    # Extraer solo un archivo
tar --exclude='*.log' -czf backup.tar.gz carpeta/  # Excluir archivos

# gzip / bzip2 / xz
gzip archivo.txt                       # Comprimir (reemplaza con .gz)
gzip -d archivo.txt.gz                 # Descomprimir
gunzip archivo.txt.gz                  # Igual
gzip -k archivo.txt                    # Mantener original
gzip -9 archivo.txt                    # Máxima compresión
zcat archivo.gz                        # Ver contenido sin descomprimir
bzip2 archivo.txt                      # Comprimir con bzip2
bunzip2 archivo.txt.bz2

# zip / unzip
zip archivo.zip archivo1.txt archivo2.txt
zip -r archivo.zip carpeta/            # Recursivo
zip -e archivo.zip carpeta/            # Con contraseña
unzip archivo.zip                      # Extraer
unzip archivo.zip -d /destino/         # Extraer en directorio
unzip -l archivo.zip                   # Ver contenido
unzip -o archivo.zip                   # Sobreescribir sin preguntar

# 7zip
7z a archivo.7z carpeta/              # Comprimir
7z e archivo.7z                        # Extraer
7z l archivo.7z                        # Listar contenido
7z a -p archivo.7z carpeta/            # Con contraseña
```

---

## 17. Gestión de Discos y Sistema de Archivos
```bash
# Información de discos
df -h                                  # Espacio en particiones montadas
df -i                                  # Uso de inodos
du -sh carpeta/                        # Tamaño de una carpeta
du -sh *                               # Tamaño de todo en el directorio actual
du -sh * | sort -h                     # Ordenado por tamaño
du -sh * | sort -rh | head -10         # Top 10 más grandes
ncdu /                                 # Navegador de uso de disco (interactivo)

lsblk                                  # Listar dispositivos de bloque
lsblk -f                               # Con sistema de archivos
fdisk -l                               # Particiones (requiere root)
parted -l                              # Alternativa a fdisk
blkid                                  # IDs y tipos de particiones

# Montar y desmontar
sudo mount /dev/sdb1 /mnt/usb          # Montar dispositivo
sudo mount -t ntfs /dev/sdb1 /mnt/     # Especificar tipo de FS
sudo mount -o ro /dev/sdb1 /mnt/       # Solo lectura
sudo umount /mnt/usb                   # Desmontar
sudo umount -f /mnt/usb                # Forzar desmontaje
mount | grep sdb                       # Ver montajes activos

# /etc/fstab — Montaje automático
cat /etc/fstab
# UUID=xxxx /punto/montaje tipo opciones dump pass

# Inodos y links
ln archivo.txt enlace_duro             # Hard link
ln -s archivo.txt enlace_simbolico     # Symbolic link (symlink)
ls -li                                 # Ver número de inodo
readlink enlace_simbolico              # Ver destino del symlink

# Verificar y reparar
sudo fsck /dev/sdb1                    # Verificar sistema de archivos
sudo fsck -y /dev/sdb1                 # Reparar automáticamente
sudo e2fsck -f /dev/sdb1               # Para ext2/3/4
```

---

## 18. Historial y Productividad en Terminal
```bash
# Historial de comandos
history                                # Ver historial
history 20                             # Últimos 20 comandos
history | grep "git"                   # Buscar en historial
!123                                   # Ejecutar comando #123 del historial
!!                                     # Repetir último comando
!ssh                                   # Último comando que empieza con "ssh"
!$                                     # Último argumento del comando anterior
!^                                     # Primer argumento del comando anterior
^viejo^nuevo                           # Corregir el último comando reemplazando texto
HISTSIZE=10000                         # Tamaño del historial en memoria
HISTFILESIZE=20000                     # Tamaño del archivo de historial
HISTCONTROL=ignoredups                 # No guardar duplicados consecutivos
history -c                             # Limpiar historial de la sesión

# Búsqueda en historial
Ctrl+R                                 # Búsqueda reversa incremental (la más útil)
# Escribe caracteres para buscar, Ctrl+R para siguiente resultado, Enter para ejecutar

# Atajos de teclado esenciales
Ctrl+A                                 # Ir al inicio de la línea
Ctrl+E                                 # Ir al final de la línea
Ctrl+U                                 # Borrar desde cursor hasta inicio
Ctrl+K                                 # Borrar desde cursor hasta final
Ctrl+W                                 # Borrar palabra anterior
Alt+D                                  # Borrar palabra siguiente
Ctrl+Y                                 # Pegar lo que se borró (yank)
Ctrl+L                                 # Limpiar pantalla (equivale a clear)
Ctrl+C                                 # Interrumpir proceso actual
Ctrl+D                                 # EOF / cerrar terminal
Ctrl+Z                                 # Suspender proceso al background
Ctrl+S                                 # Pausar output del terminal
Ctrl+Q                                 # Reanudar output del terminal
Alt+.                                  # Pegar último argumento del comando anterior
Tab                                    # Autocompletar
Tab Tab                                # Ver todas las opciones de autocompletado

# Expansiones de shell
echo {a,b,c}.txt                       # → a.txt b.txt c.txt
echo {1..5}                            # → 1 2 3 4 5
echo {a..z}                            # → a b c ... z
echo pre{fix1,fix2}suf                 # → prefix1suf prefix2suf
mkdir -p proyecto/{src,bin,docs}       # Crear múltiples directorios

# Sustitución de comandos
echo "Hoy es $(date)"                  # Ejecutar comando y capturar salida
ARCHIVOS=$(ls *.txt)
USUARIOS=$(cat /etc/passwd | cut -d: -f1)

# Multiplicidad con xargs
find . -name "*.txt" | xargs wc -l
cat servers.txt | xargs -P 4 -I {} ping -c 1 {}  # 4 en paralelo
```

---

## 19. Multiplexores de Terminal

### tmux
```bash
# Instalar y abrir
sudo apt install tmux
tmux                                   # Nueva sesión
tmux new -s nombre                     # Nueva sesión con nombre
tmux ls                                # Listar sesiones
tmux attach                            # Reconectar a última sesión
tmux attach -t nombre                  # Reconectar a sesión específica
tmux kill-session -t nombre            # Matar sesión

# Dentro de tmux (prefijo por defecto: Ctrl+B)
Ctrl+B c         # Nueva ventana
Ctrl+B n         # Siguiente ventana
Ctrl+B p         # Ventana anterior
Ctrl+B 0-9       # Ir a ventana por número
Ctrl+B ,         # Renombrar ventana actual
Ctrl+B &         # Cerrar ventana actual

Ctrl+B %         # Split vertical (paneles lado a lado)
Ctrl+B "         # Split horizontal (paneles arriba/abajo)
Ctrl+B flechas   # Moverse entre paneles
Ctrl+B Alt+flechas  # Redimensionar panel
Ctrl+B z         # Zoom en panel actual (toggle)
Ctrl+B x         # Cerrar panel actual

Ctrl+B d         # Desconectar sesión (sigue corriendo)
Ctrl+B s         # Listar sesiones
Ctrl+B $         # Renombrar sesión
Ctrl+B [         # Modo scroll (q para salir)

# ~/.tmux.conf — Configuración
set -g prefix C-a                      # Cambiar prefijo a Ctrl+A
set -g mouse on                        # Habilitar mouse
set -g history-limit 50000
set -g base-index 1                    # Numerar ventanas desde 1
```

### screen
```bash
screen                                 # Nueva sesión
screen -S nombre                       # Nueva sesión con nombre
screen -ls                             # Listar sesiones
screen -r nombre                       # Reconectar

# Dentro de screen (prefijo: Ctrl+A)
Ctrl+A c         # Nueva ventana
Ctrl+A n         # Siguiente ventana
Ctrl+A p         # Ventana anterior
Ctrl+A "         # Listar ventanas
Ctrl+A d         # Desconectar
Ctrl+A k         # Matar ventana
Ctrl+A |         # Split vertical
Ctrl+A S         # Split horizontal
Ctrl+A Tab       # Moverse entre paneles
```

---

## 20. Crontab — Tareas Programadas
```bash
crontab -l                             # Ver tareas del usuario
crontab -e                             # Editar tareas del usuario
crontab -r                             # Eliminar todas las tareas
sudo crontab -l                        # Ver tareas de root
sudo crontab -e                        # Editar tareas de root

# Formato:
# ┌───────────── minuto (0-59)
# │ ┌───────────── hora (0-23)
# │ │ ┌───────────── día del mes (1-31)
# │ │ │ ┌───────────── mes (1-12)
# │ │ │ │ ┌───────────── día de la semana (0=Dom, 6=Sáb)
# │ │ │ │ │
# * * * * * comando

# Ejemplos
* * * * *   /ruta/script.sh            # Cada minuto
0 * * * *   /ruta/script.sh            # Cada hora (en el minuto 0)
0 9 * * *   /ruta/script.sh            # Cada día a las 9:00 AM
0 9 * * 1   /ruta/script.sh            # Cada lunes a las 9:00 AM
0 0 1 * *   /ruta/script.sh            # Primer día de cada mes a medianoche
0 0 1 1 *   /ruta/script.sh            # Cada 1 de enero
*/5 * * * * /ruta/script.sh            # Cada 5 minutos
0 9-18 * * 1-5 /ruta/script.sh        # 9-18h de lunes a viernes

# Atajos especiales
@reboot     /ruta/script.sh            # Al arrancar el sistema
@hourly     /ruta/script.sh            # Cada hora
@daily      /ruta/script.sh            # Diariamente
@weekly     /ruta/script.sh            # Semanalmente
@monthly    /ruta/script.sh            # Mensualmente

# Archivos de cron del sistema
cat /etc/crontab
ls /etc/cron.d/
ls /etc/cron.daily/
ls /etc/cron.hourly/
ls /etc/cron.weekly/
ls /etc/cron.monthly/
```

---

## 21. Logs del Sistema
```bash
# Archivos de log importantes
/var/log/syslog           # Log general del sistema
/var/log/auth.log         # Autenticaciones y sudo
/var/log/kern.log         # Mensajes del kernel
/var/log/dmesg            # Mensajes de arranque (dispositivos)
/var/log/dpkg.log         # Instalaciones de paquetes
/var/log/apt/history.log  # Historial de apt
/var/log/apache2/         # Logs de Apache
/var/log/nginx/           # Logs de Nginx
/var/log/mysql/           # Logs de MySQL
/var/log/ufw.log          # Logs del firewall

# Ver logs
sudo tail -f /var/log/syslog           # Seguir en tiempo real
sudo tail -f /var/log/auth.log
sudo grep "Failed" /var/log/auth.log   # Intentos fallidos de login
sudo grep "sudo" /var/log/auth.log     # Comandos sudo ejecutados
dmesg                                  # Mensajes del kernel
dmesg | grep -i error                  # Solo errores
dmesg -T                               # Con timestamps legibles
dmesg -w                               # Seguir en tiempo real

# journalctl (systemd)
journalctl                             # Todos los logs
journalctl -f                          # Seguir en tiempo real
journalctl -n 100                      # Últimas 100 líneas
journalctl -p err                      # Solo errores
journalctl -p warning                  # Warnings y más graves
journalctl -u ssh                      # Solo servicio SSH
journalctl --since "1 hour ago"
journalctl --since "2024-01-01" --until "2024-01-31"
journalctl -b                          # Solo arranque actual
journalctl -b -1                       # Arranque anterior
journalctl --disk-usage                # Espacio usado por logs
sudo journalctl --vacuum-size=1G       # Limpiar hasta dejar solo 1GB
```

---

## 22. Comandos de Información del Sistema
```bash
# Hardware y sistema
uname -a                               # Info del kernel completa
uname -r                               # Solo versión del kernel
uname -m                               # Arquitectura
hostnamectl                            # Info del host
lscpu                                  # Info de la CPU
cat /proc/cpuinfo                      # Info detallada de CPU
nproc                                  # Número de procesadores
lsmem                                  # Info de memoria
free -h                                # Uso de RAM y swap
cat /proc/meminfo                      # Info detallada de memoria
lspci                                  # Dispositivos PCI
lspci -v                               # Verbose
lsusb                                  # Dispositivos USB
lsblk                                  # Dispositivos de bloque
lsblk -f                               # Con sistema de archivos
hwinfo --short                         # Resumen de hardware
inxi -Fxz                              # Info completa del sistema

# Tiempo y fecha
date                                   # Fecha y hora actual
date "+%Y-%m-%d %H:%M:%S"             # Formato personalizado
date +%s                               # Unix timestamp
timedatectl                            # Info de zona horaria y NTP
timedatectl set-timezone America/Bogota
uptime                                 # Tiempo encendido y carga
uptime -p                              # Formato legible
cal                                    # Calendario del mes
cal 2024                               # Calendario del año

# Variables del sistema
ulimit -a                              # Límites del sistema para el usuario
ulimit -n 65535                        # Cambiar límite de archivos abiertos
sysctl -a                              # Parámetros del kernel
sysctl net.ipv4.ip_forward             # Ver un parámetro específico
sudo sysctl -w net.ipv4.ip_forward=1   # Cambiar parámetro
```

---

## 23. Tabla de Comandos Esenciales

| Comando | Función |
|---------|---------|
| `pwd` | Directorio actual |
| `ls -la` | Listar con detalles y ocultos |
| `cd -` | Volver al directorio anterior |
| `find . -name "*.txt"` | Buscar archivos |
| `grep -r "texto" .` | Buscar texto en archivos |
| `cat archivo | grep -v "^#"` | Ver archivo sin comentarios |
| `sort \| uniq -c \| sort -rn` | Contar y ordenar frecuencias |
| `tail -f /var/log/syslog` | Seguir log en tiempo real |
| `ps aux \| grep proceso` | Buscar proceso |
| `kill -9 PID` | Matar proceso por fuerza |
| `ss -tulpn` | Ver puertos abiertos |
| `df -h` | Espacio en disco |
| `du -sh *` | Tamaño de archivos/carpetas |
| `free -h` | Uso de RAM |
| `history \| grep cmd` | Buscar en historial |
| `Ctrl+R` | Búsqueda en historial |
| `!!` | Repetir último comando |
| `sudo !!` | Repetir con sudo |
| `comando > archivo 2>&1` | Redirigir todo a archivo |
| `comando &` | Ejecutar en background |
| `nohup comando &` | Ejecutar persistente |
| `watch -n 2 comando` | Ejecutar comando cada 2 segundos |
| `time comando` | Medir tiempo de ejecución |
| `which comando` | Ruta de un ejecutable |
| `type comando` | Tipo de comando |
| `file archivo` | Tipo de archivo |
| `stat archivo` | Info completa del archivo |
| `chmod +x script.sh` | Hacer ejecutable |
| `diff archivo1 archivo2` | Comparar archivos |
| `xargs` | Pasar output como argumentos |
| `tee archivo.txt` | Guardar y mostrar a la vez |

---

## 24. Tips y Productividad Avanzada
```bash
# Ejecutar múltiples comandos
cmd1; cmd2; cmd3                       # Siempre ejecuta todos
cmd1 && cmd2                           # cmd2 solo si cmd1 tiene éxito
cmd1 || cmd2                           # cmd2 solo si cmd1 falla
(cmd1; cmd2; cmd3)                     # Subshell: no afecta env actual

# Tiempo y medición
time comando                           # Medir tiempo de ejecución
watch -n 1 "ss -tulpn"                 # Actualizar cada 1 segundo
watch -d -n 2 "df -h"                  # -d resalta cambios

# Utilidades varias
yes                                    # Output infinito de "y"
yes | apt install paquete              # Confirmar todo automáticamente
seq 1 10                               # Secuencia de números
seq 1 2 10                             # Con paso de 2
printf "%-10s %5d\n" "texto" 42        # Output formateado
column -t archivo.txt                  # Alinear columnas
nl archivo.txt                         # Numerar líneas
rev archivo.txt                        # Invertir cada línea
paste archivo1.txt archivo2.txt        # Unir archivos columna a columna
join archivo1.txt archivo2.txt         # Join de archivos por campo común
comm archivo1.txt archivo2.txt         # Comparar archivos ordenados
diff archivo1.txt archivo2.txt         # Diferencias entre archivos
sdiff archivo1.txt archivo2.txt        # Diferencias lado a lado

# Generación de datos
/dev/urandom                           # Fuente de datos aleatorios
/dev/null                              # Agujero negro (descartar datos)
/dev/zero                              # Fuente de ceros
dd if=/dev/urandom bs=1M count=10 of=random.bin  # Generar 10MB aleatorios
dd if=/dev/zero bs=1M count=100 of=cero.bin       # Generar 100MB de ceros

# Base64
base64 archivo.txt                     # Codificar
base64 -d archivo_encoded.txt          # Decodificar
echo "texto" | base64
echo "dGV4dG8=" | base64 -d

# Hash
md5sum archivo.txt
sha1sum archivo.txt
sha256sum archivo.txt
echo -n "texto" | sha256sum            # Hash de string
sha256sum archivo.txt > checksums.txt  # Guardar checksum
sha256sum -c checksums.txt             # Verificar checksum
```
