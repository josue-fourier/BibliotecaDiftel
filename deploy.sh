#!/bin/bash
set -e

echo "🚀 Iniciando compilación de Quartz..."

# Moverse al directorio de Quartz
cd quartz_app

# Instalar dependencias si no existen
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependencias de Quartz (esto tomará un momento)..."
    npm install
fi

# Construir sitio estático
echo "🔨 Compilando archivos Markdown..."
rm -rf .quartz-cache
npx quartz build

# Volver a la raíz del proyecto
cd ..

# Copiar los archivos generados a la carpeta pública del servidor web
echo "📂 Moviendo HTMLs generados a data/quartz_public/..."
rm -rf data/quartz_public/*
cp -r quartz_app/public/* data/quartz_public/

# Subir cambios a Git
echo "🔄 Subiendo cambios al repositorio..."
git add quartz_app/content/ data/quartz_public/
git commit -m "docs(quartz): actualizar apuntes y build de HTML" || echo "No hay cambios nuevos para commitear."
git push

echo "✅ ¡Despliegue completado! Tu biblioteca ha sido actualizada exitosamente."
