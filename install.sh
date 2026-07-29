#!/bin/bash
set -e
echo "PrePress PDF Optimizer - Instalación"
echo "======================================"

# Instalar Homebrew si no existe
if ! command -v brew &> /dev/null; then
    echo "Instalando Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Instalar Ghostscript
echo "Instalando Ghostscript..."
brew install ghostscript 2>/dev/null || echo "Ya instalado"

# Instalar Python
echo "Configurando Python..."
python3 --version

# Crear virtual env
echo "Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate

# Instalar librerías
echo "Instalando librerías (espera 2-3 minutos)..."
pip install --upgrade pip > /dev/null 2>&1
pip install PyQt5==5.15.9 Pillow==10.0.1 pypdf==4.0.1 reportlab==4.0.9 > /dev/null 2>&1

echo ""
echo "✅ ¡INSTALACIÓN COMPLETADA!"
echo ""
echo "Para ejecutar la aplicación:"
echo "  cd ~/Documents/PrePressApp"
echo "  ./run.sh"
echo ""
