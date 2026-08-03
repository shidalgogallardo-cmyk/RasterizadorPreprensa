# Rasterizador Preprensa v7.0 - Guía de Instalación macOS

## Requisitos

- macOS 11+
- M1/M2/M3 Pro (compatible con Apple Silicon)
- Python 3.8+
- Homebrew

## Instalación Rápida (Recomendado)

### 1. Descargar archivos
```bash
cd ~/Downloads
# Descargar o clonar:
# - rasterizador_preprensa.py
# - requirements.txt
# - install_macos.sh
# - WAN-IFRAnewspaper26v5.icc (opcional)
```

### 2. Ejecutar instalador
```bash
chmod +x install_macos.sh
./install_macos.sh
```

El script instalará automáticamente:
- ✓ Homebrew (si no está)
- ✓ poppler (pdftoppm)
- ✓ Python venv
- ✓ Dependencias Python
- ✓ Directorio ~/RasterizadorPreprensa

### 3. Ejecutar la app
```bash
~/RasterizadorPreprensa/ejecutar.sh
```

---

## Instalación Manual

Si prefieres configurar manualmente:

### 1. Instalar Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Instalar poppler
```bash
brew install poppler
```

Verifica que funciona:
```bash
pdftoppm -v
```

### 3. Crear directorio de la app
```bash
mkdir -p ~/RasterizadorPreprensa
cd ~/RasterizadorPreprensa
```

### 4. Copiar archivos
```bash
# Copia estos archivos al directorio:
cp rasterizador_preprensa.py ~/RasterizadorPreprensa/
cp requirements.txt ~/RasterizadorPreprensa/
cp WAN-IFRAnewspaper26v5.icc ~/RasterizadorPreprensa/  # opcional
```

### 5. Crear virtual environment
```bash
cd ~/RasterizadorPreprensa
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Crear script de ejecución
```bash
cat > ejecutar.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 rasterizador_preprensa.py
EOF

chmod +x ejecutar.sh
```

### 7. Ejecutar
```bash
./ejecutar.sh
```

---

## Uso de la Aplicación

### Interfaz

1. **Paso 1: Carga tu PDF**
   - Arrastra un PDF a la zona de carga O haz clic para seleccionar
   - Las medidas se detectan automáticamente

2. **Paso 2: Configura parámetros**
   - **Perfil ICC:** WAN-IFRAnewspaper26v5 o Perfil predeterminado del PDF
   - **Resolución:** 200, 250 o 300 DPI

3. **Paso 3: Rasteriza**
   - Haz clic en "✨ Rasterizar PDF"
   - El archivo se guarda en ~/Downloads/
   - Muestra medidas, tamaño y tiempo de procesamiento

### Ejemplo de flujo
```
1. Cargar: periódico.pdf (1.9 MB)
   ↓ Detecta: 28.89 × 27.94 cm
2. Configurar: 300 DPI, WAN-IFRAnewspaper26v5
3. Procesar → periódico_rasterizado.pdf (2.7 MB)
```

---

## Solución de Problemas

### Error: "pdftoppm no encontrado"
```bash
brew install poppler
pdftoppm -v  # Verifica
```

### Error: "tkinterdnd2 no instala"
Alternativa: instalar sistema:
```bash
brew install python-tk
pip install --force-reinstall tkinterdnd2
```

### La app se cierra sin cargar
Verifica Python:
```bash
python3 --version  # Debe ser 3.8+
which pdftoppm
```

### Permisos denegados
```bash
chmod +x rasterizador_preprensa.py
chmod +x ejecutar.sh
```

---

## Especificaciones

| Parámetro | Valores |
|-----------|---------|
| Entrada | PDF vectorial |
| Salida | PDF rasterizado |
| Resolución | 200, 250, 300 DPI |
| Perfil ICC | WAN-IFRAnewspaper26v5 o Predeterminado |
| Modo color | CMYK |
| Medidas | Detectadas automáticamente |
| Ubicación salida | ~/Downloads/ |

---

## Próximas Versiones

- v7.1: Soporte para perfiles ICC personalizados
- v8.0: Adaptación para Windows
- v9.0: Versión web

---

## Contacto & Soporte

Problemas o sugerencias: consulta la documentación técnica.

**Versión:** 7.0  
**Plataforma:** macOS M1/M2/M3 Pro  
**Estado:** Beta estable
