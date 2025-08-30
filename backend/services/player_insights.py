from typing import List, Dict, Optional, Any
from helpers import is_goal
def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()

def _etype(ev: Dict[str, Any]) -> str:
    return ev.get("type_name", "") or ev.get("type", "") or ""

def _shot_outcome(ev: Dict[str, Any]) -> Optional["str"]:
    outcome = ev.get("shot_outcome_name") 
    return (outcome or None)

def _appears_with_role(jugada: List[Dict[str, Any]], player_id: Optional[int], role: str) -> bool:
    if player_id is None:
        return True
    
    role = role.lower()
    
    for ev in jugada:
        
        t = _norm(_etype(ev))

        if ev.get("player_id") == player_id:
            if role == "tiradores" and t == "shot":
                return True
            elif role == "asistentes" and t == "pass" and ev.get("pass_is_shot_assist") == 1:
                return True
            elif role == "pasadores_previos" and t == "pass" and ev.get("pass_is_shot_assist") == 0:
                return True
            elif role == "regateadores" and t == "dribble":
                return True
            elif role == "recuperadores" and t in ("ball recovery", "interception"):
                return True
            elif role == "recuperadores" and t == "duel":
                outcome = _norm(ev.get("duel_outcome"))
                team_id = ev.get("team_id")
                poss_team = ev.get("possession_team_id")
                
                if outcome in ("won", "success") and team_id is not None and poss_team is not None and team_id != poss_team:
                    return True
            elif role == "porteros" and t == "goal keeper":
                return True
    return False    

