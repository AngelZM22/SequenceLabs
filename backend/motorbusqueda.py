import sqlite3
from helpers import  _norm
from helpers import  _norm_equals
from helpers import  _norm_in
from helpers import _outcome_of, is_duel_won, is_goal, is_foul, is_interception_success, is_recovery, is_shot, is_success, matches_outcome, _different_player, _different_team, _same_player, _same_team
from typing import Optional, List, Dict, Any, Union

DEBUG_FILE = "debug_log.txt"

ZoneSpec = Union[str, Dict[str, float]]

def dlog(*args):
    """Escribe logs de depuración en un archivo de texto (append)."""
    try:
        with open(DEBUG_FILE, "a", encoding="utf-8") as f:
            print(*args, file=f)
    except Exception as e:
        # Evitar que un fallo de logging rompa el motor
        pass
# ------------------------

_LANES = ["left_wing", "left_halfspace", "center", "right_halfspace", "right_wing"]
_Y = [0, 16, 32, 48, 64, 80]
GRID6x3_EDGES_X = [0, 18, 40, 60, 80, 102, 120]
GRID6x3_EDGES_Y = [0, 18, 62, 80]

def _build_extended_zones() -> Dict[str, Dict[str, float]]:
    z: Dict[str, Dict[str, float]] = {}

    # TERCERAS DEL CAMPO

    for r in range(3):
        for c in range(6):
            x0 = GRID6x3_EDGES_X[c]
            x1 = GRID6x3_EDGES_X[c + 1]
            y0 = GRID6x3_EDGES_Y[r]
            y1 = GRID6x3_EDGES_Y[r + 1]
            key = f"g_r{r+1}_c{c+1}"
            z[key] = {"x_min": x0, "x_max": x1, "y_min": y0, "y_max": y1}

    
    z["own_half"]       = {"x_min": 0,   "x_max": 60,  "y_min": 0,  "y_max": 80}
    z["opponent_half"]  = {"x_min": 60,  "x_max": 120, "y_min": 0,  "y_max": 80}
    z["final_third"]    = {"x_min": 80,  "x_max": 120, "y_min": 0,  "y_max": 80}

    # ÁREAS
    z["box_left"]       = {"x_min": 0,   "x_max": 18,  "y_min": 18, "y_max": 62}
    z["box_right"]      = {"x_min": 102, "x_max": 120, "y_min": 18, "y_max": 62}
    
    # Áreas chicas
    z["six_left"]       = {"x_min": 0,   "x_max": 6,   "y_min": 30, "y_max": 50}
    z["six_right"]      = {"x_min": 114, "x_max": 120, "y_min": 30, "y_max": 50}

    # Córners
    z["corner_top_left"]        = {"x_min": 0,   "x_max": 2,   "y_min": 0, "y_max": 2} 
    z["corner_bottom_left"]     = {"x_min": 0,   "x_max": 2,   "y_min": 79, "y_max": 80}
    z["corner_top_right"]       = {"x_min": 118,   "x_max": 120,   "y_min": 0, "y_max": 2}
    z["corner_bottom_right"]    ={"x_min": 118,   "x_max": 120,   "y_min": 78, "y_max": 80} 
    
    return z

ZONES = _build_extended_zones()

SUCCESS_OUTCOMES = {"won", "success", "successful", "complete"}  # amplía si lo necesitas

EVENTOS_RUIDO = {
    "Pressure", 
    "Player On", "Player Off", "Substitution",
    "Injury Stoppage", "Referee Ball-Drop", "Tactical Shift"
}

def ver_zona(zone: Optional[ZoneSpec]) -> Optional[Dict[str, float]]:
    #Admite: None | nombre de zona | rect dict {x_min,x_max,y_min,y_max}.
    
    if zone is None:
        return None
    
    if isinstance(zone, dict):
        # Validación mínima
        for k in ("x_min","x_max","y_min","y_max"):
            if k not in zone:
                raise ValueError(f"zone dict missing key: {k}")
            
        return zone
    if isinstance(zone, str):
        if zone not in ZONES:
            raise ValueError(f"Unknown zone name: {zone}")
        return ZONES[zone]
    raise ValueError("Invalid zone type")

