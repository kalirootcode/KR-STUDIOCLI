"""
targets_db.py — Base de Datos de Targets Legales para Pentesting
Todos estos sitios tienen permisos explícitos o están diseñados para ser testeados.
"""

TARGETS = {
    # ═══════════════════════════════════════════
    # ESCANEO DE PUERTOS Y RECONOCIMIENTO
    # ═══════════════════════════════════════════
    "scanme": {
        "url": "scanme.nmap.org",
        "description": "Servidor oficial de Nmap autorizado para escaneo de puertos",
        "category": "reconocimiento",
        "allowed_tools": ["nmap", "ping", "traceroute", "whois", "dig"],
        "example_commands": [
            "kr-cli nmap -sV scanme.nmap.org",
            "kr-cli nmap -sC -sV -p- scanme.nmap.org",
            "kr-cli nmap -sS -T4 scanme.nmap.org",
            "kr-cli nmap --script vuln scanme.nmap.org",
        ]
    },

    # ═══════════════════════════════════════════
    # VULNERABILIDADES WEB
    # ═══════════════════════════════════════════
    "vulnweb": {
        "url": "testphp.vulnweb.com",
        "description": "Aplicación PHP vulnerable de Acunetix — SQL Injection, XSS, LFI",
        "category": "web_vuln",
        "allowed_tools": ["nikto", "sqlmap", "curl", "dirb", "gobuster", "wfuzz"],
        "example_commands": [
            "kr-cli nikto -h http://testphp.vulnweb.com",
            "kr-cli curl -I http://testphp.vulnweb.com",
            "kr-cli dirb http://testphp.vulnweb.com",
        ]
    },
    "vulnweb_rest": {
        "url": "rest.vulnweb.com",
        "description": "API REST vulnerable de Acunetix — pruebas de API security",
        "category": "web_vuln",
        "allowed_tools": ["curl", "nikto", "burpsuite"],
        "example_commands": [
            "kr-cli curl -X GET http://rest.vulnweb.com",
        ]
    },
    "vulnweb_asp": {
        "url": "testasp.vulnweb.com",
        "description": "Aplicación ASP.NET vulnerable de Acunetix",
        "category": "web_vuln",
        "allowed_tools": ["nikto", "curl", "dirb"],
        "example_commands": [
            "kr-cli nikto -h http://testasp.vulnweb.com",
        ]
    },
    "juice_shop": {
        "url": "juice-shop.herokuapp.com",
        "description": "OWASP Juice Shop — Aplicación moderna vulnerable (Node.js)",
        "category": "web_vuln",
        "allowed_tools": ["nikto", "curl", "sqlmap", "burpsuite"],
        "example_commands": [
            "kr-cli curl -I https://juice-shop.herokuapp.com",
        ]
    },
    "google_gruyere": {
        "url": "google-gruyere.appspot.com",
        "description": "Google Gruyere — App vulnerable oficial de Google para XSS y más",
        "category": "web_vuln",
        "allowed_tools": ["curl"],
        "example_commands": [
            "kr-cli curl -I https://google-gruyere.appspot.com",
        ]
    },

    # ═══════════════════════════════════════════
    # OSINT Y RECONOCIMIENTO DNS
    # ═══════════════════════════════════════════
    "dns_google": {
        "url": "google.com",
        "description": "Google — para demos de WHOIS, DNS, subdomain enumeration",
        "category": "osint",
        "allowed_tools": ["whois", "dig", "nslookup", "dnsrecon", "host"],
        "example_commands": [
            "kr-cli whois google.com",
            "kr-cli dig google.com ANY",
            "kr-cli nslookup google.com",
            "kr-cli dig +short google.com MX",
        ]
    },
    "dns_cloudflare": {
        "url": "cloudflare.com",
        "description": "Cloudflare — demos de investigación DNS y headers HTTP",
        "category": "osint",
        "allowed_tools": ["whois", "dig", "curl", "nslookup"],
        "example_commands": [
            "kr-cli whois cloudflare.com",
            "kr-cli curl -I https://cloudflare.com",
        ]
    },

    # ═══════════════════════════════════════════
    # HEADERS HTTP Y SEGURIDAD WEB
    # ═══════════════════════════════════════════
    "securityheaders": {
        "url": "securityheaders.com",
        "description": "SecurityHeaders.com — para analizar cabeceras de seguridad HTTP",
        "category": "headers",
        "allowed_tools": ["curl"],
        "example_commands": [
            "kr-cli curl -I https://securityheaders.com",
        ]
    },
    "httpbin": {
        "url": "httpbin.org",
        "description": "HTTPBin — servicio de prueba HTTP/HTTPS para debugging de requests",
        "category": "headers",
        "allowed_tools": ["curl", "wget"],
        "example_commands": [
            "kr-cli curl https://httpbin.org/ip",
            "kr-cli curl https://httpbin.org/headers",
            "kr-cli curl -X POST https://httpbin.org/post -d 'test=1'",
        ]
    },

    # ═══════════════════════════════════════════
    # CTF Y PLATAFORMAS DE PRÁCTICA
    # ═══════════════════════════════════════════
    "hackthissite": {
        "url": "hackthissite.org",
        "description": "HackThisSite — plataforma CTF legal y gratuita",
        "category": "ctf",
        "allowed_tools": ["curl", "nmap", "whois"],
        "example_commands": [
            "kr-cli whois hackthissite.org",
            "kr-cli curl -I https://hackthissite.org",
        ]
    },
    "overthewire": {
        "url": "overthewire.org",
        "description": "OverTheWire — wargames de Linux y seguridad",
        "category": "ctf",
        "allowed_tools": ["ssh", "whois", "dig"],
        "example_commands": [
            "kr-cli whois overthewire.org",
        ]
    },

    # ═══════════════════════════════════════════
    # ANÁLISIS SSL/TLS
    # ═══════════════════════════════════════════
    "badssl": {
        "url": "badssl.com",
        "description": "BadSSL — sitio con certificados SSL intencionalmente malos",
        "category": "ssl",
        "allowed_tools": ["curl", "openssl", "nmap"],
        "example_commands": [
            "kr-cli curl -vI https://expired.badssl.com",
            "kr-cli curl -vI https://self-signed.badssl.com",
            "kr-cli nmap --script ssl-enum-ciphers -p 443 badssl.com",
        ]
    },

    # ═══════════════════════════════════════════
    # SHODAN / INTELIGENCIA ABIERTA
    # ═══════════════════════════════════════════
    "shodan": {
        "url": "shodan.io",
        "description": "Shodan — motor de búsqueda de dispositivos IoT conectados",
        "category": "osint",
        "allowed_tools": ["curl", "whois"],
        "example_commands": [
            "kr-cli curl -I https://www.shodan.io",
            "kr-cli whois shodan.io",
        ]
    },
}


def get_all_targets() -> list:
    """Retorna todos los targets como lista de dicts."""
    return [{"id": k, **v} for k, v in TARGETS.items()]


def get_targets_by_category(category: str) -> list:
    """Filtra targets por categoría."""
    return [{"id": k, **v} for k, v in TARGETS.items() if v["category"] == category]


def get_targets_summary_for_prompt() -> str:
    """Genera un resumen de targets para inyectar en el System Prompt de la IA."""
    lines = ["TARGETS LEGALES AUTORIZADOS PARA PENTESTING:"]
    for key, t in TARGETS.items():
        cmds = ", ".join(t["allowed_tools"][:4])
        lines.append(f"  • {t['url']} — {t['description']} (herramientas: {cmds})")
    lines.append("")
    lines.append("SIEMPRE usa estos targets en los comandos del guion. NUNCA inventes URLs aleatorias.")
    return "\n".join(lines)