def compute_role_stats(jugadas: List[List[Dict[str, Any]]], role: str, player_id: int) -> Dict[str, Any]:
    role = role.lower()
    player_name = None
    
    if role == "tiradores":
        shots = 0
        goals = 0
        context: Dict[str, Dict[str, Any]] = {}
        
        for j in jugadas:
            for e in j:
                if _norm(_etype(e)) =="shot" and e.get("player_id") == player_id:
                    player_name = e.get("player_name", player_name)
                    shots += 1
                    if is_goal(e) == "goal":
                        goals += 1
                    ctx=(e.get("play_pattern_name") or "Unknown")
                    b = context.get(ctx, {"count":0, "goals":0})
                    b["count"] += 1
                    
                    if is_goal(e)== "goal":
                        b["goals"] += 1
                        
                    context[ctx] = b
            conversion = (goals / shots * 100) if shots > 0 else 0.0
        return {
            "player_name": player_name,
            "totals":{
                "appearances": shots, "goals": goals, "conversion_rate_pct": round(conversion,2) },
            "context": context
            }
                
    if role == "asistentes":
        assists = 0
        goals_created = 0
        for j in jugadas:
            for e in j:
                assist_ths = False
                ctx_ths = Dict[str, Dict[str, Any]] = {}
                
                if _norm(_etype(e)) =="Pass" and e.get("player_id") == player_id and e.get("pass_is_shot_assist") == 1:
                    player_name = e.get("player_name", player_name)
                    assists += 1
                    assist_ths = True
                    ctx_ths = (e.get("play_pattern_name") or "Unknown")
                    
                    if assist_ths:
                        goal_created = any((_norm(_etype(ev)) =="shot" and is_goal(ev) == "goal") for ev in j)
                        if goal_created:
                            goals_created += 1
                        ctx=(ctx_ths or "Unknown")
                        b = context.get(ctx, {"assists":0, "goals_created":0})
                        b["assists"] += 1
                        
                        if goal_created:
                            b["goals_created"] += 1
                        context[ctx] = b
                        
                
        return {
            "player_name": player_name,
            "totals":{
                "appearances": assists, "assisted_shots": assists, "goals_created": goals_created},
            "context": context
                 }
    
    if role == "pasadores_previos":
        passes = 0
        passes_leading_to_shot = 0
        context: Dict[str, Dict[str, Any]] = {}
        player_name = None
        
        for j in jugadas:
            
            shot_times = [e.get("ts_abs") for e in j if _norm(_etype(e)) == "shot" and isinstance(e.get("ts_abs"), (int,float))]

            for e in j:
                
                if _norm(_etype(e)) =="pass" and e.get("player_id") == player_id and e.get("pass_is_shot_assist") == 0: # No es asistencia
                    
                    player_name = e.get("player_name", player_name) 
                    passes += 1
                    
                    ev_time = e.get("ts_abs")
                    leads = False
                    
                    if isinstance(ev_time, (int, float)) and shot_times:
                        leads = any(st > ev_time for st in shot_times)
                        
                    if leads:
                        passes_leading_to_shot += 1
                        
                    ctx=(e.get("play_pattern_name") or "Unknown")
                    b = context.get(ctx, {"passes":0, "passes_leading_to_shot":0})
                    b["passes"] += 1
                    if leads:
                        b["passes_leading_to_shot"] += 1
                    context[ctx] = b
                               
        return {
            "player_name": player_name,
            "totals":{
                "appearances": passes, "passes": passes,     "passes_leading_shots": passes_leading_to_shot},
            "context": context
            }
                
                
    if role == "regateadores":
        dribbles = 0
        successful_dribbles = 0
        context: Dict[str, Dict[str, Any]] = {}
        
        for j in jugadas:
            for e in j:
                if _norm(_etype(e)) =="dribble" and e.get("player_id") == player_id:
                    player_name = e.get("player_name", player_name)
                    dribbles += 1
                    if _norm(e.get("outcome_name")) == "successful":
                        successful_dribbles += 1
                    ctx=(e.get("play_pattern_name") or "Unknown")
                    b = context.get(ctx, {"dribbles":0, "successful_dribbles":0})
                    b["dribbles"] += 1
                    
                    if _norm(e.get("outcome_name")) == "successful":
                        b["successful_dribbles"] += 1
                        
                    context[ctx] = b
        
        success_rate = (successful_dribbles / dribbles * 100) if dribbles > 0 else 0.0
        return {
            "player_name": player_name,
            "totals":{
                "appearances": dribbles, "successful_dribbles": successful_dribbles, "success_rate_pct": round(success_rate,2) },
            "context": context
        }
    
    if role == "recuperadores":
        total_recs = 0
        context = {}
        types = {}
        player_name = None
        
        RECOVERY_TYPES = ["ball Recovery", "interception", "duel"]
        
        for j in jugadas:
            for e in j:
                
                t = _norm(_etype(e))

                if t not in RECOVERY_TYPES or e.get("player_id") != player_id:
                    continue
                counts = False
                if t in ("ball recovery", "interception"):
                    counts = True
                elif t == "duel":
                    outcome = _norm(e.get("duel_outcome"))
                    team_id = e.get("team_id")
                    poss_team = e.get("possession_team_id")
                    if outcome in ("won", "success") and team_id is not None and poss_team is not None and team_id != poss_team:
                        counts = True
                if not counts:
                    continue
                player_name = e.get("player_name", player_name)
                total_recs += 1
                types[t] = types.get(t, 0) + 1
                ctx=(e.get("play_pattern_name") or "Unknown")
                if ctx not in context:
                    context[ctx] = {"total":0, "types": {}}
                context[ctx]["total"] += 1
                context[ctx]["types"][t] = context[ctx]["types"].get(t,0) + 1

                
        types_pct = {}
        
        if total_recs > 0:
            for t, c in types.items():
                types_pct[t] = round(c / total_recs * 100, 2)
        
        context_pct = {}
        for ctx, data in context.items():
            ctx_total = data.get("total", 0)
            entry = {"total": ctx_total, "types": data["types"].copy(), "types_pct": {}}
            if ctx_total > 0:
                for k, v in data["types"].items():
                    entry["types_pct"][k] = round(100.0 * v / ctx_total, 1)
            context_pct[ctx] = entry
            
        return {
                "player_name": player_name or "Desconocido",
                "totals": {
                    "appearances": total_recs,
                    "recoveries": total_recs,
                    "types": types,          # conteo bruto global
                    "types_pct": types_pct   # % global por tipo
                },
                "context": context_pct  # por play_pattern: totales, tipos y %
                }
            
    if role == "porteros":
        interventions = 0
        goals_conceed = 0
        saves = 0
        context: Dict[str, Dict[str, Any]] = {}
        
        for j in jugadas:
            gk_participate= False
            ctx_ths = None
            
            for e in j:
                if _norm(_etype(e)) =="goal keeper" and e.get("player_id") == player_id:
                    player_name = player_name or e.get("player_name", player_name)
                    gk_participate = True
                    ctx_ths = (e.get("play_pattern_name") or "Unknown")
                    
                if gk_participate:
                    interventions += 1
                    shot_goal = any((_norm(_etype(eve)) == "shot" and is_goal(eve) == "goal") for eve in j)
                    
                    if shot_goal:
                        goals_conceed += 1
                    else:
                        saves += 1
                    
                    ctx=(ctx_ths or "Unknown")
                    b= context.get(ctx, {"interventions":0, "goals_conceed":0, "saves":0})
                    b["interventions"] += 1
                    
                    if shot_goal:
                        b["goals_conceed"] += 1
                    else:
                        b["saves"] += 1
                        
                    context[ctx] = b
                
        return {
                "player_name": player_name,
                "totals":{
                    "appearances": interventions,  "goals_conceed": goals_conceed, "saves": saves},
                "context": context
                }
    if role == "creadores":
        assists = 0
        goals_created = 0
        ctx_assist = {}
        
        player_name = None
        for j in jugadas:
            asst_this = False
            ctx_this = {}
            for e in j:
                if _norm(_etype(e))=="pass" and e.get("player_id")== player_id and e.get("pass_is_shot_assist")==1:
                    player_name = player_name or e.get("player_name")
                    assists += 1
                    asst_this = True
                    ctx_this = (e.get("play_pattern_name") or "Unknown")
                
                if asst_this:
                    if any((_norm(_etype(ev))=="shot" and is_goal(ev)=="goal") for ev in j):
                        goals_created += 1
                    
                    c = ctx_this or "Unknown"
                    b = ctx_assist.get(c, {"assists":0, "goals_created":0})
                    b["assists"] += 1
                    
                    if any((_norm(_etype(ev))=="shot" and is_goal(ev)=="goal") for ev in j):
                        b["goals_created"] += 1
                        
                    ctx_assist[c] = b
        
        passes = 0
        passes_leading_to_shot = 0
        ctx_pass = {}
        
        for j in jugadas:
            shot_times = [e.get("ts_abs") for e in j if _norm(_etype(e)) == "shot" and isinstance(e.get("ts_abs"), (int,float))]
            for e in j:
                if _norm(_etype(e)) == "pass" and e.get("player_id") == player_id and e.get("pass_is_shot_assist") != 1:
                    passes += 1
                    e_ts = e.get("ts_abs")
                    leads = isinstance(e_ts, (int, float)) and any(st > e_ts for st in shot_times)
                    if leads:
                        passes_leading_to_shot += 1
                        
                    c = (e.get("play_pattern_name") or "Unknown")
                    b = ctx_pass.get(c) or {"passes": 0, "passes_leading_to_shot": 0}
                    
                    b["passes"] += 1
                    if leads: 
                        b["passes_leading_to_shot"] += 1
                    ctx_pass[c] = b
        
        score = 3 * assists + passes_leading_to_shot
        
        context = {}
        for c, a in ctx_assist.items():
            context[c] = {"assists": a["assists"], "goals_created": a["goals_created"], "passes": 0, "passes_leading_to_shot": 0}
        for c, p in ctx_pass.items():
            ct = context.get(c) or {"assists": 0, "goals_created": 0, "passes": 0, "passes_leading_to_shot": 0}
            ct["passes"] = p["passes"]
            ct["passes_leading_to_shot"] = p["passes_leading_to_shot"]
            context[c] = ct
        
        return{"player_name": player_name or "Unknown",
            "totals": {
                "assists": assists,
                "goals_created": goals_created,
                "passes": passes,
                "passes_leading_to_shot": passes_leading_to_shot,
                "creator_score": score
            },
            "contex": context
        }

    return {"player_name": "Desconocido", "totals": {}, "context": {}}
                                             
                    
def detect_result(jugada: List[Dict[str, Any]]) -> str:
    for e in jugada:
        if _norm(_etype(e)) == "shot" and is_goal(e) == "goal":
            return "goal"
    return "no goal"          

def build_youtube_query(jugada, match_map):
    """
    Construye la URL de búsqueda de YouTube usando un lookup precalculado:
    match_map: { match_id: {home_team, away_team, season_name} }
    """
    if not jugada:
        return None

    match_id = jugada[0].get("match_id")
    info = match_map.get(match_id) if match_map else None

    minuto = None
    for ev in jugada:
        m = ev.get("minute")
        if isinstance(m, int):
            minuto = m
            break

    jugador = next(
        (ev.get("player_name") for ev in jugada if ev.get("type_name") == "Shot"),
        None
    )

    if info:
        equipos = f"{info['home_team']} vs {info['away_team']}"
        temporada = info.get("season_name") or ""
        query_parts = [equipos, temporada]
        if minuto is not None:
            query_parts.append(f"minuto {minuto}")
        query_parts.append("highlights")
        if jugador:
            query_parts.append(jugador)

        query = " ".join(p for p in query_parts if p)
        return "https://www.youtube.com/results?search_query=" + query.replace(" ", "+")
    return None