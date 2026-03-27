# Contenido Mixto - Videos con Elementos Externos y Terminal

## Concepto

El contenido mixto combina **videos externos** (animaciones de IA, páginas web, repositorios) con **grabaciones de terminal**. La idea es crear videos dinámicos que mantengan la atención del espectador alternando entre diferentes tipos de contenido visual.

---

## Estructura de un Video Mixto

### 1. INTRO hook (0:00 - 0:10)
```json
{
  "tipo": "narracion",
  "voz": "HOOK del video - frase impactante sobre el tema",
  "visual": "SLIDE/TÍTULO ANIMADO",
  "timestamp": "0:00"
}
```

### 2. CONTEXTO (0:10 - 0:30)
```json
{
  "tipo": "narracion",
  "voz": "Contexto sobre el tema y por qué es importante",
  "visual": "ANIMACIÓN DE IA o SLIDE EXPLICATIVO",
  "timestamp": "0:10",
  "indicador": "MOSTRAR ANIMACIÓN DE IA EXPLICATIVA"
}
```

### 3. PRESENTACIÓN DEL REPOSITORIO/PÁGINA (0:30 - 1:00)
```json
{
  "tipo": "narracion",
  "voz": "Esta es la página oficial del repositorio [NOMBRE]. Aquí pueden chequear sus funciones, cómo está estructurado, y conseguir el enlace para clonarlo.",
  "visual": "PÁGINA DEL REPOSITORIO EN NAVEGADOR",
  "timestamp": "0:30",
  "indicador": "ABRIR [URL] EN NAVEGADOR"
}
```

### 4. TRANSICIÓN A LA TERMINAL (1:00 - 1:10)
```json
{
  "tipo": "narracion",
  "voz": "Procedamos a clonarlo y ejecutarlo. Aquí debemos pasar a la terminal mostrando cómo se clona, con explicaciones después de cada paso.",
  "visual": "TRANSICIÓN ANIMADA A TERMINAL",
  "timestamp": "1:00",
  "indicador": "TRANSICIÓN A TERMINAL"
}
```

### 5. CLONACIÓN DEL REPOSITORIO (1:10 - 1:30)
```json
{
  "tipo": "ejecucion",
  "comando_visual": "git clone https://github.com/USUARIO/REPO.git",
  "voz": "Primero clonamos el repositorio. Esto nos dará acceso a todo el código fuente.",
  "visual": "TERMINAL CON COMANDO DE CLONACIÓN",
  "timestamp": "1:10"
}
```

### 6. ANIMACIÓN EXPLICATIVA (1:30 - 2:00)
```json
{
  "tipo": "narracion",
  "voz": "Antes de continuar, les explico con un ejemplo visual: un servidor es como un edificio, y los puestos del servidor son las puertas. Cada puerta permite o denied el acceso, exactamente como un firewall.",
  "visual": "ANIMACIÓN DE IA - SERVIDOR COMO EDIFICIO",
  "timestamp": "1:30",
  "indicador": "MOSTRAR ANIMACIÓN DE IA EXPLICATIVA"
}
```

### 7. NAVEGACIÓN Y ESTRUCTURA (2:00 - 2:30)
```json
{
  "tipo": "ejecucion",
  "comando_visual": "cd REPO && ls -la",
  "voz": "Ahora navegamos a la carpeta del proyecto y vemos su estructura. Aquí está el README con la documentación.",
  "visual": "TERMINAL MOSTRANDO ESTRUCTURA",
  "timestamp": "2:00"
}
```

### 8. DEMOSTRACIÓN DEL PROGRAMA (2:30 - 4:00)
```json
{
  "tipo": "ejecucion",
  "comando_visual": "python3 programa.py --help",
  "voz": "Veamos las opciones disponibles. Esta herramienta tiene múltiples modos de operación que vamos a explorar.",
  "visual": "TERMINAL CON HELP DEL PROGRAMA",
  "timestamp": "2:30"
}
```

### 9. EJECUCIÓN PRÁCTICA (4:00 - 5:00)
```json
{
  "tipo": "ejecucion",
  "comando_visual": "python3 programa.py --target URL --scan quick",
  "voz": "Ahora ejecutamos el scan. Como pueden ver, los resultados aparecen en tiempo real.",
  "visual": "TERMINAL CON SCAN EN PROGRESO",
  "timestamp": "4:00"
}
```

### 10. CIERRE Y CTA (5:00 - 5:30)
```json
{
  "tipo": "narracion",
  "voz": "Eso es todo por hoy. Recuerden practicar en laboratorios seguros. Si les gustó, like y suscripción para más contenido.",
  "visual": "SLIDE DE CIERRE CON CTA",
  "timestamp": "5:00"
}
```

---

## Tipos de Videos Mixtos

### A. Repositorio + Terminal
- Mostrar repo → Clonar → Ejecutar → Explicar
- Ideal para: herramientas de GitHub, scripts personalizados

