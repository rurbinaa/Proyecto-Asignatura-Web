# Flujo de Trabajo con Docker

Este documento describe los comandos básicos para trabajar con contenedores Docker, incluyendo cómo acceder a terminales, ver logs y reiniciar servicios. Estos comandos son aplicables a cualquier proyecto que use Docker Compose.

## Acceder a la Terminal de un Contenedor

### Comando Básico
```bash
docker exec -it <nombre_del_contenedor> bash
```

### Ejemplos
```bash
# Acceder al contenedor de la aplicación backend
docker exec -it proyecto-asignatura-web_backend_1 bash

# Acceder al contenedor de la base de datos PostgreSQL
docker exec -it proyecto-asignatura-web_db_1 bash

# Usar sh en lugar de bash si bash no está disponible
docker exec -it proyecto-asignatura-web_backend_1 sh
```

### Parámetros
- `-i`: Mantiene STDIN abierto (interactivo)
- `-t`: Asigna un pseudo-TTY (terminal)
- `bash`: Shell a usar (puede ser `sh`, `zsh`, etc.)

## Ver Logs de Contenedores

### Ver Logs en Tiempo Real
```bash
docker logs -f <nombre_del_contenedor>
```

### Ver Últimas Líneas de Logs
```bash
# Últimas 100 líneas
docker logs --tail 100 <nombre_del_contenedor>

# Últimas líneas y seguir en tiempo real
docker logs --tail 100 -f <nombre_del_contenedor>
```

### Ver Logs de Todos los Contenedores
```bash
# Logs de todos los servicios definidos en docker-compose.yml
docker-compose logs

# Logs en tiempo real de todos los servicios
docker-compose logs -f

# Logs de un servicio específico
docker-compose logs backend
docker-compose logs db
```

### Ejemplos Prácticos
```bash
# Ver logs del backend en tiempo real
docker logs -f proyecto-asignatura-web_backend_1

# Ver logs de la base de datos, últimas 50 líneas
docker logs --tail 50 proyecto-asignatura-web_db_1

# Ver logs de todos los servicios desde el inicio
docker-compose logs --tail="all"
```

## Reiniciar Servicios Específicos

### Reiniciar un Servicio con Docker Compose
```bash
docker-compose restart <nombre_del_servicio>
```

### Reiniciar Todos los Servicios
```bash
docker-compose restart
```

### Reiniciar y Reconstruir un Servicio
```bash
# Reinicia y reconstruye si hay cambios en el Dockerfile
docker-compose up --build <nombre_del_servicio>

# Reconstruir todos los servicios
docker-compose up --build
```

### Detener y Volver a Iniciar
```bash
# Detener un servicio específico
docker-compose stop backend

# Iniciar un servicio específico
docker-compose start backend

# Detener todos los servicios
docker-compose down

# Iniciar todos los servicios
docker-compose up -d
```

## Comandos Útiles Adicionales

### Listar Contenedores en Ejecución
```bash
docker ps
```

### Listar Todos los Contenedores (incluyendo detenidos)
```bash
docker ps -a
```

### Ver Estado de Servicios de Docker Compose
```bash
docker-compose ps
```

### Inspeccionar un Contenedor
```bash
# Ver configuración detallada del contenedor
docker inspect <nombre_del_contenedor>

# Ver variables de entorno
docker exec <nombre_del_contenedor> env
```

### Copiar Archivos desde/hacia Contenedores
```bash
# Copiar desde contenedor a host
docker cp <contenedor>:<ruta_dentro_contenedor> <ruta_host>

# Copiar desde host a contenedor
docker cp <ruta_host> <contenedor>:<ruta_dentro_contenedor>
```

### Ver Uso de Recursos
```bash
# Ver uso de CPU, memoria, etc.
docker stats

# Ver uso de disco
docker system df
```

## Solución de Problemas Comunes

### Contenedor No Responde
```bash
# Ver logs de error
docker logs <contenedor>

# Reiniciar el contenedor
docker-compose restart <servicio>

# Si no funciona, reconstruir
docker-compose up --build --force-recreate <servicio>
```

### Puerto Ya en Uso
```bash
# Ver qué proceso usa el puerto
lsof -i :8080

# Matar el proceso
kill -9 <PID>
```

### Limpiar Espacio en Disco
```bash
# Remover contenedores detenidos
docker container prune

# Remover imágenes no utilizadas
docker image prune

# Limpiar todo (cuidado, elimina datos no persistentes)
docker system prune
```

## Mejores Prácticas

1. **Usar Nombres Descriptivos**: Nombra tus servicios en `docker-compose.yml` de manera clara (ej. `backend`, `db`, `frontend`).

2. **Logs Persistentes**: Configura logging drivers para persistir logs importantes.

3. **Monitoreo**: Usa `docker stats` para monitorear recursos en producción.

4. **Backups**: Antes de reiniciar servicios críticos, asegúrate de tener backups de datos.

5. **Versionado**: Etiqueta tus imágenes con versiones específicas para evitar problemas de compatibilidad.</content>
<parameter name="filePath">/home/frandev/Documentos/Proyecto-Asignatura-Web/docs/docker_workflow.md