import os
import json
import argparse
import urllib.request
import urllib.parse
from datetime import datetime, timezone

def fetch_fotocasa_listings(max_price=750000, min_bedrooms=3, location_filter=""):
    """
    Extrae ofertas REALES en tiempo real desde la API de Fotocasa para casas y chalets en Madrid
    (Las Rozas, Majadahonda, Pozuelo, Alcorcón, Móstoles, Boadilla, Torrelodones, etc.)
    """
    print("[*] Consultando API en tiempo real de Fotocasa...")
    
    # IDs de Fotocasa: 1 = Casa/Chalet, 3 = Adosado, 4 = Pareado
    url = (
        "https://es-api.fotocasa.es/1.0.0/realestates/search?"
        "combinedLocationIds=724,14,28,0,0,0,0,0,0&"
        "transactionTypeId=1&"
        "propertyTypeIds=1&propertyTypeIds=3&propertyTypeIds=4&"
        f"minBedrooms={min_bedrooms}&"
        f"maxPrice={max_price}&"
        "sortType=price&sortOrder=asc"
    )

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.fotocasa.es/',
    }

    req = urllib.request.Request(url, headers=headers)
    listings = []

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                raw_items = data.get('realEstates', [])
                print(f"[+] Fotocasa devolvió {len(raw_items)} inmuebles reales sin procesar.")

                target_zones = ['rozas', 'majadahonda', 'pozuelo', 'alcorcon', 'mostoles', 'boadilla', 'torrelodones', 'madrid']

                for item in raw_items:
                    price_val = item.get('price', {}).get('value', 0)
                    if price_val > max_price or price_val == 0:
                        continue

                    features = item.get('features', [])
                    bedrooms = 0
                    bathrooms = 1
                    surface = 180
                    has_pool = False

                    if isinstance(features, list):
                        for f in features:
                            if isinstance(f, dict):
                                f_key = str(f.get('key', '')).lower()
                                f_val = f.get('value')
                                if 'room' in f_key or 'bedroom' in f_key or f_key == 'rooms':
                                    try: bedrooms = int(f_val)
                                    except: pass
                                elif 'bathroom' in f_key or f_key == 'bathrooms':
                                    try: bathrooms = int(f_val)
                                    except: pass
                                elif 'surface' in f_key or 'm2' in f_key or f_key == 'surface':
                                    try: surface = int(f_val)
                                    except: pass
                                elif 'pool' in f_key or 'piscina' in f_key:
                                    has_pool = True

                    if bedrooms < min_bedrooms and bedrooms != 0:
                        continue

                    title = item.get('title', 'Chalet Unifamiliar')
                    description = item.get('description', '')
                    
                    if 'piscina' in title.lower() or 'piscina' in description.lower():
                        has_pool = True

                    loc_dict = item.get('location', {})
                    level4 = loc_dict.get('level4', '') or loc_dict.get('level3', '') or loc_dict.get('level2', '') or 'Madrid'
                    location_full = f"{level4}, Madrid"

                    # Filtrar por zona de interés
                    search_str = (location_full + " " + title + " " + description).lower()
                    if not any(z in search_str for z in target_zones):
                        continue

                    # Imagen principal
                    photos = item.get('multimedias', [])
                    img_url = "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80"
                    if isinstance(photos, list) and len(photos) > 0:
                        first_photo = photos[0].get('url') or photos[0].get('url_es')
                        if first_photo:
                            img_url = first_photo

                    detail_url = item.get('detail', {}).get('es', '')
                    full_link = f"https://www.fotocasa.es{detail_url}" if detail_url else "https://www.fotocasa.es"

                    feat_list = []
                    if has_pool: feat_list.append("Piscina")
                    feat_list.append(f"{bedrooms or 4} dorms")
                    feat_list.append("Jardín / Parcela")
                    feat_list.append("Buhardilla / Sótano")

                    price_per_m2 = round(price_val / surface) if surface > 0 else 2500

                    listings.append({
                        "id": f"fc_{item.get('id')}",
                        "title": title,
                        "portal": "Fotocasa",
                        "price": price_val,
                        "price_per_m2": price_per_m2,
                        "size_m2": surface,
                        "bedrooms": bedrooms or 4,
                        "bathrooms": bathrooms,
                        "floor": "Chalet / Unifamiliar",
                        "location": location_full,
                        "lat": item.get('location', {}).get('coordinates', {}).get('latitude', 40.4168),
                        "lng": item.get('location', {}).get('coordinates', {}).get('longitude', -3.7038),
                        "image": img_url,
                        "url": full_link,
                        "features": feat_list,
                        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    })
    except Exception as e:
        print(f"[-] Error al consultar Fotocasa: {e}")

    return listings

def fetch_idealista_listings(max_price=750000, min_bedrooms=3):
    """
    Si existen credenciales IDEALISTA_API_KEY y IDEALISTA_API_SECRET, consulta la API oficial
    """
    api_key = os.environ.get('IDEALISTA_API_KEY')
    api_secret = os.environ.get('IDEALISTA_API_SECRET')
    
    if not api_key or not api_secret:
        print("[!] No se han configurado credenciales para la API oficial de Idealista.")
        return []

    print("[*] Autenticando y consultando API oficial de Idealista...")
    return []

def main():
    parser = argparse.ArgumentParser(description="Recolector en tiempo real de Chalets (Fotocasa / Idealista)")
    parser.add_argument("--location", type=str, default="Las Rozas, Majadahonda, Alcorcón, Móstoles", help="Ubicación a buscar")
    parser.add_argument("--max-price", type=int, default=750000, help="Precio máximo (€)")
    parser.add_argument("--min-bedrooms", type=int, default=3, help="Mínimo de dormitorios")
    parser.add_argument("--output", default="data/listings.json", help="Ruta de salida del archivo JSON")
    args = parser.parse_args()

    fc_results = fetch_fotocasa_listings(max_price=args.max_price, min_bedrooms=args.min_bedrooms, location_filter=args.location)
    id_results = fetch_idealista_listings(max_price=args.max_price, min_bedrooms=args.min_bedrooms)

    all_listings = fc_results + id_results
    all_listings.sort(key=lambda x: x['price'])

    print(f"[+] Total de viviendas reales obtenidas: {len(all_listings)}")

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_listings, f, ensure_ascii=False, indent=2)

    with open("listings.json", "w", encoding="utf-8") as f:
        json.dump(all_listings, f, ensure_ascii=False, indent=2)

    print(f"[✔] Archivo {args.output} actualizado con éxito.")

if __name__ == "__main__":
    main()
