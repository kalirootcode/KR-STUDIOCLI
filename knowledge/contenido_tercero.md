# Contenido de Tercero - Guiones para Videos de Herramientas y Recursos Externos

## Concepto Fundamental

Cuando el usuario proporciona un enlace, nombre de repositorio, o referencia a contenido externo, el guion debe estructurarse para que el presentador narre mientras el espectador ve el contenido de terceros en pantalla.

---

## Tipos de Contenido de Tercero

### 1. Repositorios de GitHub/GitLab
```
- Mostrar la página principal del repo
- Explicar qué hace la herramienta
- Mostrar el proceso de instalación
- Demostrar el uso básico
- Casos de uso avanzados
```

### 2. Páginas Web / Servicios Online
```
- Introducir la herramienta/servicio
- Mostrar la interfaz web
- Explicar funcionalidades
- Demo práctica en la web
- Conclusión y próximos pasos
```

### 3. Videos Externos (YouTube, etc.)
```
- Introducir el tema
- Mencionar el video externo
- Explicar qué se verá
- Reflexión y análisis post-video
- Recursos adicionales
```

### 4. Programas / Aplicaciones
```
- Presentar el programa
- Mostrar interfaz y características
- Demo de uso práctico
- Comparación con alternativas (si aplica)
- Conclusión
```

---

## Estructura de Escenas para Contenido de Tercero

### Escena de INTRODUCCIÓN (contenido externo)
```json
{
  "tipo": "narracion",
  "voz": "Hoy vamos a explorar [NOMBRE DE LA HERRAMIENTA], una solución increíble que está revolucionando [ÁREA]. Pero antes de meternos en código, quiero que vean cómo luce y qué ofrece oficialmente.",
  "visual": "LOGO DE LA HERRAMIENTA / PÁGINA PRINCIPAL DEL REPO",
  "timestamp": "0:00"
}
```

### Escena de TRANSICIÓN (indicar que viene contenido externo)
```json
{
  "tipo": "narracion",
  "voz": "Aquí pueden ver la página oficial del proyecto. Tómense un momento para explorar las opciones que ofrece.",
  "visual": "INDICADOR DE CARGA DE PÁGINA / TRANSICIÓN",
  "timestamp": "0:15",
  "indicador": "MOSTRAR CONTENIDO EXTERNO EN PANTALLA"
}
```

### Escena de INSTALACIÓN
```json
{
  "tipo": "narracion",
  "voz": "Ahora vamos a instalar la herramienta. Sigan los pasos que aparecen en pantalla.",
  "visual": "COMANDOS DE INSTALACIÓN EN TERMINAL",
  "timestamp": "1:30",
  "indicador": "GRABAR TERMINAL CON COMANDOS"
}
```

### Escena de DEMOSTRACIÓN
```json
{
  "tipo": "narracion",
  "voz": "Perfecto, ya tenemos [HERRAMIENTA] instalada. Ahora voy a mostrarles cómo usarla para [CASO DE USO]. Prueben conmigo en su máquina.",
  "visual": "DEMOSTRACIÓN EN VIVO DE LA HERRAMIENTA",
  "timestamp": "2:00",
  "indicador": "GRABAR HERRAMIENTA EN ACCIÓN"
}
```

### Escena de ANÁLISIS POST-CONTENIDO
```json
{
  "tipo": "narracion",
  "voz": "Eso fue lo que mostró [NOMBRE DEL RECURSO]. Ahora, basado en mi experiencia, les explico los puntos clave y cómo aplicarlo en su trabajo diario.",
  "visual": "PANTALLA CON NOTAS / PUNTOS CLAVE",
  "timestamp": "5:00",
  "indicador": "VOLVER A PANTALLA CONCLUSIONS"
}
```

---

## Formato de Referencia para el Usuario

Cuando el usuario menciona contenido externo, debe seguir este formato:

