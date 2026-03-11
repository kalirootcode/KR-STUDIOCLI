"""
targets_db.py — Base de Datos de Targets Legales + Laboratorios Docker para KR-STUDIO
Incluye selección automática de laboratorio según el tema del video.
"""

import subprocess
import re

# ═══════════════════════════════════════════════════════════════════
#  LABORATORIOS DOCKER LOCALES
#  Estos tienen prioridad ABSOLUTA sobre targets remotos cuando el
#  tema del video involucra explotación, ataques activos o post-explotación.
# ═══════════════════════════════════════════════════════════════════

DOCKER_LABS = {
    # ── METASPLOIT / EXPLOITS CLÁSICOS ─────────────────────────────
    "metasploitable2": {
        "nombre":      "Metasploitable2",
        "contenedor":  "victima-lab",
        "imagen":      "tleemcjr/metasploitable2",
        "ip_cmd":      "docker inspect victima-lab --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'",
        "start_cmd":   "docker start victima-lab",
        "puertos":     {"ftp": 21, "ssh": 22, "telnet": 23, "http": 80, "smb": 445},
        "descripcion": "Máquina vulnerable clásica — vsftpd backdoor, Samba, PostgreSQL, Tomcat",
        "temas": [
            "metasploit", "exploit", "vsftpd", "backdoor", "samba", "smb",
            "ftp", "msfconsole", "payload", "shell", "root", "post-explotacion",
            "privesc", "privilege escalation", "meterpreter", "bind shell",
            "reverse shell", "tomcat", "postgresql", "telnet", "rpc",
        ],
        "herramientas": ["metasploit", "msfconsole", "nmap", "netcat", "hydra"],
        "ejemplo_comandos": [
            "docker start victima-lab",
            "docker inspect victima-lab --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'",
            "nmap -sV -sC [IP_VICTIMA]",
            "msfconsole -q -x 'use exploit/unix/ftp/vsftpd_234_backdoor; set RHOSTS [IP]; run'",
        ],
    },

    # ── WEB HACKING / SQL INJECTION / XSS ──────────────────────────
    "dvwa": {
        "nombre":      "DVWA",
        "contenedor":  "dvwa",
        "imagen":      "vulnerables/web-dvwa",
        "ip_cmd":      "echo 'localhost'",
        "start_cmd":   "docker start dvwa",
        "puertos":     {"http": 8080},
        "url":         "http://localhost:8080",
        "credenciales": "admin / password",
        "descripcion": "Damn Vulnerable Web App — SQLi, XSS, CSRF, File Upload, Brute Force",
        "temas": [
            "sql injection", "sqli", "sqlmap", "xss", "cross-site scripting",
            "csrf", "file upload", "brute force", "dvwa", "php vulnerable",
            "login bypass", "union select", "database dump", "web hacking",
            "inyeccion sql", "robo de cookies", "session hijacking",
            "command injection", "lfi", "local file inclusion",
        ],
        "herramientas": ["sqlmap", "burpsuite", "nikto", "curl", "hydra", "firefox"],
        "ejemplo_comandos": [
            "docker start dvwa",
            "sqlmap -u 'http://localhost:8080/vulnerabilities/sqli/?id=1&Submit=Submit' --cookie='PHPSESSID=XXX;security=low' --dbs",
            "nikto -h http://localhost:8080",
        ],
    },

    # ── JWT / OWASP MODERN WEB ──────────────────────────────────────
    "juiceshop": {
        "nombre":      "OWASP Juice Shop",
        "contenedor":  "tender_blackwell",
        "imagen":      "bkimminich/juice-shop",
        "ip_cmd":      "echo 'localhost'",
        "start_cmd":   "echo 'Juice Shop ya esta corriendo en puerto 3000'",
        "puertos":     {"http": 3000},
        "url":         "http://localhost:3000",
        "descripcion": "OWASP Juice Shop — JWT, IDOR, XSS, SSRF, Broken Auth, API abuse",
        "temas": [
            "jwt", "json web token", "algorithm confusion", "rs256", "hs256",
            "owasp", "juice shop", "idor", "broken authentication",
            "ssrf", "api hacking", "nodejs vulnerable", "token manipulation",
            "broken access control", "security misconfiguration",
            "jwt forgery", "auth bypass", "token hijacking",
        ],
        "herramientas": ["burpsuite", "curl", "jwt_tool", "firefox", "cyberchef"],
        "ejemplo_comandos": [
            "curl -s http://localhost:3000/rest/user/login -X POST -H 'Content-Type: application/json' -d '{\"email\":\"test@test.com\",\"password\":\"test\"}'",
            "curl -s http://localhost:3000/api/Challenges | python3 -m json.tool",
        ],
    },

    # ── GRAPHQL ─────────────────────────────────────────────────────
    "dvga": {
        "nombre":      "DVGA — Damn Vulnerable GraphQL",
        "contenedor":  "dvga",
        "imagen":      "dolevf/dvga",
        "ip_cmd":      "echo 'localhost'",
        "start_cmd":   "docker start dvga",
        "puertos":     {"http": 5013},
        "url":         "http://localhost:5013/graphql",
        "descripcion": "GraphQL vulnerable — introspection, injection, DoS, IDOR",
        "temas": [
            "graphql", "introspection", "graphql injection", "graphql dos",
            "schema leak", "query depth", "graphql idor", "api graphql",
            "damn vulnerable graphql", "mutation attack",
        ],
        "herramientas": ["curl", "altair", "graphql-cop", "firefox"],
        "ejemplo_comandos": [
            "docker start dvga",
            'curl -X POST http://localhost:5013/graphql -H "Content-Type: application/json" -d \'{"query": "{ __schema { types { name } } "}\'',
        ],
    },
}