### B. Página Web + Terminal
- Navegar web → Explicar función → Demo en terminal
- Ideal para: APIs, servicios online, documentación

### C. Animación IA + Terminal
- Animación explicativa → Código/Terminal
- Ideal para: conceptos complejos de cybersecurity

### D. Video Tutorial Estándar
- Introducción → Demo → Ejemplos → Cierre
- Mezcla: slides + terminal + animations

---

## Indicadores para Videos Mixtos

```
INDICADORES DE VISUAL:
- "ABRIR [URL] EN NAVEGADOR"
- "MOSTRAR ANIMACIÓN DE IA EXPLICATIVA"
- "TRANSICIÓN A TERMINAL"
- "TRANSICIÓN A NAVEGADOR"
- "GRABAR [PROGRAMA] EN ACCIÓN"
- "MOSTRAR [PÁGINA/REPO] EN PANTALLA"
- "PAUSA PARA VER ANIMACIÓN"
- "CAMBIAR A [VENTANA/PROGRAMA]"
```

---

## Reglas para la Narración

### En contenido mixto:
1. **No repitas lo que se ve** - el visual ya muestra, enfócate en explicar el "por qué"
2. **Conecta elementos** -ربط entre la animación y el comando
3. **Da tiempo** - 2-3 segundos de pausa después de animaciones importantes
4. **Usa analogías** - "es como...", "imaginen que...", "pensemos en..."
5. **Transiciones fluidas** - siempre explica qué viene después

### Pronunciación para TTS:
- Comandos: "enemap" no "n-map"
- Flags: "menos ese" no "dash S"
- URLs: "github punto com" no "punto punto"
- Números: "cinco" no "5"

---

## Ejemplo Completo: Video sobre Nmap

```json
[
  {
    "tipo": "narracion",
    "voz": "¿Alguna vez te has preguntado cómo los hackers encuentran vulnerabilidades en segundos? Hoy te lo muestro.",
    "visual": "TÍTULO ANIMADO - ESCANEO DE RED",
    "timestamp": "0:00"
  },
  {
    "tipo": "narracion",
    "voz": "Esta es la página oficial de Nmap, la herramienta de escaneo más famosa del mundo. Aquí puedes ver la documentación y descargarla.",
    "visual": "PÁGINA DE NMAP EN NAVEGADOR",
    "timestamp": "0:15",
    "indicador": "ABRIR https://nmap.org EN NAVEGADOR"
  },
  {
    "tipo": "narracion",
    "voz": "Un puerto abierto es como una puerta abierta en un edificio. Un hacker busca esas puertas para encontrar vulnerabilidades.",
    "visual": "ANIMACIÓN IA - EDIFICIO CON PUERTAS",
    "timestamp": "0:40",
    "indicador": "MOSTRAR ANIMACIÓN DE IA EXPLICATIVA"
  },
  {
    "tipo": "narracion",
    "voz": "Vamos a la terminal. Les voy a mostrar cómo usar Nmap para encontrar esas puertas abiertas.",
    "visual": "TRANSICIÓN A TERMINAL",
    "timestamp": "1:10",
    "indicador": "TRANSICIÓN A TERMINAL"
  },
  {
    "tipo": "ejecucion",
    "comando_visual": "nmap -sV scanme.nmap.org",
    "voz": "Con este comando le decimos a Nmap que escanee scanme punto nmap punto org y nos muestre las versiones de los servicios.",
    "visual": "TERMINAL CON ESCANEO EN PROGRESO",
    "timestamp": "1:20"
  },
  {
    "tipo": "narracion",
    "voz": "Impresionante, ¿verdad? En segundos, Nmap encontró 6 puertos abiertos y nos dijo qué servicio corre en cada uno. El puerto 22 tiene SSH, el 80 tiene HTTP.",
    "visual": "RESULTADOS DEL ESCANEO",
    "timestamp": "2:30"
  },
  {
    "tipo": "narracion",
    "voz": "Ahora ya saben cómo un hacker encuentra las puertas abiertas de un sistema. Recuerden: con gran poder viene gran responsabilidad. Practiquen en laboratorios seguros.",
    "visual": "SLIDE DE CIERRE",
    "timestamp": "3:00"
  }
]
```

---

## Frecuencia de Cambios Visuales

Para mantener la atención (video de 5 min):
- **Cada 15-20 segundos**: cambio de visual
- **Alternar**: terminal → animación → navegador → terminal
- **Máximo 45 segundos** en terminal sin cambio visual
- **Mínimo 5 segundos** para animaciones/visuals externos

---

## Palabras Clave para Detectar Videos Mixtos

```
INDICADORES EN EL PROMPT:
- "video sobre [herramienta] mostrando el repo"
- "explica [concepto] con animación"
- "usando [URL/repo]"
- "clonar y ejecutar"
- "mostrar cómo se instala"
- "prueba [herramienta] en terminal"
- "tutorial de [herramienta]"
```
