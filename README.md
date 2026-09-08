# Biblioteca Diftel SJ / Telemática Hub

Un repositorio autogestionado, altamente optimizado y seguro para los estudiantes de Ingeniería Civil Telemática (Campus San Joaquín). Este proyecto separa la distribución pública de contenido estático de un pipeline de subida aislado y seguro, garantizando velocidad extrema y protección contra malware.

## 🚀 Arquitectura General

El proyecto utiliza una arquitectura de microservicios con **Docker Compose**:
- **Nginx**: Actúa como proxy inverso y servidor de altísimo rendimiento para archivos estáticos, la landing page, el sitio compilado de Quartz y la descarga de recursos pesados.
- **Django & PostgreSQL**: Operan gestionando la API del "Buzón Seguro", validando la identidad de los estudiantes mediante correos institucionales (PIN temporal OTP) y recibiendo los archivos. También proveen un endpoint dinámico con caché en RAM (latencia cero) para listar los recursos disponibles.
- **ClamAV & Watcher**: Un motor antivirus oficial y un microservicio en Python que monitorea en tiempo real las subidas temporales al buzón, escaneando, aislando amenazas y aprobando archivos limpios.
- **Quartz v4**: Generador de sitios estáticos especializado en tomar *Vaults* (bóvedas) de Obsidian y publicarlas de forma interactiva e interconectada en la web.

## 📂 Estructura de Directorios

* **`data/`**: Volúmenes montados y servidos directamente por Nginx para máxima velocidad.
  * `landing/`: Frontend principal (Página de Inicio y formulario del Buzón).
  * `quartz_public/`: Código HTML compilado generado por Quartz (despachado en `/quartz/`).
  * `recursos/`: Carpeta de almacenamiento masivo para archivos pesados (PDFs, ZIPs) servidos rápidamente vía `sendfile` de Nginx.
  * `buzon/`: Archivos en tránsito clasificados de forma automática en `tmp/`, `safe/` (limpios) y `quarantine/` (amenazas virales).
* **`quartz_app/`**: Proyecto base de Quartz y bóveda de Obsidian (ubicada en `quartz_app/content/`).
* **`django_app/`**: Código fuente de la API backend escrita en Django.
* **`nginx/`**: Configuración de enrutamiento web y reglas de seguridad para Nginx.
* **`clamav_watcher/`**: Microservicio en Python que sirve de puente entre Django y ClamAV.

## 🛠️ Flujo de Trabajo y Contribución

La comunidad puede aportar al repositorio a través de dos flujos distintos:

### Opción A: Aportar Material (El Buzón Seguro)
1. **Subida Autenticada:** Los estudiantes suben su material en la vista `/buzon/`, validando su identidad con su correo institucional.
2. **Escaneo Antivirus:** Django guarda el archivo temporalmente. El servicio `telematica-watcher` lo detecta y lo escanea a través de ClamAV.
3. **Clasificación Automática:** Si el archivo está limpio, se aprueba automáticamente y luego los administradores lo mueven a `data/recursos/`.

### Opción B: Escribir y Categorizar Apuntes (Vía GitHub + Obsidian)
1. **Explorador Dinámico:** En Quartz, la vista de `[[Archivos_Pesados]]` consume la API de Django para mostrar en tiempo real los recursos aprobados y listos para ser referenciados, proveyendo un botón para "Copiar Markdown".
2. **Edición Visual (Obsidian):** Clonas el repositorio y abres la carpeta local `quartz_app/content/` como tu Bóveda en **Obsidian**. Allí organizas tus archivos, enlazas ramos en las mallas y pegas los links hacia los archivos pesados.
3. **Publicación:** Subes tus cambios a GitHub y abres un Pull Request. El administrador revisa y ejecuta el script de despliegue.

## ⚙️ Despliegue y Configuración (Para Administradores)

1. **Requisitos:** Docker, Docker Compose y dependencias Node.js locales (npm) para compilar Quartz.
2. Clona el repositorio y configura tus variables de entorno para el backend y SMTP:
   ```bash
   cp env.example .env
   # Asegúrate de rellenar credenciales, configuraciones de correo y dominios.
   ```
3. Construye y levanta toda la infraestructura de contenedores:
   ```bash
   docker compose up -d --build
   ```
   *(Nota: ClamAV puede tardar unos minutos en iniciar por completo la primera vez, ya que debe descargar su pesada base de datos de firmas virales actualizadas).*
4. **Despliegue de Apuntes:** Ejecuta el script `./deploy.sh` en la raíz de tu terminal. Este script hace todo por ti:
   - Compila la bóveda de Obsidian en HTML interactivo.
   - Mueve y actualiza automáticamente los archivos públicos en Nginx.
   - Realiza un *commit* y *push* para respaldar tu trabajo.
