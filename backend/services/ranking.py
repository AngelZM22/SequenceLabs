from collections import Counter
from typing import List, Dict, Any
from helpers import _norm, is_success

def construir_ranking(secuencias: List[List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]] :
    tiradores = Counter()
    asistentes = Counter()
    pasadores_previos = Counter()
    recuperadores = Counter()
    regateadores = Counter()
    porteros = Counter()
    
    id2name:     Dict[int, str]= {}
    
    for jugada in secuencias:
        for ev in jugada:
            tipo = _norm(ev.get("type_name"))
            pid = ev.get("player_id")
            pname = ev.get("player_name")
            
            if pid is None:
                continue
            
            if pname:
                id2name[pid] = pname
            
            if tipo == "shot":
                tiradores[pid] += 1
            
            elif tipo == "pass":
                if ev.get("pass_is_shot_assist"):
                    asistentes[pid] += 1
                else:
                    pasadores_previos[pid] += 1
                    
            elif tipo == "dribble":
                if _norm(ev.get("dribble_outcome_name")) == "complete":
                    regateadores[pid] += 1
                
            elif tipo in ("ball recovery", "interception"):
                if(is_success(ev)):
                    recuperadores[pid] += 1
            
            elif tipo == "duel":    
                team_id = ev.get("team_id")
                poss_team = ev.get("possession_team_id")
                
                if is_success(ev) and team_id is not None and poss_team is not None and team_id != poss_team:
                    recuperadores[pid] += 1

            elif tipo == "goal keeper":
                porteros[pid] += 1
                
    def _top(counter: Counter, n: int = 10):
        out = []
        for pid, c in counter.most_common(n):
            out.append({
                "player_id": pid,
                "player_name": id2name.get(pid, "Unknown"),
                "count": c
            })
        return out
    
    ranking: Dict[str, list[dict]] ={}
    
    if tiradores:
        ranking["tiradores"] = _top(tiradores)
    if asistentes:
        ranking["asistentes"] = _top(asistentes)
    if pasadores_previos:
        ranking["pasadores_previos"] = _top(pasadores_previos)
    if recuperadores:
        ranking["recuperadores"] = _top(recuperadores)
    if regateadores:
        ranking["regateadores"] = _top(regateadores)
    if  porteros:
        ranking["porteros"] = _top(porteros)
        
    pesos = {"assist": 3, "pass_lead": 1}
    score = Counter()
    for key in set(list(asistentes.keys())+ list(pasadores_previos.keys())):
        s = pesos["assist"] * asistentes.get(key, 0) + pesos["pass_lead"] * pasadores_previos.get(key, 0)
        if s > 0:
            score[key] = s
            
    def _topcreador(counter, n=10):
        out= []
        for pid, s in counter.most_common(n):
            out.append({
                "player_id": pid, "player": id2name.get(pid, "Unknown"), "score": s,
                "assists": asistentes.get(pid, 0),
                "passes_leading_to_shot": pasadores_previos.get(pid, 0)
            })
        return out

    if score:
        ranking["creadores"] = _topcreador(score)
        
    return ranking