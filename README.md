# Proyecto-Asignatura-Web

# Guia de instalacion de Docker

## Requisitos previos

Asegurar la instalacion de las siguientes herramientas en el equipo antes de comenzar

1. **[Git](https://git-scm.com/install/): ** Descargar e instalar Git para clonar el repositorio.
2. **[Docker Desktop](https://www.docker.com/products/docker-desktop/): ** Instalar la herramienta de Docker para levantar los contenedores del entorno de desarrollo. Iniciar el motor de Docker antes de avanzar.

---

## Intruccion de Instalacion y Ejecucion

### Paso 1: Clonar el repositorio

Abrir la terminal y ejecutar el siguiente comando para descargar el repositorio:

```powershell
git clone [https://github.com/rurbinaa/Proyecto-Asignatura-Web](https://github.com/rurbinaa/Proyecto-Asignatura-Web)
```

Ingresar a la carpeta principal del proyecto una vez finalizada la descarga:

```powershell
cd Proyecto-Asignatura-Web
```

### Paso 2: Configurar variables de entorno

Configurar las credenciales necesarias para el funcionamiento del proyecto creando una copia del archivo de ejemplo:

```powershell
cp .env.example .env
```

*(Nota: Mantener las variables preconfiguradas para el desarrollo local; se recomienda no modificar los valores para el primer arranque).*

### Paso 3: Levantar los servicios con Docker

Comprobar que Docker Desktop se encuentre en ejecución en segundo plano. Ejecutar el siguiente comando en la terminal para construir las imágenes y levantar los contenedores:

```powershell
docker compose up --build
```

*(Nota: Esperar unos minutos durante la primera ejecución mientras Docker descarga las imágenes base e instala las dependencias necesarias).*

### Paso 4: Acceder a la plataforma

Acceder a la aplicación desde el navegador una vez que la terminal confirme que los servicios están en ejecución:

* **Frontend (Interfaz Gráfica):** Ingresar a [http://localhost:5173](http://localhost:5173)
* **Backend (API REST):** Ingresar a [http://localhost:8000](http://localhost:8000)

---

## Detener los servicios

Detener los contenedores de forma segura sin borrar los datos de la base de datos. Abrir una nueva terminal en la raíz del proyecto (o presionar `Ctrl + C` en la terminal en ejecución) y ejecutar el siguiente comando:

```powershell
docker compose down
```