def dentro_de_zona(x: float, y: float, rect: Dict[str, float], tol: float = 0.0) -> bool:
    return (
        (rect["x_min"] - tol) <= x <= (rect["x_max"] + tol)
        and (rect["y_min"] - tol) <= y <= (rect["y_max"] + tol)
    )
    
def rango_coordenadas(x, y, objetivo, tol_default=10):
    tol = objetivo.get("tolerance", tol_default)
    if objetivo.get("start_x") is None or objetivo.get("start_y") is None:
        return True
    return abs(x - objetivo["start_x"]) <= tol and abs(y - objetivo["start_y"]) <= tol

def _team_allows(event_team_id, equipo_actual, rule: str | None) -> bool: # rule: "same" | "opponent" | "any" | None
    
    if rule is None or rule == "same":
        return (equipo_actual is None) or (event_team_id == equipo_actual)
    if rule == "opponent":
        return (equipo_actual is not None) and (event_team_id != equipo_actual)
    if rule == "any":
        return True
    return True

def _is_switch_trigger(ev: dict, posesion_anterior: int | None) -> bool:  #Cuando cambia de equipo
    
    t = _norm(ev.get("type_name"))
    
    # Intercepción exitosa
    if t == "interception":
        try:
            if is_interception_success(ev):
                return True
        except Exception:
            pass
        
    # Duelo ganado con cambio de posesión (robo)
    if t == "duel":
        try:
            
            if is_duel_won(ev) and posesion_anterior is not None and ev.get("possession_team_id") != posesion_anterior:
                return True
        except Exception:
            pass
    if t == "ball recovery":
        return True
    # Parada del portero (evento de portero “exitoso”)
    if t in ("goal keeper", "goalkeeper"):
        try:
            if is_success(ev):
                return True
        except Exception:
            out = _norm(ev.get("gk_outcome_name"))
            if out in {"saved", "save", "collected", "claim", "caught", "success"}:
                return True
            
    # Detecta cambio explícito de equipo en la posesión
    if posesion_anterior is not None and ev.get("possession_team_id") != posesion_anterior:
        return True
    return False




def comprobar_evento(evento, objetivo, tolerancia=10):
    
    # tipo de evento (puede ser lista)
    tipos = objetivo["event"] if isinstance(objetivo["event"], list) else [objetivo["event"]]
    ev_type = _norm(evento["type_name"])
    has_xy = (evento.get("start_x") is not None and evento.get("start_y") is not None)
    tipos_norm = [_norm(t) for t in tipos]
    
    if ev_type not in tipos_norm:
        return False

    # si hay patrón de juego, comprobarlo
    if objetivo.get("play_pattern"):
        if not evento["play_pattern_name"] or _norm(evento.get("play_pattern_name")) != _norm(objetivo["play_pattern"]):

            return False
    
    # si hay zona, comprobarla
    if objetivo.get("zone") is not None:
        tol_local = float(objetivo.get("tolerance") or 0.0)
        tol_glob = float(tolerancia or 0.0)
        tol = max(tol_local, tol_glob)
        zona = ver_zona(objetivo["zone"])
        if zona is not None:
            if has_xy:
                if not dentro_de_zona(evento["start_x"], evento["start_y"], zona, tol):
                    return False
            else:
                if not is_foul(evento):
                    return False

    if objetivo.get("start_x") is not None and objetivo.get("start_y") is not None:
        zona = ver_zona(objetivo["zone"])
        tol_local = float(objetivo.get("tolerance") or 0.0)
        tol_glob = float(tolerancia or 0.0)
        tol = max(tol_local, tol_glob)
        
        if zona is not None:
            if has_xy:
                if not dentro_de_zona(evento["start_x"], evento["start_y"], zona, tol):
                    return False
            else:
                if not is_foul(evento):
                    return False

    if "goal" in objetivo:
        if ev_type != "shot":
            return False
        if bool(objetivo["goal"]) != is_goal(evento):
            return False

    # outcome: "won"/"lost"/"success"/"blocked"/...
    o1 = objetivo.get("outcome")
    oN = objetivo.get("outcomes") or []
    if isinstance(o1, list):
        oN = oN + o1
        o1 = None

    if o1 is not None:
        if not matches_outcome(evento, o1):
            return False

    if oN:
        if not any(matches_outcome(evento, o) for o in oN):
            return False

    # success: True/False (genérico por tipo de evento)
    if "success" in objetivo:
        if bool(objetivo["success"]) != is_success(evento):
            return False
    
    if ev_type == "foul won":
        if "foul_advantage" in objetivo:
            if bool(objetivo["foul_advantage"]) != bool(evento.get("foul_won_advantage")):
                return False
        if "foul_penalty" in objetivo:
            if bool(objetivo["foul_penalty"]) != bool(evento.get("foul_won_penalty")):
                return False
    return True

