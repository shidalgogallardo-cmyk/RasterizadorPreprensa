#!/bin/bash

# Rasterizador Preprensa - Instalación macOS
# Script automatizado para M1/M2/M3 Pro

echo "🚀 Instalador - Rasterizador Preprensa v7.0"
echo "==========================================="

# 1. Verificar Homebrew
if ! command -v brew &> /dev/null; then
    echo "📦 Instalando Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 2. Instalar pdftoppm (poppler)
if ! command -v pdftoppm &> /dev/null; then
    echo "📥 Instalando poppler (pdftoppm)..."
    brew install poppler
else
    echo "✓ poppler ya está instalado"
fi

# 3. Crear directorio de la app
APP_DIR="$HOME/RasterizadorPreprensa"
if [ ! -d "$APP_DIR" ]; then
    mkdir -p "$APP_DIR"
    echo "📁 Directorio creado: $APP_DIR"
fi

# 4. Copiar archivos
echo "📋 Copiando archivos..."
cp rasterizador_preprensa.py "$APP_DIR/"
cp requirements.txt "$APP_DIR/"
cp icono.icns "$APP_DIR/" 2>/dev/null || echo "⚠️ Icono no encontrado (opcional)"
cp WAN-IFRAnewspaper26v5.icc "$APP_DIR/" 2>/dev/null || echo "⚠️ Perfil ICC no encontrado (opcional)"

# 5. Crear venv
echo "🐍 Creando virtual environment..."
cd "$APP_DIR"
python3 -m venv venv

# 6. Activar venv e instalar dependencias
echo "📚 Instalando dependencias Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 7. Hacer ejecutable
chmod +x rasterizador_preprensa.py

# 8. Crear script de lanzamiento
cat > "$APP_DIR/ejecutar.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 rasterizador_preprensa.py
EOF

chmod +x "$APP_DIR/ejecutar.sh"

echo ""
echo "✓ INSTALACIÓN COMPLETADA"
echo ""
echo "Para ejecutar la aplicación:"
echo "  cd $APP_DIR"
echo "  ./ejecutar.sh"
echo ""
echo "O desde cualquier lugar:"
echo "  $APP_DIR/ejecutar.sh"
