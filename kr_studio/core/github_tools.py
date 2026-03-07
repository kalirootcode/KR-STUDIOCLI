import urllib.request
import urllib.parse
import json
import logging
import base64

logger = logging.getLogger(__name__)

class GitHubOSINTTools:
    """Herramientas de OSINT en GitHub (estilo MCP) para que la IA extraiga información real y actualizada."""

    def __init__(self):
        pass

    def search_github_repos(self, query: str, max_results: int = 5) -> str:
        """
        Busca repositorios en GitHub relevantes para ciberseguridad, hacking o herramientas específicas.
        Retorna el nombre, descripción, estrellas y URL de los repositorios encontrados.
        Útil para encontrar la herramienta exacta que el usuario solicita si la desconoces.
        """
        try:
            # Asegurar que la búsqueda se enfoque en cosas útiles
            if "hacking" not in query.lower() and "security" not in query.lower():
                safe_query = f"{query} security OR hacking"
            else:
                safe_query = query
                
            q_encoded = urllib.parse.quote(safe_query)
            url = f"https://api.github.com/search/repositories?q={q_encoded}&sort=stars&order=desc&per_page={max_results}"
            
            headers = {'User-Agent': 'KR-STUDIO-AI-Engine'}
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
            if not data.get("items"):
                return f"No se encontraron repositorios para la búsqueda: {query}"
                
            result = "Resultados de búsqueda en GitHub:\n"
            for item in data["items"]:
                result += f"• [{item['full_name']}] ⭐ {item['stargazers_count']}\n"
                result += f"  Descripción: {item.get('description', 'Sin descripción')}\n"
                result += f"  Clone URL: {item['clone_url']}\n\n"
                
            return result
        except Exception as e:
            logger.error(f"Error en search_github_repos: {e}")
            return f"Ocurrió un error al buscar en GitHub: {e}. Intenta usar Google Search en su lugar."

    def get_github_readme(self, repo_full_name: str) -> str:
        """
        Obtiene el contenido completo del README.md de un repositorio específico de GitHub.
        Requiere el nombre completo del repositorio (ejemplo: 'rapid7/metasploit-framework').
        CRÍTICO: Usa esta herramienta para leer las instrucciones REALES de instalación y uso antes de generar un guion, evitando así inventar comandos o flags irreales.
        """
        try:
            # Buscar el contenido del README a través de la API
            url = f"https://api.github.com/repos/{repo_full_name}/readme"
            headers = {'User-Agent': 'KR-STUDIO-AI-Engine'}
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
            if "content" in data:
                # Decodificar el contenido base64 del README
                readme_content = base64.b64decode(data["content"]).decode('utf-8')
                # Truncar si es demasiado largo para no gastar todos los tokens (max 15000 chars estim)
                if len(readme_content) > 15000:
                    readme_content = readme_content[:15000] + "\n... [README TRUNCADO POR LONGITUD] ..."
                return f"--- README DE {repo_full_name} ---\n\n{readme_content}"
            else:
                return f"No se encontró contenido decodificable en el README de {repo_full_name}."
                
        except urllib.error.HTTPError as e:
            if e.code == 403:
                return "Error 403: Rate Limit excedido en la API de GitHub."
            elif e.code == 404:
                return f"Error 404: No se encontró un README para el repositorio {repo_full_name}."
            return f"Error accediendo al README: {e}"
        except Exception as e:
            logger.error(f"Error en get_github_readme: {e}")
            return f"Ocurrió un error inesperado al leer el README: {e}"

    def get_tool_functions(self):
        """Devuelve las funciones que el agente IA (Gemini) puede usar como 'tools'."""
        return [self.search_github_repos, self.get_github_readme]
