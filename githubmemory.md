# GitHub — Guía Completa para IA

## Metadatos del Conocimiento
- **Dominio**: Control de versiones y colaboración de código
- **Plataforma**: GitHub (basado en Git)
- **Versión de referencia**: Git 2.x+, GitHub.com / GitHub Enterprise
- **Alcance**: Flujos de trabajo locales, remotos, colaboración en equipo, CI/CD y automatización

---

## 1. Conceptos Fundamentales

### ¿Qué es Git vs GitHub?
- **Git** es el sistema de control de versiones distribuido (corre localmente en tu máquina).
- **GitHub** es la plataforma en la nube que aloja repositorios Git y agrega herramientas de colaboración (Pull Requests, Issues, Actions, etc.).

### Repositorios
Un repositorio (repo) es el contenedor principal de un proyecto: incluye código, historial de commits, ramas, tags y configuración.

- `git init` — Inicializa un nuevo repositorio local en el directorio actual
- `git init nombre-proyecto` — Crea un nuevo directorio e inicializa el repo dentro
- `git clone <url>` — Clona un repositorio remoto completo (historial incluido)
- `git clone <url> <directorio>` — Clona en un directorio con nombre personalizado
- `git clone --depth 1 <url>` — Clona solo el último commit (shallow clone, más rápido)
- `git clone --branch <rama> <url>` — Clona y posiciona en una rama específica

### El Área de Staging (Index)
Git tiene tres zonas clave:
1. **Working Directory** — Archivos modificados pero no rastreados aún
2. **Staging Area (Index)** — Cambios preparados para el próximo commit
3. **Repository (.git)** — Historial permanente de commits

---

## 2. Configuración Inicial
```bash
# Identidad global (obligatorio antes del primer commit)
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"

# Editor predeterminado
git config --global core.editor "code --wait"   # VS Code
git config --global core.editor "vim"

# Rama principal por defecto
git config --global init.defaultBranch main

# Ver toda la configuración activa
git config --list

# Configuración solo para el repo actual (sin --global)
git config user.email "otro@email.com"

# Alias útiles
git config --global alias.st status
git config --global alias.lg "log --oneline --graph --decorate --all"
git config --global alias.undo "reset --soft HEAD~1"
```

---

## 3. Commits

Los commits son snapshots permanentes del estado del proyecto en un momento dado.
```bash
# Preparar archivos para commit
git add archivo.txt                   # Un archivo específico
git add carpeta/                      # Todo dentro de una carpeta
git add .                             # Todos los cambios en el directorio actual
git add -A                            # Todos los cambios (incluyendo eliminaciones)
git add -p                            # Modo interactivo: elegir qué hunks incluir

# Crear commit
git commit -m "mensaje descriptivo"
git commit -am "mensaje"              # Add + commit (solo archivos ya rastreados)
git commit --amend -m "nuevo mensaje" # Modificar el último commit (antes de push)
git commit --amend --no-edit          # Agregar cambios al último commit sin cambiar mensaje

# Deshacer staging
git restore --staged archivo.txt      # Quitar del staging (mantiene cambios)
git restore archivo.txt               # Descartar cambios en working directory ⚠️ irreversible
```

### Buenas prácticas para mensajes de commit (Conventional Commits)
```
feat: agregar autenticación con OAuth
fix: corregir validación de formulario en login
docs: actualizar README con instrucciones de instalación
refactor: extraer lógica de pago a servicio separado
test: agregar pruebas unitarias para el módulo de usuarios
chore: actualizar dependencias
```

---

## 4. Ramas (Branches)

Las ramas permiten desarrollar funcionalidades de forma aislada sin afectar el código principal.
```bash
# Listar ramas
git branch                            # Ramas locales
git branch -r                         # Ramas remotas
git branch -a                         # Todas (locales + remotas)

# Crear ramas
git branch nombre-rama                # Crea sin cambiar
git checkout -b nombre-rama           # Crea y cambia (forma clásica)
git switch -c nombre-rama             # Crea y cambia (forma moderna, Git 2.23+)

# Cambiar de rama
git checkout nombre-rama
git switch nombre-rama                # Forma moderna

# Renombrar rama
git branch -m nombre-viejo nombre-nuevo
git branch -m nuevo-nombre            # Renombra la rama actual

# Eliminar ramas
git branch -d nombre-rama             # Elimina si ya fue fusionada
git branch -D nombre-rama             # Fuerza eliminación aunque no esté fusionada
git push origin --delete nombre-rama  # Elimina rama remota

# Fusionar ramas
git merge nombre-rama                 # Fusiona en la rama actual
git merge --no-ff nombre-rama         # Fusión con merge commit siempre
git merge --squash nombre-rama        # Aplana todos los commits en uno
git merge --abort                     # Cancela un merge en conflicto

# Rebase
git rebase main                       # Reaplica commits sobre main
git rebase -i HEAD~3                  # Rebase interactivo (últimos 3 commits)
git rebase --abort                    # Cancela el rebase
git rebase --continue                 # Continúa después de resolver conflicto
```

