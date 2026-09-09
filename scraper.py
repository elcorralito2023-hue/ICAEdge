import os
import json
import re
import argparse
import urllib.request
from datetime import datetime, timezone

def find_real_estates(obj):
    if isinstance(obj, dict):
        if "realEstates" in obj and isinstance(obj["realEstates"], list):
            return obj["realEstates"]
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                res = find_real_estates(v)
                if res:
                    return res
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                res = find_real_estates(item)
                if res:
                    return res
    return None

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

    # Fallback actualizando marcas de tiempo
    if not results and os.path.exists("listings.json"):
        print("[!] Reutilizando dataset existente y actualizando marcas de tiempo...")
        try:
            with open("listings.json", "r", encoding="utf-8") as f:
                results = json.load(f)
                now_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                for item in results:
                    item["updated_at"] = now_str
        except Exception as ex:
            print("[-] Error leyendo listings.json existente:", ex)

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

    with open("listings.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    os.makedirs("data", exist_ok=True)
    with open("data/listings.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
