# 🏠 Dashboard de Buscador y Resumen de Viviendas (Idealista & Fotocasa)

Un sistema completo y autónomo para recopilar, analizar y visualizar viviendas de **Idealista** y **Fotocasa**, desplegable gratuitamente en **GitHub Pages** con actualización automática diaria mediante **GitHub Actions**.

---

## ✨ Características Principales

- 💶 **Ordenación Inteligente al Acceder**:
  - **Precio: Menor a Mayor** (por defecto al abrir la app).
  - Precio: Mayor a Menor.
  - Precio por m² (€/m²).
  - Superficie útil (m²).
  - Fecha de publicación.
- 🔍 **Filtros Avanzados en Tiempo Real**:
  - Selector de Portal (Todos, Idealista, Fotocasa).
  - Rango de precio máximo dinámico.
  - Mínimo de habitaciones.
  - Búsqueda por texto (barrio, calle, características como "terraza", "piscina", "garaje").
- 🗺️ **Vista Dual (Tarjetas y Mapa Interactivo)**:
  - Cambia al instante entre la vista en rejilla y un **mapa interactivo (Leaflet.js)** con chinchetas numeradas y precio en cada ubicación.
- 🔗 **Acceso Directo al Anuncio Original**:
  - Cada tarjeta incluye un botón directo a la ficha del inmueble en Idealista o Fotocasa.
- ⭐ **Sistema de Favoritos y Notas Personales**:
  - Marca viviendas como favoritas para filtrarlas rápidamente.
  - Guarda notas privadas sobre cada piso (ej: *"Llamar a la agencia los martes"*), persistiéndose en el almacenamiento de tu navegador (`localStorage`).
- 🔄 **Actualización Diaria Automática**:
  - Flujo de trabajo de **GitHub Actions** que ejecuta el rastreador todos los días a las 08:00 AM UTC y actualiza los datos sin intervención humana.

---

## 📁 Estructura del Proyecto

```
viviendas-tracker/
├── index.html                  # Dashboard web interactivo (Tailwind CSS, Leaflet, JS)
├── scraper.py                  # Recolector en Python para Idealista y Fotocasa
├── data/
│   └── listings.json           # Base de datos JSON con las viviendas registradas
└── .github/
    └── workflows/
        └── update.yml          # Automatización de rastreo y despliegue en GitHub Pages
```

---

## 🚀 Guía de Despliegue en GitHub Pages (Paso a Paso)

### Opción 1: Crear un nuevo repositorio en GitHub (Recomendado)

1. **Crear Repositorio en GitHub**:
   - Entra en [GitHub.com](https://github.com) y haz clic en **New Repository**.
   - Nombre sugerido: `viviendas-tracker`.
   - Selecciona la opción **Public** (o Private si tienes plan con GitHub Actions para repos privados).

2. **Subir los Archivos**:
   - Inicializa el repositorio local y súbelo a GitHub:
   ```bash
   git init
   git add .
   git commit -m "feat: versión inicial del tracker de viviendas"
   git branch -M main
   git remote add origin https://github.com/TU-USUARIO/viviendas-tracker.git
   git push -u origin main
   ```

3. **Activar GitHub Pages**:
   - En tu repositorio de GitHub, ve a **Settings** (Configuración) -> **Pages**.
   - En **Build and deployment** -> **Source**, selecciona **GitHub Actions**.
   - ¡Listo! El workflow `.github/workflows/update.yml` empaquetará la web y te dará una URL pública tipo:
     `https://TU-USUARIO.github.io/viviendas-tracker/`

---

## ⚙️ Configuración del Rastreador (`scraper.py`)

### 1. Cambiar la zona de búsqueda
Abre el archivo `.github/workflows/update.yml` y modifica la línea donde se ejecuta el script:

```yaml
- name: 3. Ejecutar recolector de viviendas
  run: |
    python scraper.py --location "Madrid" --max-price 500000 --min-m2 60
```

### 2. Uso con API Oficial de Idealista (Opcional)
Si cuentas con credenciales de desarrollador de Idealista:
1. Ve a **Settings** -> **Secrets and variables** -> **Actions** en tu repositorio de GitHub.
2. Agrega los siguientes **Repository Secrets**:
   - `IDEALISTA_API_KEY`: Tu API Key.
   - `IDEALISTA_API_SECRET`: Tu API Secret.
3. El script detectará automáticamente las credenciales y consultará la API oficial de Idealista.

---

## 💻 Ejecución Local

Para probar el proyecto localmente en tu ordenador:

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU-USUARIO/viviendas-tracker.git
cd viviendas-tracker

# 2. Ejecutar el rastreador manualmente
python3 scraper.py --location "Madrid" --mock

# 3. Abrir el dashboard
# Puedes abrir directamente el archivo index.html en tu navegador
# O bien lanzar un servidor local ligero:
python3 -m http.server 8000
```
Abre tu navegador en `http://localhost:8000`.

---

## 🛠️ Tecnologías Utilizadas

- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript (ES6+), FontAwesome Icons, Leaflet.js (Mapas).
- **Backend / Scraping**: Python 3.11 (`urllib`, `json`, `datetime`).
- **CI/CD & Hosting**: GitHub Actions, GitHub Pages.
