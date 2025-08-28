from collections import Counter, defaultdict
from typing import List, Dict, Any

def build_summary(resultados: List[List[dict]]) -> dict:
    
    total = len(resultados)
    if total == 0:
        return {
            "total": 0,
            "ranking": {},
            "sequences": []
        }
    
    deltas = []
    teams_ids, match_ids = set(), set()
    eventos_por_jugada = []
    
    for jugada in resultados:
        if not jugada:
            continue
        
        for ev in jugada:
            if ev.get("team_id") is not None:
                teams_ids.add(ev["team_name"])
            if ev.get("match_id") is not None:
                match_ids.add(ev["match_id"])
            
        tiempos = [ev.get("ts_abs") for ev in jugada if isinstance(ev.get("ts_abs"),(int,float))]
        tiempos_ordenados = sorted(tiempos)
        
        if tiempos_ordenados:
            for i in range(1, len(tiempos_ordenados)):
                deltas.append(max(0.0, float(tiempos_ordenados[i]- tiempos_ordenados[i-1])))
                
    avg_delta = sum(deltas)/len(deltas) if deltas else 0.0
    
    return {
        "total": total,
        "avg_time_between_events_sec": round(avg_delta, 2),
        "teams_covered": len(teams_ids),
        "matches_covered": len(match_ids),
    }