# ═══════════════════════════════════════════════════════════════════
#  TARGETS REMOTOS LEGALES (para reconocimiento, OSINT, sin ataques)
# ═══════════════════════════════════════════════════════════════════

REMOTE_TARGETS = {
    "scanme": {
        "url":         "scanme.nmap.org",
        "descripcion": "Servidor oficial de Nmap — solo reconocimiento pasivo",
        "categoria":   "reconocimiento",
        "herramientas": ["nmap", "ping", "traceroute", "whois"],
        "temas": ["reconocimiento", "nmap basico", "ping", "traceroute", "puertos abiertos"],
    },
    "vulnweb": {
        "url":         "testphp.vulnweb.com",
        "descripcion": "Acunetix PHP vulnerable — demo nikto/dirb sin explotación real",
        "categoria":   "web_demo",
        "herramientas": ["nikto", "dirb", "curl"],
        "temas": ["nikto", "dirb", "fuzzing web", "reconocimiento web", "gobuster"],
    },
    "httpbin": {
        "url":         "httpbin.org",
        "descripcion": "HTTPBin — pruebas HTTP/HTTPS, headers, requests",
        "categoria":   "http",
        "herramientas": ["curl", "wget"],
        "temas": ["http headers", "curl", "api rest", "requests", "burp basico"],
    },
    "badssl": {
        "url":         "badssl.com",
        "descripcion": "BadSSL — certificados SSL intencionalmente malos",
        "categoria":   "ssl",
        "herramientas": ["curl", "openssl", "nmap"],
        "temas": ["ssl", "tls", "certificados", "https", "openssl", "cipher suites"],
    },
    "dns_google": {
        "url":         "google.com",
        "descripcion": "Google — demos WHOIS, DNS, OSINT",
        "categoria":   "osint",
        "herramientas": ["whois", "dig", "nslookup", "dnsrecon"],
        "temas": ["osint", "whois", "dns", "subdominios", "reconocimiento pasivo", "dig", "nslookup"],
    },
}


# ═══════════════════════════════════════════════════════════════════
#  MOTOR DE SELECCIÓN AUTOMÁTICA
# ═══════════════════════════════════════════════════════════════════

def seleccionar_lab_automatico(tema: str) -> dict:
    """
    Analiza el tema del video y retorna el laboratorio más apropiado.
    Prioridad: Docker local > Remote target.

    Returns dict con:
        {
            "tipo": "docker" | "remoto",
            "lab": <dict del lab>,
            "key": <nombre del lab>,
            "ip_placeholder": <IP o URL>,
            "instrucciones_inicio": <str>,
        }
    """
    tema_lower = tema.lower()
    tokens = set(re.findall(r'\w+', tema_lower))

    # 1 — Buscar en Docker labs primero (mayor prioridad)
    mejor_docker = None
    mejor_docker_score = 0

    for key, lab in DOCKER_LABS.items():
        score = 0
        for palabra in lab["temas"]:
            # coincidencia exacta de frase
            if palabra in tema_lower:
                score += 3
            # coincidencia por token
            elif any(t in tokens for t in palabra.split()):
                score += 1
        if score > mejor_docker_score:
            mejor_docker_score = score
            mejor_docker = (key, lab)

    if mejor_docker and mejor_docker_score >= 2:
        key, lab = mejor_docker
        ip = _obtener_ip_lab(lab)
        return {
            "tipo":               "docker",
            "lab":                lab,
            "key":                key,
            "ip_placeholder":     ip,
            "instrucciones_inicio": _generar_instrucciones_docker(lab, ip),
        }

    # 2 — Fallback a targets remotos
    mejor_remoto = None
    mejor_remoto_score = 0

    for key, target in REMOTE_TARGETS.items():
        score = sum(
            3 if palabra in tema_lower else (1 if any(t in tokens for t in palabra.split()) else 0)
            for palabra in target["temas"]
        )
        if score > mejor_remoto_score:
            mejor_remoto_score = score
            mejor_remoto = (key, target)

    if mejor_remoto:
        key, target = mejor_remoto
        return {
            "tipo":               "remoto",
            "lab":                target,
            "key":                key,
            "ip_placeholder":     target["url"],
            "instrucciones_inicio": f"# Target remoto: {target['url']} — {target['descripcion']}",
        }

    # 3 — Fallback absoluto
    return {
        "tipo":               "remoto",
        "lab":                REMOTE_TARGETS["scanme"],
        "key":                "scanme",
        "ip_placeholder":     "scanme.nmap.org",
        "instrucciones_inicio": "# Fallback: scanme.nmap.org",
    }


