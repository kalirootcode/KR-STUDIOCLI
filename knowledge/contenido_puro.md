# Contenido Puro - Terminal y Herramientas Gráficas

## Concepto

El contenido puro se enfoca en **grabaciones de terminal** y **herramientas con interfaz gráfica** sin necesidad de videos externos o animaciones. Es ideal para:

- Herramientas con UI gráfica (Wireshark, Burp Suite, Caido, Hydra, etc.)
- Secciones de Kali Linux
- Páginas web interactivas
- Demostraciones prácticas de cybersecurity

La clave es que el presentador narra mientras el espectador ve la herramienta en acción, creando una experiencia inmersiva tipo "hands-on".

---

## Estructura de un Video Puro

### 1. INTRO HOOK (0:00 - 0:15)
```json
{
  "tipo": "narracion",
  "voz": "HOOK - frase impactante sobre la herramienta/tema",
  "visual": "PANTALLA DE LA HERRAMIENTA / TERMINAL",
  "timestamp": "0:00",
  "indicador": "MOSTRAR HERRAMIENTA EN PANTALLA"
}
```

### 2. INTRODUCCIÓN RÁPIDA (0:15 - 0:45)
```json
{
  "tipo": "narracion",
  "voz": "Hoy vamos a explorar [NOMBRE DE HERRAMIENTA], una herramienta esencial para [CASO DE USO]. Les voy a mostrar cómo instalarla y los features principales.",
  "visual": "PANTALLA DE LA HERRAMIENTA",
  "timestamp": "0:15"
}
```

### 3. INSTALACIÓN (0:45 - 1:30)
```json
{
  "tipo": "ejecucion",
  "comando_visual": "sudo apt install [paquete] -y",
  "voz": "Primero instalamos la herramienta. En Kali Linux ya viene preinstalada, pero les muestro cómo hacerlo en otras distribuciones.",
  "visual": "TERMINAL CON INSTALACIÓN",
  "timestamp": "0:45"
}
```

### 4. LANZAMIENTO DE LA HERRAMIENTA (1:30 - 2:00)
```json
{
  "tipo": "ejecucion",
  "comando_visual": "[comando de lanzamiento]",
  "voz": "Ahora lanzamos la herramienta. Aquí podemos ver la interfaz principal.",
  "visual": "HERRAMIENTA CON INTERFAZ GRÁFICA",
  "timestamp": "1:30",
  "indicador": "CAMBIAR A [NOMBRE DE HERRAMIENTA]"
}
```

### 5. EXPLORACIÓN DE LA UI (2:00 - 3:00)
```json
{
  "tipo": "narracion",
  "voz": "Veamos las secciones principales. Aquí tenemos el menú de configuración, aquí los resultados del scan, y aquí las opciones avanzadas.",
  "visual": "HERRAMIENTA CON PUNTOS DESTACADOS",
  "timestamp": "2:00"
}
```

### 6. DEMOSTRACIÓN PRÁCTICA (3:00 - 5:30)
```json
{
  "tipo": "ejecucion",
  "comando_visual": "[comandos específicos]",
  "voz": "Ahora viene lo interesante. Vamos a probar la herramienta contra un objetivo de práctica.",
  "visual": "HERRAMIENTA EN ACCIÓN",
  "timestamp": "3:00"
}
```

### 7. ANÁLISIS DE RESULTADOS (5:30 - 6:30)
```json
{
  "tipo": "narracion",
  "voz": "Excelente. Los resultados muestran [INTERPRETACIÓN]. Esta información es crucial para [CASO DE USO].",
  "visual": "RESULTADOS DESTACADOS",
  "timestamp": "5:30"
}
```

### 8. CIERRE Y CTA (6:30 - 7:00)
```json
{
  "tipo": "narracion",
  "voz": "Eso es todo. Ahora tienen una nueva herramienta en su arsenal. Recuerden practicar en laboratorios legales. Nos vemos en el próximo video.",
  "visual": "TERMINAL / HERRAMIENTA CERRADA",
  "timestamp": "6:30"
}
```

---

## Herramientas Ideales para Contenido Puro

### Herramientas de Terminal Puras
```
- nmap
- sqlmap
- dirb/gobuster
- hydra
- john
- hashcat
- netcat
- masscan
- nikto
- exploitdb
- metasploit
- responder
```

### Herramientas con Interfaz Gráfica
```
- Wireshark (capturas de red)
- Burp Suite (pentesting web)
- Caido (alternativa a Burp)
- Ettercap (MITM)
- Aircrack-ng (wifi)
- Hash-Identifier
- OSINT Framework (web)
- SpiderFoot (reconocimiento)
```

### Secciones de Kali Linux
```
- Top 10 herramientas
- Menú de aplicaciones
- Secciones de privilege escalation
- Análisis forense
- Reverse engineering
```

### Páginas Web para Demo
```
- DVWA (laboratorio vulnerable)
- OWASP WebGoat
- HackTheBox
- TryHackMe
- PortSwigger Web Security Academy
```

---

## Tipos de Videos Puros

