# Convenciones de Git para el proyecto Rift Analytics

## Branches

| Branch | Uso | Notas |
|---|---|---|
| `main` | Producción estable | Nunca se hace push directo; solo merges desde `develop` o hotfixes |
| `develop` | Desarrollo principal | Acumula features completas y testeadas |
| `feature/<nombre>` | Desarrollo de una nueva funcionalidad | Se crea desde `develop` y se mergea a `develop` al terminar |
| `bugfix/<nombre>` | Corrección de errores | Se crea desde `develop` (o desde `main` si es hotfix crítico) |
| `hotfix/<nombre>` | Corrección urgente en producción | Se crea desde `main` y se mergea a `main` y `develop` |
| `release/<version>` | Preparación de release | Se crea desde `develop` antes de un release; permite ajustes menores y testing |

Ejemplos de nombres:

- `feature/auth-login`
- `bugfix/fix-drf-cors`
- `hotfix/fix-frontend-build`
- `release/v1.2.0`

## Convenciones de commits

Se recomienda usar Conventional Commits:

``` powershell
<tipo>(<área>): <descripción corta>

[body opcional]

[footer opcional]
```

Tipos permitidos:

| Tipo | Descripción | Ejemplo |
|---|---|---|
| `feat` | Nueva funcionalidad | `feat(auth): agregar login con JWT` |
| `fix` | Corrección de bug | `fix(api): corregir endpoint de usuarios` |
| `docs` | Cambios en documentación | `docs(readme): actualizar guía de docker` |
| `style` | Formato, linting, espacios | `style(backend): aplicar black` |
| `refactor` | Refactorización sin cambio funcional | `refactor(frontend): simplificar layout de cards` |
| `perf` | Mejoras de rendimiento | `perf(db): optimizar query de posts` |
| `test` | Añadir o corregir tests | `test(api): agregar pruebas para endpoints de auth` |
| `chore` | Tareas de mantenimiento | `chore(docker): actualizar imagen base de node` |

Reglas generales:

- Mensaje corto máximo 50 caracteres.
- Mensaje descriptivo en imperativo: “Agregar feature” en lugar de “Agregado feature”.
- Body opcional para explicar qué y por qué.
- Footer opcional para issues o breaking changes:

```powershell
BREAKING CHANGE: cambia el formato de respuesta de /api/users
Closes #42
```

## Flujo de trabajo recomendado (Git Flow simplificado)

Siempre partir de `develop` para nuevas features:

```powershell
git checkout develop
git pull origin develop
git checkout -b feature/nombre
```

Hacer commits frecuentes y atómicos siguiendo las convenciones.

Al terminar la feature:

```powershell
git checkout develop
git pull origin develop
git merge --no-ff feature/nombre
git push origin develop
```

Para preparar releases:

```powershell
git checkout develop
git checkout -b release/vX.Y.Z
# Ajustes menores y pruebas
git checkout main
git merge --no-ff release/vX.Y.Z
git tag vX.Y.Z
git push origin main --tags
git checkout develop
git merge --no-ff release/vX.Y.Z
```

Para hotfixes críticos:

```powershell
git checkout main
git checkout -b hotfix/nombre
# arreglar bug
git checkout main
git merge --no-ff hotfix/nombre
git tag vX.Y.Z+1
git push origin main --tags
git checkout develop
git merge --no-ff hotfix/nombre
```

## Recomendaciones adicionales

- Antes de hacer PR, asegúrate de `pull --rebase` para evitar conflictos.
- Utilizar reviewers en Pull Requests.
- Evitar commits que rompan la compilación del proyecto (Django y Next.js deben correr localmente).
- Mantener PRs pequeños y enfocados en una sola feature o bugfix.

## Migraciones

- docker exec -it drf_backend python manage.py makemigrations.
- docker exec -it drf_backend python manage.py migrate