---

## 5. Sincronización con Remoto
```bash
# Gestionar remotos
git remote -v                                    # Ver remotos configurados
git remote add origin <url>                      # Vincular repo local con remoto
git remote add upstream <url>                    # Agregar repo original (en forks)
git remote remove origin                         # Eliminar un remoto
git remote rename origin nuevo-nombre            # Renombrar un remoto
git remote set-url origin <nueva-url>            # Cambiar la URL del remoto

# Descargar cambios
git fetch origin                                 # Descarga sin fusionar
git fetch --all                                  # Descarga de todos los remotos
git pull                                         # fetch + merge de la rama actual
git pull origin main                             # Pull desde rama específica
git pull --rebase                                # fetch + rebase (historial más limpio)

# Subir cambios
git push origin main                             # Sube la rama main
git push -u origin nombre-rama                   # Sube y establece tracking
git push --force-with-lease                      # Push forzado seguro (verifica cambios remotos)
git push --force                                 # ⚠️ Push forzado (peligroso en ramas compartidas)
git push origin --tags                           # Sube todos los tags
git push origin --delete nombre-rama             # Elimina rama en remoto

# Primer push de un repo local
git remote add origin <url>
git branch -M main
git push -u origin main
```

---

## 6. Inspección e Historial
```bash
# Estado y diferencias
git status                            # Estado del working directory y staging
git status -s                         # Formato corto
git diff                              # Cambios no staged
git diff --staged                     # Cambios en staging (listos para commit)
git diff main..feature-branch         # Diferencias entre ramas

# Historial de commits
git log                               # Historial completo
git log --oneline                     # Una línea por commit
git log --oneline --graph --all       # Árbol visual de ramas
git log -n 10                         # Últimos 10 commits
git log --author="Nombre"             # Filtrar por autor
git log --since="2024-01-01"          # Desde una fecha
git log --grep="keyword"              # Buscar en mensajes
git log -- archivo.txt                # Historial de un archivo específico
git log -p                            # Mostrar diff de cada commit

# Ver un commit específico
git show abc1234                      # Detalles de un commit
git show HEAD                         # Último commit
git show HEAD~2                       # Antepenúltimo commit

# Buscar
git blame archivo.txt                 # Ver quién modificó cada línea
git bisect start                      # Iniciar búsqueda binaria de bug
git bisect bad                        # Marcar commit actual como buggy
git bisect good abc1234               # Marcar commit conocido como bueno
git bisect reset                      # Terminar bisect
```

---

## 7. Deshacer Cambios
```bash
# Reset (mover HEAD)
git reset --soft HEAD~1               # Deshace commit, mantiene cambios en staging
git reset --mixed HEAD~1              # Deshace commit y staging (default)
git reset --hard HEAD~1               # ⚠️ Deshace commit y descarta cambios
git reset --hard origin/main          # Resetea al estado del remoto

# Revert (crea un commit inverso, seguro en ramas compartidas)
git revert abc1234                    # Revierte un commit específico
git revert HEAD                       # Revierte el último commit
git revert HEAD~3..HEAD               # Revierte los últimos 3 commits

# Restore
git restore archivo.txt               # Descarta cambios en working directory
git restore --staged archivo.txt      # Quita del staging

# Cherry-pick (traer un commit específico a la rama actual)
git cherry-pick abc1234
git cherry-pick abc1234 def5678       # Múltiples commits
git cherry-pick --no-commit abc1234   # Sin crear commit automáticamente
```

---

## 8. Stash