### A. Tutorial de Herramienta Completo
1. Introducción → Instalación → UI → Demo → Cierre
2. Duración: 5-15 minutos
3. Ideal para: herramientas nuevas o poco conocidas

### B. Quick Demo (Short)
1. Hook → Demo directa → Cierre
2. Duración: 1-3 minutos
3. Ideal para: tips rápidos, one-liners

### C. Comparativa
1. Intro → Herramienta A → Herramienta B → Comparación
2. Duración: 10-20 minutos
3. Ideal para: Burp vs Caido, Hydra vs Medusa

### D. Walkthrough de Lab
1. Objetivo → Recon → Explotación → Post-explotación → Cierre
2. Duración: 15-45 minutos
3. Ideal para: HTB, TryHackMe, CTFs

---

## Formato de Escenas para Herramientas Gráficas

### Cambio a Herramienta GUI
```json
{
  "tipo": "narracion",
  "voz": "Ahora abrimos Wireshark para capturar el tráfico.",
  "visual": "CAMBIAR A WIRESHARK",
  "timestamp": "1:30",
  "indicador": "CAMBIAR A WIRESHARK"
}
```

### Navegación en GUI
```json
{
  "tipo": "narracion",
  "voz": "Aquí en el menú superior encontramos las opciones de captura. Seleccionamos la interfaz de red.",
  "visual": "WIRESHARK - MENÚ SUPERIOR DESTACADO",
  "timestamp": "2:00"
}
```

### Resultado en GUI
```json
{
  "tipo": "narracion",
  "voz": "Perfecto, ya tenemos los paquetes capturados. Como ven, hay tráfico HTTP sin cifrar.",
  "visual": "WIRESHARK - PAQUETES CAPTURADOS",
  "timestamp": "3:30"
}
```

### Transición Terminal → GUI
```json
{
  "tipo": "narracion",
  "voz": "Ahora vamos a usar Wireshark para analizar los resultados del scan.",
  "visual": "CAMBIO DE VENTANA",
  "timestamp": "4:00",
  "indicador": "CAMBIAR A WIRESHARK"
}
```

### Transición GUI → Terminal
```json
{
  "tipo": "narracion",
  "voz": "Ahora exportamos los datos y los procesamos con un script en Python.",
  "visual": "TRANSICIÓN A TERMINAL",
  "timestamp": "5:00",
  "indicador": "TRANSICIÓN A TERMINAL"
}
```

---

## Reglas para Contenido Puro

### Narración:
1. **Explica cada paso** - el espectador solo ve la pantalla
2. **Describe los resultados** - "aquí podemos ver que...", "esto significa que..."
3. **Contexto técnico** - menciona puertos, protocolos, vulnerabilidades
4. **Tiempo de reacción** - deja 2-3 segundos después de resultados importantes
5. **Preaviso de comandos** - "vamos a ejecutar...", "ahora ejecuto..."

### Ritmo Visual:
- **Comandos**: 5-15 segundos por comando (dependiendo de output)
- **Explicaciones**: 10-20 segundos
- **Resultados extensos**: usar "pausa" para que el espectador lea

### Transiciones entre Herramientas:
```
INDICADORES DE TRANSICIÓN:
- "CAMBIAR A [NOMBRE_HERRAMIENTA]"
- "VOLVER A TERMINAL"
- "TRANSICIÓN A [PROGRAMA]"
- "MINIMIZAR [HERRAMIENTA]"
- "NUEVA PESTAÑA EN NAVEGADOR"
```

---

## Ejemplo Completo: Wireshark Basics

```json
[
  {
    "tipo": "narracion",
    "voz": "¿Sabías que cada vez que te conectas a una red WiFi sin contraseña, alguien puede ver TODO lo que haces? Te voy a mostrar cómo funciona.",
    "visual": "WIRESHARK ABIERTO",
    "timestamp": "0:00",
    "indicador": "CAMBIAR A WIRESHARK"
  },
  {
    "tipo": "narracion",
    "voz": "Esto es Wireshark, el analizador de protocolos más potente del mundo. Con él podemos ver todo el tráfico de red en tiempo real.",
    "visual": "WIRESHARK - INTERFAZ PRINCIPAL",
    "timestamp": "0:20"
  },
  {
    "tipo": "narracion",
    "voz": "Antes de capturar, seleccionamos la interfaz de red. En mi caso uso wlan0 que es mi adaptador WiFi.",
    "visual": "WIRESHARK - LISTA DE INTERFACES",
    "timestamp": "0:50",
    "indicador": "SELECCIONAR INTERFAZ WI-FI"
  },
  {
    "tipo": "ejecucion",
    "comando_visual": "[Click en botón Start]",
    "voz": "Damos click en Start y Wireshark comienza a capturar todos los paquetes que pasan por la red.",
    "visual": "WIRESHARK - CAPTURA EN PROGRESO",
    "timestamp": "1:20"
  },
  {
    "tipo": "pausa",
    "espera": 5.0,
    "voz": "Déjenme navegar a una página web para generar tráfico.",
    "visual": "NAVEGADOR - CARGANDO PÁGINA",
    "timestamp": "1:25"
  },
  {
    "tipo": "narracion",
    "voz": "Aquí está el resultado. Cada línea es un paquete capturado. Como ven, hay tráfico HTTP sin cifrar visible para cualquiera en la red.",
    "visual": "WIRESHARK - LISTA DE PAQUETES",
    "timestamp": "1:30"
  },
  {
    "tipo": "narracion",
    "voz": "Hagamos click en un paquete HTTP para ver su contenido. Aquí podemos ver las cabeceras, la URL solicitada, incluso cookies si las hay.",
    "visual": "WIRESHARK - DETALLE DE PAQUETE HTTP",
    "timestamp": "2:00"
  },
  {
    "tipo": "narracion",
    "voz": "Por eso es tan importante usar HTTPS. Con HTTPS todo este tráfico estaría cifrado y sería ilegible para un atacante.",
    "visual": "WIRESHARK - PAQUETES HTTPS CIFRADOS",
    "timestamp": "2:45"
  },
  {
    "tipo": "narracion",
    "voz": "Eso es Wireshark en acción. Ahora entienden por qué nunca deben conectarse a redes WiFi públicas sin VPN. Nos vemos en el próximo video.",
    "visual": "STOP CAPTURA - CIERRE DE WIRESHARK",
    "timestamp": "3:20"
  }
]
```