```
COMANDO/PROMPT A LA IA:
"Video sobre [TEMA] usando [ENLACE/REPO/HERRAMIENTA]"

Ejemplo:
"Video sobre SQLMap usando https://github.com/sqlmapproject/sqlmap"
"Video sobre Burp Suite mostrando su interfaz desde https://portswigger.net/burp"
```

---

## Instrucciones para la IA

### Detectar Contenido de Tercero
```
La IA debe detectar cuando el usuario menciona:
1. URLs (github.com, gitlab.com, etc.)
2. Nombres de herramientas/programas específicos
3. Referencias a contenido externo ("el video de X", "la página de Y")
```

### Generar Guion con Indicadores
```
Para cada referencia externa, la IA debe generar:
1. Escena introductoria al recurso
2. Escena de transición indicando "muestren X"
3. Narración mientras se muestra el contenido
4. Análisis post-visualización
5. Conexión con el tema principal
```

---

## Ejemplo Completo de Guion con Contenido de Tercero

### Prompt del Usuario:
```
"Video de 5 minutos sobre SQL Injection usando sqlmap, mostraremos el repo de github y la herramienta en acción"
```

### Guion Generado:
```json
[
  {
    "tipo": "narracion",
    "voz": "Bienvenidos a un nuevo video. Hoy vamos a hablar de SQL Injection, una de las vulnerabilidades más comunes en aplicaciones web. Y para demostrar cómo funciona en la práctica, vamos a usar sqlmap, una herramienta automática de detección y explotación.",
    "visual": "SLIDE INTRO / TÍTULO DEL VIDEO",
    "timestamp": "0:00"
  },
  {
    "tipo": "narracion",
    "voz": "Primero, quiero que vean el repositorio oficial de sqlmap en GitHub. Aquí pueden encontrar toda la documentación, ejemplos y la última versión disponible.",
    "visual": "PANTALLA NEGRA CON INDICADOR",
    "timestamp": "0:20",
    "indicador": "ABRIR https://github.com/sqlmapproject/sqlmap EN NAVEGADOR"
  },
  {
    "tipo": "pausa",
    "espera": 3.0,
    "visual": "REPO DE SQLMAP EN GITHUB",
    "timestamp": "0:23"
  },
  {
    "tipo": "narracion",
    "voz": "Como ven, el repo tiene más de 30 mil estrellas, lo que nos indica que es una herramienta muy popular y bien mantenida. La documentación es bastante completa. Tómense un momento para explorarla.",
    "visual": "SCROLL POR LA PÁGINA DEL REPO",
    "timestamp": "0:26"
  },
  {
    "tipo": "narracion",
    "voz": "Ahora vamos a la acción. Vamos a instalar sqlmap en nuestra máquina y probarlo contra un objetivo de práctica. Abran su terminal y sigan los pasos.",
    "visual": "PANTALLA NEGRA CON INDICADOR",
    "timestamp": "1:00",
    "indicador": "TRANSICIÓN A TERMINAL"
  },
  {
    "tipo": "ejecucion",
    "comando_visual": "git clone https://github.com/sqlmapproject/sqlmap.git",
    "voz": "Primero clonamos el repositorio. Esto nos dará la última versión de la herramienta.",
    "visual": "TERMINAL CON COMANDO DE CLONACIÓN",
    "timestamp": "1:05"
  },
  {
    "tipo": "ejecucion",
    "comando_visual": "cd sqlmap && python sqlmap.py --version",
    "voz": "Una vez descargado, navegamos a la carpeta y verificamos que esté instalado correctamente ejecutando el comando de versión.",
    "visual": "TERMINAL MOSTRANDO VERSIÓN",
    "timestamp": "1:25"
  },
  {
    "tipo": "narracion",
    "voz": "Perfecto, sqlmap está listo. Ahora vamos a probarlo contra un objetivo de práctica. Para esto usaremos un laboratorio vulnerable que pueden descargar gratuitamente.",
    "visual": "PANTALLA NEGRA CON INDICADOR",
    "timestamp": "2:00",
    "indicador": "MOSTRAR DVWA O LABORATORIO DE PRÁCTICA"
  },
  {
    "tipo": "ejecucion",
    "comando_visual": "python sqlmap.py -u 'http://localhost/DVWA/vulnerabilities/sqli/?id=1' --dbs",
    "voz": "Con este comando le decimos a sqlmap que analice la URL que le pasamos. El flag --dbs le indica que enumere las bases de datos disponibles. Como pueden ver, sqlmap empieza a hacer magia.",
    "visual": "TERMINAL CON SQLMAP EN ACCIÓN",
    "timestamp": "2:15"
  },
  {
    "tipo": "narracion",
    "voz": "Impresionante, ¿verdad? En cuestión de segundos, sqlmap detectó que el parámetro ID es vulnerable a SQL Injection y nos mostró las bases de datos del sistema. Esto es exactamente lo que hace sqlmap: automatiza el proceso de detección y explotación.",
    "visual": "RESULTADOS DE SQLMAP EN PANTALLA",
    "timestamp": "3:30"
  },
  {
    "tipo": "narracion",
    "voz": "Ahora que entienden cómo funciona sqlmap, quiero que reflexionen sobre la importancia de esta herramienta para los profesionales de seguridad. Nos ahorra horas de trabajo manual y nos ayuda a encontrar vulnerabilidades que podrían pasar desapercibidas.",
    "visual": "SLIDE CON PUNTOS CLAVE",
    "timestamp": "4:15"
  },
  {
    "tipo": "narracion",
    "voz": "Eso es todo por hoy. Recuerden practicar siempre en laboratorios de prueba, nunca en sistemas sin autorización. Si les gustó el video, dele like y suscríbanse para más contenido de ciberseguridad. Nos vemos en el próximo video.",
    "visual": "SLIDE DE CIERRE / CTA",
    "timestamp": "4:45"
  }
]
```

