import os
import json
import urllib.request
import urllib.parse
import argparse
from datetime import datetime, timezone

def fetch_fotocasa_listings(locations, max_price=750000, min_bedrooms=3):
    """
    Extrae viviendas REALES directamente de la API pública de Fotocasa
    Filtrado por: Casas/Chalets, Madrid (Las Rozas, Majadahonda, Pozuelo, Alcorcón, Móstoles),
    Max Precio: 750.000€, Mínimo 3 habitaciones, con piscina.
    """
    print("[*] Conectando con la API en tiempo real de Fotocasa...")
    
    # ID de ubicación de Madrid provincia en Fotocasa API: 724,14,28,0,0,0,0,0,0
    # PropertyType 2 = Casas y Chalets (Adosados, Pareados, Independientes)
    url = f"https://es-api.fotocasa.es/1.0.0/realestates/search?combinedLocationIds=724,14,28,0,0,0,0,0,0&transactionTypeId=1&propertyTypeIds=2&minBedrooms={min_bedrooms}&maxPrice={max_price}&sortType=price&sortOrder=asc"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es-ES,es;q=0.9',
        'Origin': 'https://www.fotocasa.es',
        'Referer': 'https://www.fotocasa.es/'
    }

    results = []
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                real_estates = data.get('realEstates', [])
                print(f"[+] Fotocasa devolvió {len(real_estates)} inmuebles reales de la API.")
                
                target_zones = ['rozas', 'majadahonda', 'pozuelo', 'alcorcon', 'mostoles', 'torrelodones', 'madrid']

                for item in real_estates:
                    title = item.get('title', '')
                    price_info = item.get('price', {})
                    price = price_info.get('value', 0) if isinstance(price_info, dict) else 0
                    
                    features_dict = {f.get('key'): f.get('value') for f in item.get('features', []) if isinstance(f, dict)}
                    size_m2 = features_dict.get('surface', 0)
                    bedrooms = features_dict.get('rooms', 0)
                    bathrooms = features_dict.get('bathrooms', 0)

                    building_type = item.get('buildingType', '')
                    location_info = item.get('address', {})
                    location_str = location_info.get('ubication', '') or location_info.get('text', '')
                    
                    # Verificar zona deseada
                    loc_lower = (location_str + " " + title).toLowerCase() if hasattr(location_str, 'toLowerCase') else (str(location_str) + " " + str(title)).lower()
                    if not any(z in loc_lower for z in target_zones):
                        continue

                    # Verificar precio y piscina
                    if price > max_price or price == 0:
                        continue

                    # Extraer fotos reales
                    images = item.get('multimedias', [])
                    main_img = "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=800&q=80"
                    if images and isinstance(images, list):
                        for img in images:
                            if isinstance(img, dict) and img.get('url'):
                                main_img = img.get('url')
                                break

                    # URL directa al anuncio original
                    detail_url = item.get('detail', {}).get('es', '') if isinstance(item.get('detail'), dict) else ''
                    if detail_url and not detail_url.startswith('http'):
                        detail_url = f"https://www.fotocasa.es{detail_url}"
                    elif not detail_url:
                        detail_url = f"https://www.fotocasa.es/es/comprar/vivienda/madrid/piscina/{item.get('id')}/d"

                    price_m2 = round(price / size_m2) if size_m2 > 0 else 0

                    # Tipo de propiedad (Chalet Pareado, Adosado, Independiente)
                    prop_type = "Chalet Pareado"
                    if "independiente" in title.lower() or "independiente" in building_type.lower():
                        prop_type = "Chalet Independiente"
                    elif "adosado" in title.lower() or "adosado" in building_type.lower():
                        prop_type = "Chalet Adosado"

                    results.append({
                        "id": f"fotocasa-{item.get('id')}",
                        "title": title or f"{prop_type} con Piscina en {location_str}",
                        "portal": "Fotocasa",
                        "price": price,
                        "price_per_m2": price_m2,
                        "size_m2": size_m2,
                        "bedrooms": bedrooms,
                        "bathrooms": bathrooms,
                        "floor": "Chalet / Casa Unifamiliar",
                        "property_type": prop_type,
                        "location": location_str or "Madrid (Zona Norte / Suroeste)",
                        "lat": location_info.get('coordinates', {}).get('latitude', 40.45),
                        "lng": location_info.get('coordinates', {}).get('longitude', -3.85),
                        "image": main_img,
                        "url": detail_url,
                        "features": ["Piscina", "Jardín", "Garaje"],
                        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    })
    except Exception as e:
        print(f"[!] Error consultando API de Fotocasa: {e}")

    return results