def preprocesar_secuencia(secuencia):
    
    tipos = []
    
    _sec_norm = []
    for step in (secuencia or []):
        step = step = dict(step) if isinstance(step, dict) else (dict(step) if step else {})
        ev = step.get("event")
        
        if isinstance(ev, str):
            if _norm(ev) == "recovery":
                st = dict(step)
                st["event"] = ["Ball Recovery", "Interception", "Duel"]
                if "success" not in st:
                    st["success"] = True
                if "switch_possession" not in st:
                    st["switch_possession"] = True
                # outcomes no tienen sentido en el macro → se ignoran
                st.pop("outcome", None)
                st.pop("outcomes", None)
                step = st    
                
        elif isinstance(ev, list) and ("Recovery" in ev):
            st = dict(step)
            new_ev = [t for t in ev if t != "Recovery"]
            new_ev.extend(["Ball Recovery", "Interception", "Duel"])
            st["event"] = new_ev
            if "success" not in st:
                st["success"] = True
            if "switch_possession" not in st:
                st["switch_possession"] = True
            st.pop("outcome", None)
            st.pop("outcomes", None)
            step = st
                    
        _sec_norm.append(step)
        
        ev_final = step.get("event")
        
        
        if isinstance(ev_final, list):
            for t in ev_final:
                tipos.append(t)
                    
        elif ev_final:
            tipos.append(ev_final)
                
    
    nueva = []
    i = 0
    while i < len(_sec_norm):
        actual = _sec_norm[i]
        siguiente = _sec_norm[i+1] if i+1 < len(_sec_norm) else None

        ev_val = actual.get("event")
        ev_norm = _norm(ev_val) if isinstance(ev_val, str) else None
        sig_norm = _norm(siguiente.get("event")) if (siguiente and isinstance(siguiente.get("event"), str)) else None
        
        if ev_norm == "foul":
            act = dict(actual)
            act["event"] = ["Foul Won", "Foul Committed"]
            nueva.append(act)
            # asegúrate de que ambos están en 'tipos'
            tipos.extend(["Foul Won", "Foul Committed"])
            i += 1
            continue    
        
                    
        # Detectar combo Pass → Shot
        if ev_norm == "pass" and siguiente and sig_norm == "shot":
            
            tipos.append("Shot")
            combo = {"event": "Pass→Shot", "combo": True}

            # Si el primer evento tiene play_pattern, lo mantenemos
            if actual.get("play_pattern"):
                combo["play_pattern"] = actual["play_pattern"]

            # Si el primer evento tiene coords o tolerancia, también
            for param in ["start_x", "start_y", "tolerance", "zone"]:
                if actual.get(param) is not None:
                    combo[param] = actual[param]

            nueva.append(combo)
            i += 2  # saltamos dos
            
            continue

        nueva.append(actual)
        i += 1
                
    if tipos:
        seen = set()
        tipos = [t for t in tipos if not (t in seen or seen.add(t))]
        
    return {"secuencia": nueva, "tipos": tipos}

