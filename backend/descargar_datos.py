"""
Descarga el dataset open-data de StatsBomb:
- competitions.json
- matches/<competition_id>/<season_id>.json
- events/<match_id>.json
- three-sixty/<match_id>.json (si existe)

Características:
- Reintentos con backoff exponencial y timeouts.
- Crea directorios automáticamente.
- Barra de progreso con tqdm.
- Opción de saltar archivos existentes (predeterminado).
- Filtros opcionales por competición y/o temporada.
- Comprobación final de eventos faltantes.

Uso típico (todo):
    python descargar_datos.py

Forzar re-descarga de todo:
    python descargar_datos.py --overwrite

Filtrar por competición:
    python descargar_datos.py --competition 11

Filtrar por comp+season concretos (varias veces):
    python descargar_datos.py --pair 11:1 --pair 43:3
"""


import argparse
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from requests import Response
from tqdm import tqdm


RAW_BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data" 

LDEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

HEADERS = {
    "User-Agent": "FootAnalytics/1.0 (+https://github.com/AngelZM22/SequenceLabs) Python-requests"
}


# GET JSON con reintentos. Devuelve dict o None si 404. Lanza excepción si tras reintentos no es 2xx y no es 404. 
def http_get_json(url: str, *, retries: int = 3, timeout: int = 20, sleep_base: float = 0.8) -> Optional[dict]:
   
    last_exc = None
    for attempt in range(retries):
        try:
            resp: Response = requests.get(url, headers=HEADERS, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 404:
                return None
            # Otros códigos: backoff y reintento
            time.sleep(sleep_base * (2 ** attempt))
        except requests.RequestException as e:
            last_exc = e
            time.sleep(sleep_base * (2 ** attempt))
    if last_exc:
        raise last_exc
    raise RuntimeError(f"GET {url} failed after {retries} retries")

def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def descargar_competitions(dst_dir: Path, overwrite: bool):
    out = dst_dir / "competitions.json"
    
    if out.exists() and not overwrite:
        return out
    
    url = f"{RAW_BASE}/competitions.json"
    
    data = http_get_json(url)
    
    if data is None:
        raise RuntimeError("No se pudo obtener competitions.json (404)")
    
    save_json(out, data)
    
    return out

def iter_comp_seasons_from_competitions(competitions_json: Path) -> List[Tuple[int, int, Optional[str], Optional[str]]]:
    
    comps = load_json(competitions_json)
    pairs: List[Tuple[int, int, Optional[str], Optional[str]]] = []
    
    for row in comps:
        comp_id = int(row["competition_id"])
        season_id = int(row["season_id"])
        comp_name = row.get("competition_name")
        season_name = row.get("season_name")
        pairs.append((comp_id, season_id, comp_name, season_name))
        
    return pairs


# Descarga matches/<comp>/<season>.json

def descargar_partidos(dst_dir: Path, comp_id: int, season_id: int, overwrite: bool) -> Optional[Path]:
    
    out = dst_dir / "matches" / str(comp_id) / f"{season_id}.json"
    if out.exists() and not overwrite:
        return out
    url = f"{RAW_BASE}/matches/{comp_id}/{season_id}.json"
    data = http_get_json(url)
    if data is None:
        # Algunas combinaciones pueden no existir en open-data
        return None
    
    save_json(out, data)
    return out

def extraer_match_ids(matches_path: Path) -> List[int]:
    if not matches_path or not matches_path.exists():
        return []
    data = load_json(matches_path)
    ids: List[int] = []
    for m in data:
        mid = int(m["match_id"])
        ids.append(mid)
    return ids

def descargar_evento_por_partido(dst_dir: Path, match_id: int, overwrite: bool) -> bool:
    """
    Devuelve True si se descargó/guardó (nuevo o sobreescrito).
    Devuelve False si ya existía y no se sobreescribe.
    """
    out = dst_dir / "events" / f"{match_id}.json"
    if out.exists() and not overwrite:
        return False
    url = f"{RAW_BASE}/events/{match_id}.json"
    data = http_get_json(url)
    if data is None:
        # No todos los partidos tienen events en el repo (raro pero posible).
        return False
    save_json(out, data)
    return True


def descargar_datos():
    parser = argparse.ArgumentParser(description="Descargar StatsBomb Open Data (competitions, matches, events, three-sixty).")
    parser.add_argument("--data-dir", type=str, default=str(LDEFAULT_DATA_DIR), help="Directorio base de datos (por defecto: ./data)")
    parser.add_argument("--overwrite", action="store_true", help="Re-descargar y sobrescribir archivos existentes")
    parser.add_argument("--competition", type=int, nargs="*", help="Filtrar por competition_id (uno o varios)")
    parser.add_argument("--pair", type=str, nargs="*", help="Filtrar por pares comp:season (p.ej. 11:1 43:3)")

    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    overwrite = args.overwrite
    
    print(f"➡ Descargando a: {data_dir}")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    
    # 1) competitions.json
    comp_json_path = descargar_competitions(data_dir, overwrite)
    pairs = iter_comp_seasons_from_competitions(comp_json_path)
    
    if args.competition:
        wanted = set(args.competition)
        pairs = [p for p in pairs if p[0] in wanted]
    
    if args.pair:
        wanted_pairs = set()
        for token in args.pair:
            try:
                c, s = token.split(":")
                wanted_pairs.add((int(c), int(s)))
            except Exception:
                print(f"⚠️  Ignorando --pair inválido: {token} (usa comp:season)")
        pairs = [p for p in pairs if (p[0], p[1]) in wanted_pairs] or pairs
    
    
    # 2) matches por cada comp-season
    match_files: List[Tuple[int, int, Optional[Path]]] = []
    print("\n📥 Descargando MATCHES por competición/temporada…")
    for comp_id, season_id, comp_name, season_name in tqdm(pairs, ncols=100):
        mpath = descargar_partidos(data_dir, comp_id, season_id, overwrite)
        match_files.append((comp_id, season_id, mpath))
    
    
    # 3) events y 360 por cada partido
    all_match_ids: List[int] = []
    for _, _, mfile in match_files:
        mids = extraer_match_ids(mfile) if mfile else []
        all_match_ids.extend(mids)
        
    print(f"\n📦 Partidos totales a comprobar: {len(all_match_ids)}")

    # Events
    print("\n🎯 Descargando EVENTS (por partido)…")
    downloaded_events = 0
    for mid in tqdm(all_match_ids, ncols=100):
        ok = descargar_evento_por_partido(data_dir, mid, overwrite)
        if ok:
            downloaded_events += 1
        # pausas breves para no estresar GitHub Raw si hay muchos
        time.sleep(0.02)
        
    print("\n Resumen:")
    print(f" - competitions.json: {comp_json_path}")
    print(f" - matches descargados o presentes: {sum(1 for _, _, p in match_files if p and p.exists())}/{len(match_files)}")
    print(f" - events nuevos descargados: {downloaded_events}")


    # Chequeo de faltantes
    events_dir = data_dir / "events"
    missing = []
    for mid in all_match_ids:
        if not (events_dir / f"{mid}.json").exists():
            missing.append(mid)

    if missing:
        print(f"\n Eventos faltantes: {len(missing)} (puede que no existan en open-data o fallo de red).")
        # Muestra los primeros para depurar
        print("   Ejemplos:", missing[:20])
    else:
        print("\n🎉 Todos los partidos listados tienen su events.json local.")

if __name__ == "__main__":
    descargar_datos()