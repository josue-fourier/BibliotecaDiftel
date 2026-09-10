# Contexto de Arquitectura: Biblioteca Diftel

## Estado Estable y Servicios (Septiembre 2026)
* **Nginx:** Proxy inverso principal (servidor web). Sirve la landing page en `/`, archivos estáticos en `/recursos/` (optimizado) y redirige a los demás servicios.
* **Docmost (Wiki):** Reemplazó a Quartz como gestor de conocimiento. **No soporta subrutas**. Se sirve a través de un túnel Cloudflare directamente al contenedor (`telematica-docmost:3000`) mediante el dominio `wiki-diftel.josnic.cl`.
* **Filebrowser Quantum:** Reemplazó a FileGator. Sirve como administrador de archivos privado. Expuesto en la subruta `/filebrowser` por Nginx. Usa la variable de entorno `FB_BASEURL=/filebrowser`.
* **Buzón Seguro (Django + Postgres):** Backend API en `/buzon/api/`. Valida identidad por correo institucional (@usm.cl / @sansano.usm.cl) mediante PIN OTP.
* **Seguridad y Notificaciones:** ClamAV & Watcher escanean archivos subidos. n8n & Ntfy envían notificaciones push.

## Reglas Operativas Críticas
1. **No ejecutar comandos de Docker localmente:** NUNCA ejecutes `docker compose up`, `docker start` o comandos que alteren el estado de los contenedores locales. El usuario administra el ciclo de vida de los contenedores manualmente. Puedes editar `docker-compose.yml`, pero el despliegue final es responsabilidad del usuario.
2. **Subrutas vs Subdominios:** Si agregas una aplicación Node.js/React moderna (como Docmost), asume que no soporta subrutas en Nginx de manera nativa y requiere subdominios. Para apps que sí lo soportan (como Filebrowser), asegúrate de pasar la variable de entorno `BASEURL` correcta.
