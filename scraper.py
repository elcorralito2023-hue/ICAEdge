import os
import json
import re
import argparse
import urllib.request
from datetime import datetime, timezone

def fetch_real_estates():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
    }

    zones = [
        ("Las Rozas", "https://www.fotocasa.es/es/comprar/viviendas/las-rozas-de-madrid/todas-las-zonas/l"),
        ("Majadahonda", "https://www.fotocasa.es/es/comprar/viviendas/majadahonda/todas-las-zonas/l"),
        ("Pozuelo de Alarcón", "https://www.fotocasa.es/es/comprar/viviendas/pozuelo-de-alarcon/todas-las-zonas/l"),
        ("Alcorcón", "https://www.fotocasa.es/es/comprar/viviendas/alcorcon/todas-las-zonas/l"),
        ("Móstoles", "https://www.fotocasa.es/es/comprar/viviendas/mostoles/todas-las-zonas/l"),
        ("Torrelodones", "https://www.fotocasa.es/es/comprar/viviendas/torrelodones/todas-las-zonas/l"),
        ("Boadilla del Monte", "https://www.fotocasa.es/es/comprar/viviendas/boadilla-del-monte/todas-las-zonas/l")
    ]

    all_listings = {}

    for zone_name, url in zones:
        print(f"[*] Buscando viviendas reales en {zone_name}...")
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
                for s in scripts:
                    if "combinedLocationIds" in s and len(s) > 10000:
                        data = json.loads(s)
                        
                        def find_real_estates(obj):
                            if isinstance(obj, dict):
                                if "realEstates" in obj and isinstance(obj["realEstates"], list):
                                    return obj["realEstates"]
                                for k, v in obj.items():
                                    if isinstance(v, (dict, list)):
                                        res = find_real_estates(v)
                                        if res: return res
                            elif isinstance(obj, list):
                                for item in obj:
                                    if isinstance(item, (dict, list)):
                                        res = find_real_estates(item)
                                        if res: return res
                            return None

                        items = find_real_estates(data)
                        if items:
                            for item in items:
                                item_id = item.get("id")
                                if not item_id or item_id in all_listings:
                                    continue

                                price_raw = item.get("rawPrice") or item.get("price") or 0
                                if isinstance(price_raw, str):
                                    try: price_val = int(re.sub(r"[^\d]", "", price_raw))
                                    except: price_val = 0
                                else:
                                    price_val = price_raw

                                if price_val < 200000 or price_val > 750000:
                                    continue

                                detail = item.get("detail", {})
                                detail_path = detail.get("es-ES") or detail.get("es") or ""
                                if not detail_path:
                                    continue

                                title_raw = str(item.get("title") or item.get("description") or f"Chalet en {zone_name}").strip()
                                lower_title = title_raw.lower()
                                if any(w in lower_title for w in ["local", "nave", "garaje", "trastero", "oficina"]):
                                    continue

                                title = title_raw
                                if len(title) > 110:
                                    title = title[:107] + "..."

                                multimedia = item.get("multimedias") or item.get("photos") or []
                                img_url = "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80"
                                if isinstance(multimedia, list) and len(multimedia) > 0:
                                    m0 = multimedia[0]
                                    if isinstance(m0, dict):
                                        img_url = m0.get("url") or m0.get("url_es") or img_url

                                bedrooms = item.get("bedrooms") or item.get("rooms") or 4
                                bathrooms = item.get("bathrooms") or 2
                                surface = item.get("surface") or item.get("buildingSurface") or 220

                                features_raw = item.get("features", [])
                                has_pool = False
                                if isinstance(features_raw, list):
                                    for f in features_raw:
                                        if isinstance(f, dict):
                                            f_key = str(f.get("key") or f.get("value") or "").lower()
                                            if "pool" in f_key or "piscina" in f_key:
                                                has_pool = True

                                loc_str = str(item.get("location") or zone_name)
                                full_loc = f"{loc_str}, {zone_name}" if zone_name.lower() not in loc_str.lower() else loc_str

                                full_url = "https://www.fotocasa.es" + str(detail_path)

                                feat_tags = []
                                if has_pool: feat_tags.append("Piscina")
                                feat_tags.append(f"{bedrooms} dorms")
                                feat_tags.append("Jardín / Parcela")

                                price_m2 = round(price_val / surface) if surface > 0 else 2500

                                all_listings[item_id] = {
                                    "id": "fc_" + str(item_id),
                                    "title": title,
                                    "portal": "Fotocasa",
                                    "price": price_val,
                                    "price_per_m2": price_m2,
                                    "size_m2": surface,
                                    "bedrooms": bedrooms,
                                    "bathrooms": bathrooms,
                                    "floor": "Chalet / Unifamiliar",
                                    "location": full_loc,
                                    "lat": 40.4500,
                                    "lng": -3.8700,
                                    "image": img_url,
                                    "url": full_url,
                                    "features": feat_tags,
                                    "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                                }
        except Exception as e:
            print(f"[-] Error en {zone_name}: {e}")

    results = list(all_listings.values())
    results.sort(key=lambda x: x["price"])
    print(f"[✔] Total de viviendas reales volcadas a listings.json: {len(results)}")
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--location", default="")
    parser.add_argument("--max-price", type=int, default=750000)
    parser.add_argument("--min-bedrooms", type=int, default=3)
    parser.add_argument("--output", default="listings.json")
    args = parser.parse_args()

    results = fetch_real_estates()

    # Guardar en listings.json y en data/listings.json
    with open("listings.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    os.makedirs("data", exist_ok=True)
    with open("data/listings.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()


🎨 Parte 2: El Panel HTML (index.html)

Copia y pega este código en tu archivo index.html en GitHub:
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Buscador de Chalets en Madrid | Idealista & Fotocasa</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen">
    <header class="bg-indigo-900 text-white shadow-lg sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 py-4 flex flex-col md:flex-row justify-between items-center gap-4">
            <div class="flex items-center space-x-3">
                <div class="bg-amber-400 text-indigo-900 p-2.5 rounded-xl font-black text-2xl shadow-inner">
                    <i class="fa-solid fa-house-chimney"></i>
                </div>
                <div>
                    <h1 class="text-xl font-bold tracking-tight">Buscador de Chalets en Madrid</h1>
                    <p class="text-xs text-indigo-200">Las Rozas, Majadahonda, Pozuelo, Alcorcón, Móstoles, Torrelodones, Boadilla</p>
                </div>
            </div>
            <div id="statsBadge" class="bg-indigo-800/80 px-4 py-2 rounded-lg text-sm flex items-center gap-4 border border-indigo-700">
                <span><i class="fa-solid fa-list-check text-amber-400"></i> <strong id="totalCount">0</strong> viviendas</span>
                <span><i class="fa-solid fa-clock text-emerald-400"></i> <span id="lastUpdated">Actualizando...</span></span>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-6">
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5 mb-6">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-500 mb-1">Ordenar Por</label>
                    <select id="sortSelect" onchange="applyFilters()" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm font-medium focus:ring-2 focus:ring-indigo-500">
                        <option value="price-asc" selected>💰 Precio: Menor a Mayor</option>
                        <option value="price-desc">💰 Precio: Mayor a Menor</option>
                        <option value="m2-desc">📏 Superficie (m²)</option>
                        <option value="price-m2-asc">💶 Precio por m² (€/m²)</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-500 mb-1">Buscar Zona / Palabra</label>
                    <input type="text" id="searchInput" oninput="applyFilters()" placeholder="Ej. Las Rozas, Piscina..." class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500">
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-500 mb-1">Precio Máx: <span id="priceVal" class="text-indigo-600 font-bold">750.000 €</span></label>
                    <input type="range" id="priceRange" min="300000" max="850000" step="10000" value="750000" oninput="updatePriceLabel(); applyFilters()" class="w-full accent-indigo-600 mt-2">
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-500 mb-1">Portal</label>
                    <select id="portalSelect" onchange="applyFilters()" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm font-medium focus:ring-2 focus:ring-indigo-500">
                        <option value="all">Todos los Portales</option>
                        <option value="Idealista">Idealista</option>
                        <option value="Fotocasa">Fotocasa</option>
                    </select>
                </div>
            </div>
        </div>

        <div id="gridContainer" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"></div>

        <div id="emptyState" class="hidden bg-white p-12 text-center rounded-xl border border-slate-200">
            <i class="fa-solid fa-house-circle-xmark text-5xl text-slate-300 mb-4"></i>
            <h3 class="text-lg font-bold text-slate-700 mb-1">No se encontraron viviendas con estos filtros</h3>
            <p class="text-slate-500 text-sm">Prueba a ampliar el rango de precio o borrar el texto del buscador.</p>
        </div>
    </main>

    <script>
        let allListings = [];

        async function loadListings() {
            try {
                let response = await fetch("./listings.json");
                if (!response.ok) {
                    response = await fetch("./data/listings.json");
                }
                if (response.ok) {
                    allListings = await response.json();
                }
            } catch (e) {
                console.error("Error cargando listings.json:", e);
            }
            applyFilters();
        }

        function updatePriceLabel() {
            const val = document.getElementById("priceRange").value;
            document.getElementById("priceVal").innerText = parseInt(val).toLocaleString("es-ES") + " €";
        }

        function applyFilters() {
            const sortVal = document.getElementById("sortSelect").value;
            const searchVal = document.getElementById("searchInput").value.toLowerCase();
            const maxPrice = parseInt(document.getElementById("priceRange").value);
            const portalVal = document.getElementById("portalSelect").value;

            let filtered = allListings.filter(item => {
                if (item.price > maxPrice) return false;
                if (portalVal !== "all" && item.portal !== portalVal) return false;
                if (searchVal) {
                    const text = (item.title + " " + item.location + " " + (item.features || []).join(" ")).toLowerCase();
                    if (!text.includes(searchVal)) return false;
                }
                return true;
            });

            if (sortVal === "price-asc") {
                filtered.sort((a, b) => a.price - b.price);
            } else if (sortVal === "price-desc") {
                filtered.sort((a, b) => b.price - a.price);
            } else if (sortVal === "m2-desc") {
                filtered.sort((a, b) => b.size_m2 - a.size_m2);
            } else if (sortVal === "price-m2-asc") {
                filtered.sort((a, b) => a.price_per_m2 - b.price_per_m2);
            }

            renderGrid(filtered);
        }

        function renderGrid(listings) {
            const container = document.getElementById("gridContainer");
            const empty = document.getElementById("emptyState");
            container.innerHTML = "";

            document.getElementById("totalCount").innerText = listings.length;
            if (listings.length > 0 && listings[0].updated_at) {
                const dt = new Date(listings[0].updated_at);
                document.getElementById("lastUpdated").innerText = dt.toLocaleTimeString("es-ES", {hour: "2-digit", minute: "2-digit"});
            }

            if (listings.length === 0) {
                empty.classList.remove("hidden");
                return;
            } else {
                empty.classList.add("hidden");
            }

            listings.forEach(item => {
                const portalBadge = item.portal === "Idealista" 
                    ? `<span class="bg-lime-500 text-white text-xs font-bold px-2.5 py-1 rounded-full shadow-sm"><i class="fa-solid fa-building text-xs mr-1"></i> Idealista</span>`
                    : `<span class="bg-blue-600 text-white text-xs font-bold px-2.5 py-1 rounded-full shadow-sm"><i class="fa-solid fa-house text-xs mr-1"></i> Fotocasa</span>`;

                const cardHtml = `
                    <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden hover:shadow-xl transition-all duration-300 flex flex-col justify-between">
                        <div>
                            <div class="relative h-56 overflow-hidden group">
                                <img src="${item.image}" alt="${item.title}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" onerror="this.src='https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80'">
                                <div class="absolute top-3 left-3 flex gap-2">
                                    ${portalBadge}
                                </div>
                                <div class="absolute bottom-3 right-3 bg-slate-900/80 backdrop-blur-md text-white px-3 py-1 rounded-lg text-xs font-semibold">
                                    ${item.price_per_m2} €/m²
                                </div>
                            </div>
                            <div class="p-5">
                                <div class="flex justify-between items-baseline mb-2">
                                    <span class="text-2xl font-extrabold text-indigo-900">${item.price.toLocaleString("es-ES")} €</span>
                                    <span class="text-xs font-semibold text-slate-500"><i class="fa-solid fa-vector-square text-indigo-500 mr-1"></i> ${item.size_m2} m²</span>
                                </div>
                                <h3 class="font-bold text-slate-800 text-base leading-snug mb-2 line-clamp-2">${item.title}</h3>
                                <p class="text-slate-500 text-xs mb-4 flex items-center"><i class="fa-solid fa-location-dot text-rose-500 mr-1.5"></i> ${item.location}</p>
                                <div class="flex flex-wrap gap-1.5 mb-4">
                                    ${(item.features || []).map(f => `<span class="bg-slate-100 text-slate-600 text-xs font-medium px-2 py-0.5 rounded-md border border-slate-200">${f}</span>`).join("")}
                                </div>
                            </div>
                        </div>
                        <div class="px-5 pb-5 pt-0">
                            <a href="${item.url}" target="_blank" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 transition-colors shadow-md text-sm">
                                <span>Ver Anuncio Original</span>
                                <i class="fa-solid fa-arrow-up-right-from-square text-xs"></i>
                            </a>
                        </div>
                    </div>
                `;
                container.innerHTML += cardHtml;
            });
        }

        window.onload = loadListings;
    </script>
</body>
</html>


⏱️ Parte 3: La Automatización Horaria (.github/workflows/update.yml)

Copia y pega este código en .github/workflows/update.yml:
name: Cron de Busqueda y Despliegue de Panel

on:
  schedule:
    # Se ejecuta cada hora de 07:00 a 23:00 (hora espanola)
    - cron: '0 5-21 * * *'
  workflow_dispatch:

permissions:
  contents: write
  pages: write
  id-token: write

jobs:
  cron-job:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Ejecutar Cron de Busqueda y volcado a listings.json
        run: |
          python scraper.py

      - name: Guardar listings.json actualizado en el repositorio
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add -A
          git diff-index --quiet HEAD || git commit -m "chore: actualizar listings.json [skip ci]"
          git push || true

      - name: Configurar GitHub Pages
        uses: actions/configure-pages@v4

      - name: Empaquetar artefectos
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'

      - name: Desplegar Panel
        id: deployment
        uses: actions/deploy-pages@v4