---

## Ejemplo: Burp Suite Intruder

```json
[
  {
    "tipo": "narracion",
    "voz": "Burp Suite Intruder es como un balas locas para web hacking. Envía cientos de requests automatizadas para encontrar parámetros vulnerables.",
    "visual": "BURP SUITE - PESTAÑA INTRUDER",
    "timestamp": "0:00",
    "indicador": "CAMBIAR A BURP SUITE"
  },
  {
    "tipo": "narracion",
    "voz": "Primero interceptamos una request desde el navegador. Aquí la tenemos en la pestana Proxy.",
    "visual": "BURP SUITE - PROXY INTERCEPT",
    "timestamp": "0:30"
  },
  {
    "tipo": "ejecucion",
    "comando_visual": "Click en 'Send to Intruder' (Ctrl+I)",
    "voz": "Enviamos la request a Intruder con Ctrl+I o el botón correspondiente.",
    "visual": "BURP SUITE - SEND TO INTRUDER",
    "timestamp": "1:00"
  },
  {
    "tipo": "narracion",
    "voz": "En la pestana Intruder, en la sección Positions, marcamos los puntos donde queremos insertar payloads. Burp ya detecta algunos automáticamente.",
    "visual": "BURP SUITE - INTRUDER POSITIONS",
    "timestamp": "1:30"
  },
  {
    "tipo": "narracion",
    "voz": "En la sección Payloads cargamos una lista de payloads. Voy a usar una lista de passwords comunes para este ataque de fuerza bruta.",
    "visual": "BURP SUITE - PAYLOADS CONFIG",
    "timestamp": "2:00"
  },
  {
    "tipo": "ejecucion",
    "comando_visual": "Click en 'Start Attack'",
    "voz": "Iniciamos el ataque. Burp comenzará a enviar requests con cada payload.",
    "visual": "BURP SUITE - ATAQUE EN PROGRESO",
    "timestamp": "2:30"
  },
  {
    "tipo": "narracion",
    "voz": "Aquí podemos ver los resultados en tiempo real. Cada request muestra su longitud de respuesta y código de estado. Una respuesta anomalamente larga puede indicar éxito.",
    "visual": "BURP SUITE - RESULTADOS DEL ATAQUE",
    "timestamp": "3:00"
  },
  {
    "tipo": "narracion",
    "voz": "Al finalizar, ordenamos por longitud de respuesta. Esta request número 47 tiene una longitud diferente a las demás, lo que sugiere que el login fue exitoso.",
    "visual": "BURP SUITE - RESULTADOS ORDENADOS",
    "timestamp": "4:00"
  },
  {
    "tipo": "narracion",
    "voz": "Y eso es cómo un atacante podría usar Burp Intruder para bruteforcear un login. Usa autenticación fuerte y rate limiting para prevenir estos ataques.",
    "visual": "BURP SUITE - CIERRE",
    "timestamp": "4:45"
  }
]
```

---

## Palabras Clave para Detectar Contenido Puro

```
INDICADORES EN EL PROMPT:
- "tutorial de [herramienta]"
- "how to use [herramienta]"
- "prueba [herramienta]"
- "demo de [herramienta]"
- "burp suite"
- "wireshark"
- "kali linux"
- "terminal"
- "grabación de pantalla"
- "captura de red"
- "pentest con [herramienta]"
```

---

## Best Practices para Contenido Puro

1. **Claridad del audio** - el espectador depende completamente de tu narración
2. **Visibilidad** - asegúrate de que el texto sea legible en la grabación
3. **Ritmo** - no vayas muy rápido, da tiempo a que el espectador procese
4. **Contexto** - siempre explica qué estás haciendo y por qué
5. **Herramientas visuales** - usa highlight/zoom para destacar elementos importantes
6. **Resultados claros** - cuando muestres resultados, interprétalos para el espectador