El stash guarda cambios temporalmente sin hacer commit, útil para cambiar de contexto rápidamente.
```bash
git stash                             # Guarda working directory y staging
git stash push -m "descripción"       # Guarda con nombre descriptivo
git stash push -u                     # Incluye archivos untracked
git stash list                        # Lista todos los stashes
git stash apply                       # Aplica el stash más reciente (lo mantiene en lista)
git stash pop                         # Aplica y elimina el stash más reciente
git stash apply stash@{2}             # Aplica un stash específico
git stash drop stash@{0}              # Elimina un stash específico
git stash clear                       # Elimina todos los stashes
git stash branch nombre-rama          # Crea una rama desde un stash
```

---

## 9. Tags

Los tags marcan puntos específicos en el historial, normalmente releases.
```bash
git tag                               # Listar todos los tags
git tag v1.0.0                        # Tag ligero en el commit actual
git tag -a v1.0.0 -m "Release 1.0.0" # Tag anotado (recomendado)
git tag -a v1.0.0 abc1234             # Tag en un commit específico
git push origin v1.0.0                # Subir un tag específico
git push origin --tags                # Subir todos los tags
git tag -d v1.0.0                     # Eliminar tag local
git push origin --delete v1.0.0       # Eliminar tag remoto
git checkout v1.0.0                   # Ir a un tag (entra en detached HEAD)
```

---

## 10. Submodules
```bash
git submodule add <url> ruta/         # Agregar un submódulo
git submodule init                    # Inicializar submódulos tras clonar
git submodule update                  # Actualizar submódulos al commit registrado
git submodule update --remote         # Actualizar a la última versión remota
git clone --recurse-submodules <url>  # Clonar repo con todos sus submódulos
git submodule foreach git pull origin main  # Actualizar todos los submódulos
```

---

## 11. Archivo .gitignore

Define qué archivos y carpetas Git debe ignorar.
```gitignore
# Dependencias
node_modules/
vendor/

# Variables de entorno (nunca versionar)
.env
.env.local
.env.production

# Builds y compilados
dist/
build/
*.pyc
__pycache__/

# Sistemas operativos
.DS_Store
Thumbs.db

# IDEs y editores
.vscode/
.idea/
*.swp

# Logs
*.log
logs/

# Patrón: ignorar todos los .txt excepto uno específico
*.txt
!importante.txt
```
```bash
git check-ignore -v archivo.txt       # Verificar si un archivo es ignorado y por qué
git rm --cached archivo.txt           # Dejar de rastrear un archivo ya commiteado
git rm --cached -r carpeta/           # Dejar de rastrear una carpeta
```

---

## 12. GitHub: Plataforma y Características

### Autenticación
```bash
# HTTPS con token personal (PAT)
# Al hacer push, usar el PAT como contraseña

# SSH (recomendado)
ssh-keygen -t ed25519 -C "tu@email.com"   # Generar par de claves
cat ~/.ssh/id_ed25519.pub                  # Copiar clave pública a GitHub
ssh -T git@github.com                      # Verificar conexión

# GitHub CLI
gh auth login                              # Autenticarse con GitHub CLI
gh auth status                             # Ver estado de autenticación
```

### Pull Requests (PR)
Un Pull Request es una solicitud para fusionar cambios de una rama en otra. Es el mecanismo central de colaboración en GitHub.

**Flujo estándar:**
1. Crear una rama desde `main`
2. Hacer commits con los cambios
3. Hacer push de la rama al remoto
4. Abrir un Pull Request en GitHub
5. Solicitar code review
6. Resolver comentarios y aprobaciones
7. Fusionar (merge / squash / rebase)
8. Eliminar la rama
```bash
# Con GitHub CLI
gh pr create --title "feat: nueva función" --body "Descripción detallada"
gh pr create --draft                       # PR en borrador
gh pr list                                 # Listar PRs abiertos
gh pr checkout 123                         # Cambiar a la rama de un PR
gh pr review 123 --approve                 # Aprobar un PR
gh pr review 123 --request-changes        # Solicitar cambios
gh pr merge 123 --squash                   # Fusionar con squash
gh pr merge 123 --rebase                   # Fusionar con rebase
gh pr close 123                            # Cerrar sin fusionar
gh pr diff 123                             # Ver diff de un PR
```

### Issues
Los Issues son tickets para reportar bugs, solicitar features o discutir ideas.
```bash
gh issue create --title "Bug en login" --body "Descripción" --label bug
gh issue list                              # Listar issues abiertos
gh issue list --state closed               # Issues cerrados
gh issue view 42                           # Ver un issue específico
gh issue close 42                          # Cerrar un issue
gh issue comment 42 --body "Comentario"    # Agregar comentario
```