def motor_busqueda_avanzado(db_path='futbol.db', secuencia=None,  match_id=None, team_id=None, play_pattern=None, competition=None, tolerancia=10, margen_tiempo=30, filtros: Optional[Dict[str, Any]] = None):
    
    
    prep = preprocesar_secuencia(secuencia or [])
    secuencia = prep["secuencia"]
    tipos = prep["tipos"]
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
        
    query_esqueleto= """
            SELECT e.event_id, e.match_id, e.type_name, e.play_pattern_name,
                e.ts_abs, e.team_id, c.competition_name, e.player_name, e.player_id, 
                
                e.possession_team_id AS possession_team_id,
                
                COALESCE(p.start_x, s.start_x, d.start_x, ca.start_x, du.start_x, br.start_x, brcv.start_x) AS start_x,
                COALESCE(p.start_y, s.start_y, d.start_y, ca.start_y, du.start_y, br.start_y, brcv.start_y) AS start_y, 
                
                p.shot_assist            AS pass_is_shot_assist,
                p.shot_assist_id         AS pass_shot_assist_id,
                s.goal                   AS shot_goal,
                s.outcome                AS shot_outcome_name,
                d.outcome                AS dribble_outcome_name,
                du.outcome               AS duel_outcome_name,
                p.outcome_name           AS pass_outcome_name,
                inter.outcome            AS interception_outcome_name,
                fw.advantage             AS foul_won_advantage,
                fw.penalty               AS foul_won_penalty,
                fc.offensive             AS foul_committed_offensive,
                fc.penalty               AS foul_committed_penalty,
                fc.card                  AS foul_committed_card,
                gk.outcome               AS gk_outcome_name,
                br.outcome               AS ball_receipt_outcome_name,
                brcv.recovery_failure    AS ball_recovery_failure,
                brcv.offensive           AS ball_recovery_offensive,
                brcv.counterpress        AS ball_recovery_counterpress
                
                FROM events e
                JOIN matches m                  ON m.match_id = e.match_id
                JOIN competitions c             ON c.competition_id = m.competition_id
                                                AND c.season_id = m.season_id
                                                
                LEFT JOIN passes   p            ON p.event_id = e.event_id
                LEFT JOIN shots    s            ON s.event_id = e.event_id
                LEFT JOIN dribbles d            ON d.event_id = e.event_id
                LEFT JOIN carries  ca           ON ca.event_id = e.event_id
                LEFT JOIN duels    du           ON du.event_id = e.event_id
                LEFT JOIN goalkeeper gk         ON gk.event_id = e.event_id
                LEFT JOIN interceptions inter   ON inter.event_id = e.event_id
                LEFT JOIN fouls_won      fw     ON fw.event_id = e.event_id
                LEFT JOIN fouls_committed fc    ON fc.event_id = e.event_id
                LEFT JOIN ball_receipts   br   ON br.event_id   = e.event_id
                LEFT JOIN ball_recoveries brcv ON brcv.event_id = e.event_id
    """
    
    
    params, conds = [], []
    
    if match_id:
        conds.append("e.match_id = ?")
        params.append(match_id)

    if competition:
        conds.append("LOWER(c.competition_name) = ?")
        params.append(_norm(competition))
    
    if team_id:
        conds.append("e.team_id = ?")
        params.append(team_id)

    if play_pattern:
        conds.append("LOWER(e.play_pattern_name) = ?")
        params.append(_norm(play_pattern))
    
    if tipos:
        placeholders = ",".join(["?"] * len(tipos))
        conds.append(f"LOWER(e.type_name) IN ({placeholders})")
        params.extend([_norm(t) for t in tipos])
    
    if filtros:
        # lista de partidos
        mids = filtros.get("match_ids")
        if mids:
            # admite [{id:..}] o [ids] por seguridad
            if isinstance(mids, list) and mids and isinstance(mids[0], dict):
                mids = [m.get("id") for m in mids if m.get("id") is not None]
            if mids:
                conds.append(f"e.match_id IN ({','.join(['?']*len(mids))})")
                params.extend(mids)
        # equipo
        if filtros.get("team_id") is not None:
            conds.append("e.team_id = ?")
            params.append(int(filtros["team_id"]))
        # jugador
        if filtros.get("player_id") is not None:
            conds.append("e.player_id = ?")
            params.append(int(filtros["player_id"]))

    if conds:
        query_esqueleto += " WHERE " + " AND ".join(conds)
    
    query_esqueleto += " ORDER BY e.match_id, e.ts_abs"
    
    
    cursor.execute(query_esqueleto, params)
    eventos = cursor.fetchall()
    
    
    resultados = []
    actual = []
    indice_obj = 0
    ultimo_tiempo = None
    partido_actual = None
    
    equipo_actual = None
    posesion_actual = None

            
    for e in eventos:
        
        evento = dict(e)
        
        # Si ya hemos completado la secuencia, ignorar eventos anteriores al último tiempo
        if ultimo_tiempo is not None and evento["ts_abs"] < ultimo_tiempo:
            continue
        
        # ¿hemos completado la secuencia justo en la iteración anterior?
        if indice_obj == len(secuencia):
            resultados.append(actual.copy())
            actual = []
            indice_obj = 0
            ultimo_tiempo = None
            equipo_actual = None
            posesion_actual = None 
            continue
        
        objetivo = secuencia[indice_obj] if indice_obj < len(secuencia) else None
        
        # Filtro por equipo 

        team_rule = (objetivo or {}).get("team")  # "same"|"opponent"|"any"|None
        if not _team_allows(evento["team_id"], equipo_actual, team_rule):
            continue  

        
        if ultimo_tiempo is not None:
            dt = evento["ts_abs"] - ultimo_tiempo
            if dt > margen_tiempo:
                # ventana expirada → reset
                actual = []
                indice_obj = 0
                ultimo_tiempo = None
                equipo_actual = None
                # seguimos con el stream
                continue
            
        
            
        if objetivo and objetivo.get("combo") and objetivo["event"] == "Pass→Shot" :
            
            if _norm(evento["type_name"]) == "pass" and int(evento.get("pass_is_shot_assist") or 0) == 1:
                
                if objetivo.get("play_pattern"):
                    ev_pp = (evento.get("play_pattern_name") or "").lower()
                    
                    if ev_pp != objetivo["play_pattern"].lower():
                        continue
                    
                    
                actual.append(evento)
                equipo_actual = evento["team_id"]
                posesion_actual = evento.get("possession_team_id")
                            
                        # Buscar el Shot asociado en la misma jugada
                cursor2 = conn.cursor()
                cursor2.execute("""
                            SELECT e.event_id, e.match_id, e.type_name, e.ts_abs, e.team_id,
                                e.player_name, e.player_id,
                                s.start_x, s.start_y,
                                s.goal    AS shot_goal,
                                s.outcome AS shot_outcome_name
                            FROM events e
                            JOIN shots s ON s.event_id = e.event_id
                            WHERE e.match_id = ? AND e.team_id = ? 
                            AND e.type_name = 'Shot' 
                            AND e.ts_abs >= ?
                            AND e.ts_abs <= ?
                            ORDER BY e.ts_abs ASC
                            LIMIT 1
                        """, (evento["match_id"], evento["team_id"], evento["ts_abs"], evento["ts_abs"] + margen_tiempo))
                shot = cursor2.fetchone()

                if not shot:
                    actual=[]
                    continue
                else:
                    shdict = dict(shot)
                        
                if "goal" in objetivo and bool(objetivo["goal"]) != bool(shdict.get("shot_goal")):
                    # no es el tipo de tiro que queremos (gol/no gol)
                    # reseteamos secuencia parcial
                    actual = []
                    continue
                        
                if objetivo.get("outcome"):
                    if _norm(shdict.get("shot_outcome_name")) != _norm(objetivo["outcome"]):
                        actual = []
                        continue
                            
                actual.append(shdict)
                            
                ultimo_tiempo = shdict["ts_abs"]
                            
                indice_obj += 1
                            
                if indice_obj == len(secuencia):
                    resultados.append(actual.copy())
                    actual, indice_obj, ultimo_tiempo, equipo_actual, posesion_actual = [], 0, None , None, None
                                
                            
                            
            continue

        if comprobar_evento(evento, objetivo, tolerancia=tolerancia):
            
            if (objetivo or {}).get("switch_possession"):
                if not _is_switch_trigger(evento, posesion_actual):
                    # este evento no supuso cambio de posesión → no vale para este paso
                    continue
                
            actual.append(evento)
            
            equipo_actual = evento["team_id"]
            posesion_actual = evento.get("possession_team_id")

            ultimo_tiempo = evento["ts_abs"]
            indice_obj += 1
            
            if indice_obj == len(secuencia):
                resultados.append(actual.copy())
                actual = []
                indice_obj = 0
                ultimo_tiempo = None
                equipo_actual = None 
                posesion_actual = None 
            
            continue
        
        if not (objetivo or {}).get("switch_possession") and _is_switch_trigger(evento, posesion_actual):
            actual = []
            indice_obj = 0
            ultimo_tiempo = None
            equipo_actual = None
            posesion_actual = None
            continue       
        
        if objetivo.get("optional"):
            indice_obj += 1
                
            if indice_obj == len(secuencia):
                resultados.append(actual.copy())
                actual = []
                indice_obj = 0
                ultimo_tiempo = None
                equipo_actual = None
                posesion_actual = None
            continue
    conn.close()
    
    return resultados

    
