#!/bin/bash
# Script de Setup e Instalación del Sistema

set -e

echo "🎬 Configurando Generador de Clips Virales..."
echo ""

# Verificar Python
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 no encontrado. Por favor instálalo primero."
    exit 1
fi

echo "✓ Python 3.11 encontrado"

# Crear entorno virtual
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3.11 -m venv venv
fi

# Activar entorno
source venv/bin/activate || . venv\Scripts\activate

echo "✓ Entorno virtual activado"

# Instalar dependencias
echo "📚 Instalando dependencias..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "✓ Dependencias instaladas"

# Copiar archivo .env si no existe
if [ ! -f ".env" ]; then
    echo "⚙️  Creando archivo .env..."
    cp .env.example .env
    echo "⚠️  Por favor, edita .env con tus claves API"
fi

echo ""
echo "✅ Instalación completada"
echo ""
echo "Próximos pasos:"
echo "1. Edita .env con tus claves API"
echo "2. Ejecuta: docker-compose up -d"
echo "3. O ejecuta: celery -A celery_config worker & uvicorn app:app --reload"
echo ""
