# Compilar Rasterizador de PDFs como app de macOS vía GitHub Actions

No tengo acceso directo a tu cuenta de GitHub, así que sigue estos pasos manualmente (5-10 min):

## 1. Estructura de tu repositorio

Sube estos archivos a la RAÍZ de tu repo (mismo nivel):

```
tu-repo/
├── rasterizador_pdfs.py
├── icono.icns
├── WAN-IFRAnewspaper26v5.icc
├── requirements.txt
└── .github/
    └── workflows/
        └── build-macos.yml
```

Los 3 primeros archivos ya los tienes (te los pasé antes). `requirements.txt` y el workflow te los entrego ahora mismo.

## 2. Subir los archivos

```bash
cd tu-repo
cp ~/Downloads/rasterizador_pdfs.py .
cp ~/Downloads/requirements.txt .
mkdir -p .github/workflows
cp ~/Downloads/build-macos.yml .github/workflows/

git add .
git commit -m "Agregar app y workflow de compilación macOS"
git push
```

## 3. Verificar la compilación

En GitHub: pestaña **Actions** de tu repo → verás "Build macOS App" corriendo automáticamente al hacer push. Tarda ~3-5 minutos.

## 4. Descargar el resultado

Cuando termine (check verde ✓):
- Entra al run finalizado
- Sección **Artifacts** al final de la página
- Descarga `RasterizadorDePDFs-macOS.zip` → contiene el `.app` y el `.dmg` listos para usar

## 5. (Opcional) Crear una Release oficial

Si quieres una versión "v1.0" descargable desde la página principal del repo:

```bash
git tag v1.0
git push origin v1.0
```

Esto dispara el mismo workflow y además publica el `.dmg` como Release automáticamente.

## Notas importantes

- El runner de GitHub (`macos-latest`) NO está firmado con tu certificado de Apple Developer, así que al abrir la app por primera vez macOS mostrará advertencia de "desarrollador no identificado". Clic derecho → Abrir → Abrir, la primera vez.
- Si tu perfil ICC o ícono tienen otro nombre exacto, ajusta las líneas `--icon` y `--add-data` del workflow para que coincidan.
