---
title: Explorador de Archivos
---
# 📁 Explorador de Recursos Pesados

Aquí puedes encontrar todos los archivos pesados (mayormente ZIPs, RARs o PDFs pesados) que han sido aprobados por nuestro sistema de seguridad y están listos para ser referenciados en tus apuntes.

Usa el botón **Copiar Markdown** para pegar el enlace directamente en tus guías de estudio.

<div id="recursos-container" style="margin-top: 2rem;">
    <p>⏳ Cargando recursos desde el servidor...</p>
</div>

<script>
    async function loadRecursos() {
        const container = document.getElementById('recursos-container');
        try {
            // Se asume que Quartz y Django están en el mismo dominio
            const response = await fetch('/buzon/api/recursos');
            if (!response.ok) {
                throw new Error('Error al obtener los recursos');
            }
            const data = await response.json();
            
            if (!data.files || data.files.length === 0) {
                container.innerHTML = '<p>No hay recursos disponibles en este momento.</p>';
                return;
            }

            let html = `
            <table style="width: 100%; text-align: left; border-collapse: collapse;">
                <thead>
                    <tr style="border-bottom: 2px solid #ccc;">
                        <th style="padding: 10px;">Archivo</th>
                        <th style="padding: 10px;">Tamaño</th>
                        <th style="padding: 10px;">Fecha</th>
                        <th style="padding: 10px;">Acción</th>
                    </tr>
                </thead>
                <tbody>
            `;

            data.files.forEach(file => {
                // Link is root-relative (e.g., /recursos/file.pdf). We make it absolute for the markdown to ensure it always works.
                const absoluteLink = window.location.origin + file.url;
                const encodedLink = encodeURI(absoluteLink);
                const basename = file.name.split('/').pop();
                const markdownText = `[${basename}](${encodedLink})`;
                
                html += `
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px;"><strong><a href="${absoluteLink}" target="_blank">${file.name}</a></strong></td>
                        <td style="padding: 10px;">${file.size}</td>
                        <td style="padding: 10px;">${file.date}</td>
                        <td style="padding: 10px;">
                            <button 
                                onclick="navigator.clipboard.writeText('${markdownText}').then(() => { this.innerText = '¡Copiado!'; setTimeout(() => this.innerText = 'Copiar Markdown', 2000); })"
                                style="background-color: #004B87; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; font-size: 0.9em;">
                                Copiar Markdown
                            </button>
                        </td>
                    </tr>
                `;
            });

            html += `</tbody></table>`;
            container.innerHTML = html;

        } catch (error) {
            console.error(error);
            container.innerHTML = '<p style="color: red;">❌ Hubo un error cargando el explorador de archivos. Intenta más tarde.</p>';
        }
    }

    // Load when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadRecursos);
    } else {
        loadRecursos();
    }
</script>
