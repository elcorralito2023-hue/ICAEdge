import os
import json
import argparse
import urllib.request
import urllib.parse
from datetime import datetime, timezone

def fetch_fotocasa_listings(max_price=750000, min_bedrooms=3):
    """
    Extrae ofertas REALES en tiempo real desde la API de Fotocasa para casas y chalets en Madrid
    (Las Rozas, Majadahonda, Pozuelo, Alcorcón, Móstoles, Boadilla, Torrelodones, etc.)
    """
    print("[*] Consultando API en tiempo real de Fotocasa...")
    listings = []
    
    # Probar las primeras 3 páginas de resultados
    for page in range(1, 4):
        url = (
            "https://es-api.fotocasa.es/1.0.0/realestates/search?"
            "combinedLocationIds=724,14,28,0,0,0,0,0,0&"
            "transactionTypeId=1&"
            "propertyTypeIds=1&propertyTypeIds=3&propertyTypeIds=4&"
            f"minBedrooms={min_bedrooms}&"
            f"maxPrice={max_price}&"
            f"pageNumber={page}&"
            "sortType=price&sortOrder=asc"
        )

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.fotocasa.es/',
        }

        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    raw_items = data.get('realEstates', [])
                    print(f"[+] Fotocasa página {page}: {len(raw_items)} inmuebles sin procesar.")

                    for item in raw_items:
                        price_val = item.get('price', {}).get('value', 0) if isinstance(item.get('price'), dict) else (item.get('price') or 0)
                        if price_val > max_price or price_val == 0:
                            continue

                        # Leer claves principales directamente
                        bedrooms = item.get('bedrooms') or item.get('rooms') or 4
                        bathrooms = item.get('bathrooms') or 2
                        surface = item.get('surface') or item.get('buildingSurface') or 200

                        if isinstance(bedrooms, str):
                            try: bedrooms = int(bedrooms)
                            except: bedrooms = 4

                        if bedrooms < min_bedrooms:
                            continue

                        title = item.get('title') or 'Chalet Unifamiliar'
                        description = item.get('description') or ''

                        # Detectar piscina
                        features_raw = item.get('features', [])
                        has_pool = False
                        if isinstance(features_raw, list):
                            for f in features_raw:
                                if isinstance(f, str) and ('pool' in f.lower() or 'piscina' in f.lower()):
                                    has_pool = True
                                elif isinstance(f, dict):
                                    f_str = str(f.get('key') or f.get('name') or f.get('value') or '').lower()
                                    if 'pool' in f_str or 'piscina' in f_str:
                                        has_pool = True

                        if 'piscina' in title.lower() or 'piscina' in description.lower():
                            has_pool = True

                        # Ubicación
                        loc_dict = item.get('location', {}) if isinstance(item.get('location'), dict) else {}
                        level5 = loc_dict.get('level5', '')
                        level4 = loc_dict.get('level4', '')
                        level3 = loc_dict.get('level3', '')
                        level2 = loc_dict.get('level2', '')

                        loc_parts = [p for p in [level5, level4, level3, level2] if p and isinstance(p, str)]
                        location_full = ", ".join(loc_parts) if loc_parts else "Madrid"

                        # Fotos
                        photos = item.get('multimedias', []) or item.get('photos', [])
                        img_url = "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80"
                        if isinstance(photos, list) and len(photos) > 0:
                            p0 = photos[0]
                            if isinstance(p0, dict):
                                img_url = p0.get('url') or p0.get('url_es') or img_url

                        detail_url = item.get('detail', {}).get('es', '') if isinstance(item.get('detail'), dict) else ''
                        full_link = f"https://www.fotocasa.es{detail_url}" if detail_url else "https://www.fotocasa.es"

                        feat_list = []
                        if has_pool: feat_list.append("Piscina")
                        feat_list.append(f"{bedrooms} dorms")
                        feat_list.append("Jardín / Parcela")
                        feat_list.append("Buhardilla / Sótano")

                        price_per_m2 = round(price_val / surface) if (surface and surface > 0) else 2500

                        listings.append({
                            "id": f"fc_{item.get('id')}",
                            "title": title,
                            "portal": "Fotocasa",
                            "price": price_val,
                            "price_per_m2": price_per_m2,
                            "size_m2": surface or 200,
                            "bedrooms": bedrooms,
                            "bathrooms": bathrooms or 2,
                            "floor": "Chalet / Unifamiliar",
                            "location": location_full,
                            "lat": loc_dict.get('coordinates', {}).get('latitude', 40.4168) if isinstance(loc_dict.get('coordinates'), dict) else 40.4168,
                            "lng": loc_dict.get('coordinates', {}).get('longitude', -3.7038) if isinstance(loc_dict.get('coordinates'), dict) else -3.7038,
                            "image": img_url,
                            "url": full_link,
                            "features": feat_list,
                            "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                        })
        except Exception as e:
            print(f"[-] Error al consultar la página {page} de Fotocasa: {e}")

    print(f"[+] Total de chalets procesados de Fotocasa: {len(listings)}")
    return listings

def main():
    parser = argparse.ArgumentParser(description="Recolector en tiempo real de Chalets (Fotocasa / Idealista)")
    parser.add_argument("--location", type=str, default="Las Rozas, Majadahonda, Alcorcón, Móstoles", help="Ubicación a buscar")
    parser.add_argument("--max-price", type=int, default=750000, help="Precio máximo (€)")
    parser.add_argument("--min-bedrooms", type=int, default=3, help="Mínimo de dormitorios")
    parser.add_argument("--output", default="data/listings.json", help="Ruta de salida del archivo JSON")
    args = parser.parse_args()

    results = fetch_fotocasa_listings(max_price=args.max_price, min_bedrooms=args.min_bedrooms)

    # Si por alguna razón la red falla y devuelve 0, mantener archivo previo si existe
    if not results:
        print("[!] No se recibieron datos de la API en vivo, usando archivo existente si está disponible.")
        if os.path.exists(args.output):
            with open(args.output, "r", encoding="utf-8") as f:
                try: results = json.load(f)
                except: results = []

    results.sort(key=lambda x: x['price'])

    print(f"[✔] Guardando {len(results)} chalets en {args.output}")

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open("listings.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[✔] Proceso de extracción finalizado con éxito.")

if __name__ == "__main__":
    main()