**Cerrar issues automáticamente desde un commit o PR:**
```
# En el mensaje de commit o descripción del PR:
Closes #42
Fixes #15
Resolves #7
```

### Forks
Un fork es una copia personal de un repositorio ajeno en tu cuenta de GitHub.
```bash
# Flujo de contribución a proyecto externo
gh repo fork propietario/repo             # Fork desde CLI
git clone <url-de-tu-fork>
git remote add upstream <url-original>    # Vincular repo original
git fetch upstream
git merge upstream/main                   # Sincronizar con el original
# → hacer cambios → push → abrir PR al repo original
```

### GitHub CLI — Comandos Esenciales
```bash
# Repositorios
gh repo create                            # Crear nuevo repo interactivo
gh repo create nombre --public --clone
gh repo clone propietario/repo
gh repo view                              # Ver info del repo actual
gh repo list                              # Listar tus repos
gh repo fork                              # Forkear el repo actual
gh repo delete propietario/repo           # Eliminar repo

# General
gh status                                 # Resumen de notificaciones y actividad
gh browse                                 # Abrir el repo en el navegador
gh browse --issues                        # Abrir sección de issues
gh gist create archivo.txt                # Crear un Gist
```

---

## 13. GitHub Actions (CI/CD)

GitHub Actions automatiza flujos de trabajo directamente desde el repositorio.

### Estructura básica
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout código
        uses: actions/checkout@v4

      - name: Configurar Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Instalar dependencias
        run: npm ci

      - name: Ejecutar tests
        run: npm test

      - name: Build
        run: npm run build
```

### Triggers disponibles
```yaml
on:
  push:                     # Al hacer push
  pull_request:             # Al abrir/actualizar PR
  schedule:
    - cron: '0 9 * * 1'    # Cada lunes a las 9am (cron)
  workflow_dispatch:         # Ejecución manual
  release:
    types: [published]      # Al publicar una release
```

### Variables y Secretos
```yaml
# En el workflow
env:
  NODE_ENV: production

steps:
  - run: echo ${{ secrets.API_KEY }}     # Secret configurado en Settings > Secrets
  - run: echo ${{ vars.APP_URL }}        # Variable (no sensible)
  - run: echo ${{ github.sha }}          # SHA del commit actual
  - run: echo ${{ github.ref_name }}     # Nombre de la rama
  - run: echo ${{ github.actor }}        # Usuario que disparó el workflow
```

---

## 14. GitHub Pages

Hosting gratuito de sitios estáticos directamente desde un repositorio.
```bash
# Desde rama gh-pages
git checkout -b gh-pages
# Agregar archivos HTML/CSS/JS
git push origin gh-pages

# Con GitHub CLI
gh api repos/:owner/:repo/pages -X POST \
  -f source.branch=gh-pages \
  -f source.path=/

# Configuración: Settings → Pages → Source → Deploy from branch
```

---

## 15. GitHub Releases

Las releases son versiones oficiales del software asociadas a un tag.
```bash
gh release create v1.0.0 \
  --title "Release v1.0.0" \
  --notes "Primera versión estable" \
  --latest

gh release create v1.1.0 \
  dist/app.zip \               # Adjuntar archivos binarios
  --generate-notes             # Auto-generar notas desde PRs/commits