def _obtener_ip_lab(lab: dict) -> str:
    """Intenta obtener la IP real del contenedor Docker. Retorna placeholder si falla."""
    try:
        result = subprocess.run(
            lab["ip_cmd"], shell=True,
            capture_output=True, text=True, timeout=5
        )
        ip = result.stdout.strip()
        if ip and ip != "localhost":
            return ip
    except Exception:
        pass
    return "DOCKER_LAB_IP"


def _generar_instrucciones_docker(lab: dict, ip: str) -> str:
    """Genera el bloque de instrucciones de inicio para el prompt de la IA."""
    lines = [
        f"# LABORATORIO DOCKER: {lab['nombre']}",
        f"# Contenedor: {lab['contenedor']}",
        f"# Iniciar con: {lab['start_cmd']}",
        f"# IP de la víctima: {ip}",
    ]
    if "url" in lab:
        lines.append(f"# URL: {lab['url']}")
    if "credenciales" in lab:
        lines.append(f"# Credenciales: {lab['credenciales']}")
    lines.append(f"# Herramientas recomendadas: {', '.join(lab['herramientas'])}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
#  FUNCIONES DE COMPATIBILIDAD (API anterior)
# ═══════════════════════════════════════════════════════════════════

def get_all_targets() -> list:
    """Retorna todos los labs como lista (Docker + remotos)."""
    resultado = []
    for k, v in DOCKER_LABS.items():
        resultado.append({"id": k, "tipo": "docker", **v})
    for k, v in REMOTE_TARGETS.items():
        resultado.append({"id": k, "tipo": "remoto", **v})
    return resultado


def get_targets_by_category(category: str) -> list:
    return [t for t in get_all_targets() if t.get("categoria") == category]


def get_targets_summary_for_prompt() -> str:
    """
    Genera el bloque completo de laboratorios para inyectar en el System Prompt.
    Incluye labs Docker locales (alta prioridad) y targets remotos (fallback).
    """
    lines = [
        "═══════════════════════════════════════════════",
        "LABORATORIOS DISPONIBLES — SELECCIÓN AUTOMÁTICA",
        "═══════════════════════════════════════════════",
        "",
        "🐳 LABS DOCKER LOCALES (PRIORIDAD MÁXIMA — usar para ataques reales):",
    ]
    for key, lab in DOCKER_LABS.items():
        temas_str = ", ".join(lab["temas"][:6])
        lines.append(f"  • [{key.upper()}] {lab['nombre']}")
        lines.append(f"    Contenedor: {lab['contenedor']}")
        if "url" in lab:
            lines.append(f"    URL: {lab['url']}")
        lines.append(f"    Temas: {temas_str}...")
        lines.append(f"    Inicio: {lab['start_cmd']}")
        lines.append("")

    lines += [
        "🌐 TARGETS REMOTOS (solo reconocimiento pasivo, SIN ataques activos):",
    ]
    for key, t in REMOTE_TARGETS.items():
        lines.append(f"  • {t['url']} — {t['descripcion']}")

    lines += [
        "",
        "REGLAS DE SELECCIÓN:",
        "1. Si el tema involucra Metasploit, exploits, shells, backdoors → USA metasploitable2 (victima-lab)",
        "2. Si el tema involucra SQLi, XSS, CSRF, brute force web → USA DVWA (localhost:8080)",
        "3. Si el tema involucra JWT, OWASP Top 10 moderno, API abuse → USA Juice Shop (localhost:3000)",
        "4. Si el tema involucra GraphQL → USA DVGA (localhost:5013)",
        "5. Si el tema es solo reconocimiento pasivo → USA scanme.nmap.org",
        "6. NUNCA uses scanme.nmap.org para ataques activos, exploits o herramientas ofensivas.",
        "7. SIEMPRE inicia el contenedor Docker con su start_cmd antes del primer comando.",
        "8. SIEMPRE obtén la IP real con: docker inspect [contenedor] --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'",
    ]
    return "\n".join(lines)
