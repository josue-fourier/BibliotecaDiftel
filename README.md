# Biblioteca Diftel / Telemática Hub

Un repositorio autogestionado, altamente optimizado y seguro para los estudiantes de Ingeniería Civil Telemática de la Universidad Técnica Federico Santa María. Este proyecto separa la distribución pública de contenido estático de un pipeline de subida aislado y seguro, garantizando velocidad extrema y protección contra malware.

## 🚀 Arquitectura General

El proyecto utiliza una arquitectura de microservicios con **Docker Compose**:
- **Nginx**: Actúa como proxy inverso y servidor de altísimo rendimiento para archivos estáticos, la landing page, el sitio compilado de Quartz y la descarga de recursos pesados.
- **Django & PostgreSQL**: Operan de forma *headless* (sin frontend propio) gestionando la API del "Buzón Seguro", validando la identidad de los estudiantes mediante correos institucionales `@usm.cl` (PIN temporal OTP) y recibiendo los archivos.
- **ClamAV & Watcher**: Un motor antivirus oficial y un microservicio en Python que monitorea en tiempo real las subidas temporales al buzón, escaneando, aislando amenazas y aprobando archivos limpios.
- **Quartz v4**: Generador de sitios estáticos especializado en tomar *Vaults* (bóvedas) de Obsidian y publicarlas de forma interactiva e interconectada en la web.

## 📂 Estructura de Directorios

* **`data/`**: Volúmenes montados y servidos directamente por Nginx para máxima velocidad.
  * `landing/`: Frontend principal (Página de Inicio y formulario del Buzón).
  * `quartz_public/`: Código HTML compilado generado por Quartz (despachado en `/quartz/`).
  * `recursos/`: Carpeta de almacenamiento masivo para archivos pesados (PDFs, ZIPs) servidos rápidamente vía `sendfile` de Nginx (despachados en `/recursos/`).
  * `buzon/`: Archivos en tránsito clasificados de forma automática en `tmp/`, `safe/` (limpios) y `quarantine/` (amenazas virales).
* **`quartz_app/`**: Proyecto base de Quartz y bóveda de Obsidian (ubicada en `quartz_app/content/`).
* **`django_app/`**: Código fuente de la API backend escrita en Django.
* **`nginx/`**: Configuración de enrutamiento web y reglas de seguridad para Nginx.
* **`clamav_watcher/`**: Microservicio en Python que sirve de puente entre Django y ClamAV.

## 🛠️ Flujo de Trabajo (Operación Diaria)

La magia de este repositorio reside en cómo los aportes fluyen desde el estudiante hacia la web publicada:

### 1. Recepción y Seguridad (El Buzón)
1. **Subida Autenticada:** Los estudiantes suben su material en la vista `/buzon/`, validando su identidad con su correo institucional (solicitud de PIN OTP).
2. **Escaneo Antivirus:** Django guarda el archivo en `data/buzon/tmp/`. El servicio `telematica-watcher` lo detecta al instante y lo escanea a través del socket TCP de ClamAV.
3. **Clasificación Automática:** Si el archivo está limpio, se mueve automáticamente a `data/buzon/safe/`. Si contiene firmas maliciosas, queda totalmente aislado y bloqueado en `data/buzon/quarantine/`.

### 2. Gestión de Contenidos y Publicación (La Bóveda)
Para integrar nuevos aportes validados al repositorio público:
1. **Aprobar Aportes:** El equipo administrativo revisa la carpeta `data/buzon/safe/` y mueve los archivos que valgan la pena hacia su ubicación definitiva y categorizada en `data/recursos/[ramo]/archivo.pdf`.
2. **Edición Visual (Obsidian):** Abres la carpeta local `quartz_app/content/` como tu Bóveda (Vault) en la aplicación **Obsidian**. Allí organizas tus archivos de texto, enlazas ramos en las mallas con `[[wikilinks]]` y añades links web estándar hacia los archivos pesados usando la ruta ultrarrápida (ej: `[Descargar Guía de Python](/recursos/inf119/guia.pdf)`).
3. **Despliegue Automático (One-Click):** Ejecutas el script `./deploy.sh` en la raíz de tu terminal. Este script hace todo por ti:
   - Compila la bóveda de Obsidian en HTML interactivo (usando Quartz).
   - Mueve y actualiza automáticamente los archivos en `data/quartz_public/` (y quedan online instantáneamente).
   - Realiza un *commit* y *push* para respaldar tu trabajo en el repositorio Git.

## ⚙️ Despliegue y Configuración

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
4. ¡El ecosistema está listo! Entra a tu localhost o dominio y usa el Buzón, y edita el contenido con tu Bóveda de Quartz para darle forma.