---

## Palabras Clave para Detectar Contenido de Tercero

```
INDICADORES EN EL PROMPT:
- "usando [herramienta/enlace]"
- "mostrando [recurso/página]"
- "con [nombre de programa]"
- "desde [URL/enlace]"
- "basado en [video/artículo]"
- "el repo de [nombre]"
- "la herramienta [nombre]"
- "demostrar [herramienta]"
```

---

## Indicadores Visuales para el Editor/KenLive

### En el campo "indicador" de cada escena:

```
INDICADORES PARA CONTENIDO EXTERNO:
- "ABRIR [URL] EN NAVEGADOR"
- "MOSTRAR [NOMBRE DE HERRAMIENTA/PÁGINA]"
- "GRABAR [PROGRAMA/HERRAMIENTA] EN ACCIÓN"
- "TRANSICIÓN A [CONTEXTO]"
- "PAUSA PARA VER [CONTENIDO]"
- "VOLVER A PANTALLA PRINCIPAL"
- "CAMBIAR A [VENTANA/PROGRAMA]"
```

### Ejemplo de escena con indicador:
```json
{
  "tipo": "narracion",
  "voz": "Aquí pueden ver la documentación oficial. Tómense su tiempo para revisarla.",
  "visual": "DOCUMENTACIÓN EN NAVEGADOR",
  "timestamp": "1:30",
  "indicador": "ABRIR https://github.com/sqlmapproject/sqlmap/wiki EN NAVEGADOR"
}
```

---

## Best Practices

1. **Siempre introduce el recurso externo** antes de mostrarlo
2. **Da tiempo al espectador** para que observe el contenido
3. **Explica mientras se muestra** el contenido, no antes ni después
4. **Usa transiciones claras** entre contenido tuyo y externo
5. **Cierra con reflexión** sobre lo que se mostró
6. **Incluye timestamps** para facilitar la edición en post-producción