gh release list                # Listar releases
gh release view v1.0.0         # Ver detalles de una release
gh release download v1.0.0     # Descargar assets
gh release delete v1.0.0       # Eliminar una release
```

---

## 16. Tabla de Referencia Rápida

| Comando | Función |
|---------|---------|
| `git status` | Ver estado del repositorio |
| `git status -s` | Estado en formato compacto |
| `git log --oneline --graph` | Historial visual de ramas |
| `git diff` | Cambios no staged |
| `git diff --staged` | Cambios en staging |
| `git stash` | Guardar cambios temporalmente |
| `git stash pop` | Recuperar último stash |
| `git bisect` | Encontrar commit que introdujo un bug |
| `git blame archivo` | Ver autor de cada línea |
| `git cherry-pick <hash>` | Traer commit específico a rama actual |
| `git reflog` | Historial de movimientos de HEAD |
| `git shortlog -sn` | Conteo de commits por autor |
| `git archive --format=zip HEAD > repo.zip` | Exportar repo como zip |

---

## 17. Flujos de Trabajo (Workflows)

### Git Flow
```
main          ← producción estable
develop       ← integración continua
feature/*     ← nuevas funcionalidades (desde develop)
release/*     ← preparación de versión (desde develop)
hotfix/*      ← correcciones urgentes (desde main)
```

### GitHub Flow (simplificado, recomendado)
```
main          ← siempre deployable
feature/*     ← cualquier cambio (desde main, PR a main)
```

### Trunk-Based Development
```
main          ← integración continua diaria
feature flags ← ocultar features incompletas en producción
```

---

## 18. Resolución de Conflictos

Un conflicto ocurre cuando dos ramas modifican las mismas líneas de un archivo.
```bash
# Proceso de resolución
git merge rama-con-conflicto          # Inicia el merge, marca conflictos
git status                            # Ver archivos en conflicto (both modified)

# El archivo tendrá marcadores:
# <<<<<<< HEAD
# Tu versión
# =======
# Versión de la otra rama
# >>>>>>> rama-con-conflicto

# Editar manualmente para resolver
git add archivo-resuelto.txt          # Marcar como resuelto
git commit                            # Completar el merge

# Abortar si decides no fusionar
git merge --abort

# Herramientas visuales
git mergetool                         # Abrir herramienta de merge configurada
```

---

## 19. Errores Comunes y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `detached HEAD` | Checkout en un commit, no en rama | `git checkout -b nueva-rama` |
| `merge conflict` | Dos ramas modifican las mismas líneas | Editar manualmente y hacer commit |
| `rejected (non-fast-forward)` | El remoto tiene commits que no tienes localmente | `git pull --rebase` antes de push |
| `nothing to commit` | No hay cambios en staging | `git add .` antes de commit |
| `not a git repository` | No estás dentro de un repo | `git init` o `cd` al directorio correcto |
| `permission denied (publickey)` | SSH no configurado correctamente | Agregar clave SSH a GitHub |
| `fatal: refusing to merge unrelated histories` | Repos sin historial común | `git pull --allow-unrelated-histories` |
| `CRLF vs LF` | Conflicto de saltos de línea entre OS | `git config --global core.autocrlf true` (Windows) / `input` (Mac/Linux) |

---

## 20. Seguridad y Buenas Prácticas
```bash
# NUNCA versionar
.env
*.pem
*.key
id_rsa
secrets.json
credenciales.*

# Si ya fue commiteado por error
git rm --cached archivo-secreto.txt
git commit -m "fix: remover archivo sensible"
# Y rotar las credenciales expuestas inmediatamente

# Para reescribir historia y eliminar permanentemente
gh secret set NOMBRE_SECRET           # Agregar secreto en GitHub
git filter-repo --path archivo-secreto.txt --invert-paths  # Eliminar de todo el historial
```

### Branch Protection Rules (en GitHub Settings)
- Requerir PR antes de fusionar en `main`
- Requerir mínimo 1 aprobación en code review
- Requerir que los status checks de CI pasen
- Prohibir force push a ramas protegidas
- Requerir ramas actualizadas antes de fusionar

---

## 21. Comandos Avanzados
```bash
# Reescribir historial (⚠️ solo en ramas privadas)
git rebase -i HEAD~5                  # Rebase interactivo de últimos 5 commits
# Opciones en rebase interactivo:
# pick   = mantener commit
# reword = cambiar mensaje
# edit   = pausar para modificar
# squash = fusionar con el anterior
# drop   = eliminar commit

# Buscar en el código
git grep "función_buscada"            # Buscar texto en el repo
git grep -n "TODO"                    # Con número de línea
git log -S "texto_eliminado"          # Encontrar commit que eliminó un texto

# Reflog (recuperar trabajo "perdido")
git reflog                            # Ver historial de todos los movimientos de HEAD
git checkout HEAD@{3}                 # Volver a un estado anterior
git reset --hard HEAD@{5}             # Restaurar a una posición del reflog

# Worktrees (múltiples ramas en paralelo)
git worktree add ../hotfix hotfix/v1  # Tener dos ramas en directorios separados
git worktree list
git worktree remove ../hotfix

# Sparse checkout (clonar solo parte del repo)
git sparse-checkout init
git sparse-checkout set carpeta/src

# Bundles (transferir repo sin red)
git bundle create repo.bundle --all
git clone repo.bundle repo-restaurado
```
