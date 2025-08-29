from typing import List, Optional, Union, Dict, Any
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import Counter
import os


from motorbusqueda import motor_busqueda_avanzado

from summary import build_summary
from ranking import construir_ranking
from services import appears_with_role, compute_role_stats, detect_result, build_youtube_query

# Ajusta esta ruta a tu BBDD
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "futbol.db")

from cache import _cache_put, _cache_get

app = FastAPI(title="TFG Fútbol API")

# CORS: permite peticiones desde Vite (puerto 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EventFilter(BaseModel):
    event: Union[str, List[str]]
    play_pattern: Optional[Union[str, List[str]]] = None
    start_x: Optional[float] = None
    start_y: Optional[float] = None
    tolerance: Optional[int] = None
    zone: Optional[Dict[str, float]] = None
    optional: Optional[bool] = None

class SearchRequest(BaseModel):
    pattern: List[EventFilter]
    match_id: Optional[int] = None
    team_id: Optional[int] = None
    play_pattern: Optional[str] = None
    competition: Optional[str] = None
    tolerancia: Optional[int] = 10
    margen_tiempo: Optional[int] = 30

def _build_match_info_map(db_path, match_ids):
    if not match_ids:
        return {}

    marks = ",".join(["?"] * len(match_ids))
    sql = f"""
        SELECT m.match_id, m.home_team, m.away_team, c.season_name
        FROM matches m
        JOIN competitions c
          ON c.competition_id = m.competition_id
         AND c.season_id = m.season_id
        WHERE m.match_id IN ({marks})
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(sql, list(match_ids))
    out = {}
    for mid, home, away, season in cur.fetchall():
        out[mid] = {
            "home_team": home,
            "away_team": away,
            "season_name": season
        }
    conn.close()
    return out
        
@app.get("/status")
def status():
    return {"ok": True}

@app.post("/buscar")
def buscar(req: SearchRequest) -> Any:
    try:
        secuencia = [e.model_dump(exclude_none=True) for e in req.pattern]
        resultados = motor_busqueda_avanzado(
            db_path=DB_PATH,
            secuencia=secuencia,
            match_id=req.match_id,
            team_id=req.team_id,                     
            play_pattern=req.play_pattern,
            competition=req.competition,
            tolerancia=req.tolerancia,
            margen_tiempo=req.margen_tiempo,
        ) or []
        
        query_id = uuid4().hex[:8]
        _cache_put(query_id, resultados)
        
        summary= build_summary(resultados)
        ranking = construir_ranking(resultados)
        
        def _with_drilldown(lista: List[dict], role: str) -> List[dict]:
            
            out = []
            
            for item in lista:
                p = dict(item)
                pid = p.get("player_id")
                p["drilldown"] = f"/player-insights?role={role}&player_id={pid or ''}&query_id={query_id}"
                out.append(p)
            return out
        
        ranking_links = {role: _with_drilldown(lst, role) for role, lst in ranking.items()}

        # Limitar para evitar sobrecarga
        return {
            "summary": summary,
            "ranking": ranking_links,
            "examples": resultados[:3],
            "query_id": query_id   
        }

    except Exception as e:
        import traceback
        print("ERROR EN BUSCAR:", traceback.format_exc())
        return {"error": str(e)}
    

@app.get("/player-insights")
def player_insights(role: str, player_id: Optional[int] = None, query_id: Optional[str]= None, limit_examples: int = 5):
    seqs = _cache_get(query_id) if query_id else []
    
    if seqs is None:
        return HTTPException(status_code=404, detail="Query ID not found in cache")
    
    jugadas = [j for j in seqs if appears_with_role(j, player_id, role)]
    
    stats = compute_role_stats(jugadas, role, player_id)
    
    #----------------------------------------------------------------------------#
    wanted = jugadas[:max(1, min(int(limit_examples or 5), 15))]
    match_ids = set()
    for j in wanted:
        for ev in j:
            mid = ev.get("match_id")
            if mid is not None:
                match_ids.add(mid)
                
    match_info_map = _build_match_info_map(DB_PATH, list(match_ids))
    #----------------------------------------------------------------------------#
    examples = []
    
    n = max(1, min( int (limit_examples or 5), 15))
    
    
    for j in jugadas[:n]:
        match_id = next((ev.get("match_id") for ev in j if ev.get("match_id") is not None), None)
        minute = next((ev.get("minute") for ev in j if ev.get("minute") is not None), None)
        event_ids = ";".join([ev.get("event_id") for ev in j if ev.get("event_id")])
        examples.append({
            "match_id": match_id,
            "minute": minute,
            "events": [ev.get("type_name") for ev in j],
            "result": detect_result(j),
            "preview": f"/render/play?match_id={match_id}&event_ids={event_ids}" if match_id and event_ids else None,
            "youtube_search": build_youtube_query(j, match_info_map)
        })

    return {
        "role": role,
        "player_id": player_id,
        "player": stats.get("player_name"),
        "totals": stats.get("totals"),
        "context": stats.get("context"),
        "examples": examples
    }