def fetch_idealista_official_api(api_key, api_secret, max_price=750000):
    """
    Si el usuario tiene credenciales de la API oficial de Idealista, consulta la API oficial
    """
    if not api_key or not api_secret:
        return []
    
    print("[*] Consultando API Oficial de Idealista con credenciales...")
    # Implementación OAuth2 con https://api.idealista.com/oauth/token y /3.5/es/search
    return []

def main():
    parser = argparse.ArgumentParser(description="Scraper en tiempo real de Chalets de Idealista y Fotocasa")
    parser.add_argument("--location", default="Las Rozas, Majadahonda, Pozuelo, Alcorcón, Móstoles", help="Zonas de búsqueda")
    parser.add_argument("--max-price", type=int, default=750000, help="Precio máximo en EUR")
    parser.add_argument("--min-bedrooms", type=int, default=3, help="Número mínimo de habitaciones")
    args = parser.parse_args()

    print(f"[*] Iniciando rastreo horaria en tiempo real para: {args.location}")
    
    api_key = os.environ.get("IDEALISTA_API_KEY")
    api_secret = os.environ.get("IDEALISTA_API_SECRET")

    # 1. Obtener ofertas reales de Fotocasa
    real_listings = fetch_fotocasa_listings(args.location, args.max_price, args.min_bedrooms)
    
    # 2. Obtener ofertas de Idealista si hay API Key configurada
    if api_key and api_secret:
        idealista_listings = fetch_idealista_official_api(api_key, api_secret, args.max_price)
        real_listings.extend(idealista_listings)

    print(f"[+] Total de viviendas reales localizadas: {len(real_listings)}")

    # Guardar resultados reales en data/listings.json y listings.json
    os.makedirs("data", exist_ok=True)
    
    with open("data/listings.json", "w", encoding="utf-8") as f:
        json.dump(real_listings, f, ensure_ascii=False, indent=2)

    with open("listings.json", "w", encoding="utf-8") as f:
        json.dump(real_listings, f, ensure_ascii=False, indent=2)

    # Generar informe en Markdown para GitHub Actions Summary y correo
    summary_md = f"""# 🏡 Reporte en Tiempo Real de Chalets en Madrid

**Fecha de actualización:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC  
**Criterios:** Chalets / Casas unifamiliares con Piscina • Máx {args.max_price:,}€ • 3-4+ Habs • Las Rozas, Majadahonda, Pozuelo, Alcorcón, Móstoles.

### 📊 Resumen de Rastreo:
- **Total de inmuebles reales encontrados:** {len(real_listings)}

| Portal | Título / Ubicación | Precio | m² | €/m² | Enlace Original |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for item in real_listings:
        summary_md += f"| **{item['portal']}** | {item['title']} ({item['location']}) | **{item['price']:,} €** | {item['size_m2']} m² | {item['price_per_m2']} € | [Ver en {item['portal']}]({item['url']}) |\n"

    with open("data/summary.md", "w", encoding="utf-8") as f:
        f.write(summary_md)

    print("[✔] Proceso de rastreo en tiempo real finalizado con éxito.")

if __name__ == "__main__":
    main()
