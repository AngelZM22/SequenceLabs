import sqlite3
from helpers import normalize_text as _norm
from helpers import norm_equals as _norm_equals
from helpers import norm_in as _norm_in
from services.helpers import _outcome_of, is_duel_won, is_goal, is_interception_success, is_recovery, is_shot, is_won_outcome, is_success, matches_outcome
from typing import List, Dict, Any
DEBUG_FILE = "debug_log.txt"

def dlog(*args):
    """Escribe logs de depuración en un archivo de texto (append)."""
    try:
        with open(DEBUG_FILE, "a", encoding="utf-8") as f:
            print(*args, file=f)
    except Exception as e:
        # Evitar que un fallo de logging rompa el motor
        pass
# ------------------------



ZONES = {
    "own_half": lambda x, y: x < 60,
    "opponent_half": lambda x, y: x >= 60,
    "final_third": lambda x, y: x >= 80,

    # Área grande
    "box_right": lambda x, y: 102 <= x <= 120 and 18 <= y <= 62,
    "box_left": lambda x, y: 0 <= x <= 18 and 18 <= y <= 62,

    # Área pequeña ""
    "six_yard_right": lambda x, y: 114 <= x <= 120 and 30 <= y <= 50,
    "six_yard_left": lambda x, y: 0 <= x <= 6 and 30 <= y <= 50,

    # Córners
    "corner_top_left": lambda x, y: x <= 2 and y <= 2,
    "corner_bottom_left": lambda x, y: x <= 2 and y >= 78,
    "corner_top_right": lambda x, y: x >= 118 and y <= 2,
    "corner_bottom_right": lambda x, y: x >= 118 and y >= 78,
}

EXPANSIONES = {

    "Dribble": ["Carry"],      # tras un regate suele venir una conducción
    
}

SUCCESS_OUTCOMES = {"won", "success", "successful", "complete"}  # amplía si lo necesitas

EVENTOS_RUIDO = {
    "Pressure", "Duel", "Foul Committed", "Foul Won",
    "Player On", "Player Off", "Substitution",
    "Injury Stoppage", "Referee Ball-Drop", "Tactical Shift"
}   


def dentro_de_zona(x, y, zone_name:str) -> bool:
    fn = ZONES.get(zone_name)
    if not fn:
        return True  # zona desconocida => no restringir
    return fn(x, y)

def rango_coordenadas(x, y, objetivo, tol_default=10):
    tol = objetivo.get("tolerance", tol_default)
    if objetivo.get("start_x") is None or objetivo.get("start_y") is None:
        return True
    return abs(x - objetivo["start_x"]) <= tol and abs(y - objetivo["start_y"]) <= tol

def comprobar_evento(evento, objetivo, tolerancia=10):
    
    # tipo de evento (puede ser lista)
    tipos = objetivo["event"] if isinstance(objetivo["event"], list) else [objetivo["event"]]
    ev_type = _norm(evento["type_name"])
    tipos_norm = [_norm(t) for t in tipos]
    
    if ev_type not in tipos_norm:
        return False

    # si hay patrón de juego, comprobarlo
    if objetivo.get("play_pattern"):
        if not evento["play_pattern_name"] or _norm(evento.get("play_pattern_name")) != _norm(objetivo["play_pattern"]):

            return False
    
    # si hay zona, comprobarla
    if objetivo.get("zone") and not dentro_de_zona(evento["start_x"], evento["start_y"], objetivo["zone"]):
        return False

    # si hay coords, comprobarlas
    if not rango_coordenadas(evento["start_x"], evento["start_y"], objetivo, tolerancia):
        return False

    if "goal" in objetivo:
        if _norm(evento["type_name"]) != "shot":
            return False
        if bool(objetivo["goal"]) != is_goal(evento):
            return False

    # outcome: "won"/"lost"/"success"/"blocked"/...
    if objetivo.get("outcome"):
        if not matches_outcome(evento, objetivo["outcome"]):
            return False

    # outcomes múltiples
    if objetivo.get("outcomes"):
        if not any(matches_outcome(evento, o) for o in objetivo["outcomes"]):
            return False

    # success: True/False (genérico por tipo de evento)
    if "success" in objetivo:
        if bool(objetivo["success"]) != is_success(evento):
            return False
        
    return True

def preprocesar_secuencia(secuencia):
    """
    Detecta patrones especiales (ej: Pass → Shot) y los convierte en combos.
    """
    tipos = []
    nueva = []
    i = 0
    while i < len(secuencia):
        actual = secuencia[i]
        siguiente = secuencia[i+1] if i+1 < len(secuencia) else None

        if actual.get("event"):
            tipos.append(actual["event"])
        
        
                    
        # Detectar combo Pass → Shot
        if _norm(actual.get("event")) == "pass" and siguiente and _norm(siguiente.get("event")) == "shot":
            
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
        
        if actual.get("event") in EXPANSIONES:
            for exp in EXPANSIONES[actual["event"]]:
                nueva.append({"event": exp, "synthetic": True})
                tipos.append(exp)
        i += 1
    return {"secuencia": nueva, "tipos": tipos}

def motor_busqueda_avanzado(db_path='futbol.db', secuencia=None,  match_id=None, team_id=None, play_pattern=None, competition=None, tolerancia=10, margen_tiempo=30):
    
    
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
               
               COALESCE(p.start_x, s.start_x, d.start_x, ca.start_x, du.start_x) AS start_x,
               COALESCE(p.start_y, s.start_y, d.start_y, ca.start_y, du.start_y) AS start_y, 
               
               p.shot_assist        AS pass_is_shot_assist,
               p.shot_assist_id     AS pass_shot_assist_id,
               s.goal               AS shot_goal,
               s.outcome            AS shot_outcome_name,
               d.outcome            AS dribble_outcome_name,
               du.outcome           AS duel_outcome_name,
               p.outcome_name       AS pass_outcome_name,
               inter.outcome        AS interception_outcome_name
               
        FROM events e
        JOIN matches m                  ON m.match_id = e.match_id
        JOIN competitions c             ON c.competition_id = m.competition_id
        LEFT JOIN passes   p            ON p.event_id = e.event_id
        LEFT JOIN shots    s            ON s.event_id = e.event_id
        LEFT JOIN dribbles d            ON d.event_id = e.event_id
        LEFT JOIN carries  ca           ON ca.event_id = e.event_id
        LEFT JOIN duels    du           ON du.event_id = e.event_id
        LEFT JOIN goalkeeper gk         ON gk.event_id = e.event_id
        LEFT JOIN interceptions inter   ON inter.event_id = e.event_id
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
            continue
        
        objetivo = secuencia[indice_obj] if indice_obj < len(secuencia) else None
        
        # Filtro por equipo (si ya se ha establecido)

        if equipo_actual is not None and evento["team_id"] != equipo_actual:

            # ¿El próximo paso es GK opcional? (útil si saltas el opcional)
            prox = secuencia[indice_obj] if indice_obj < len(secuencia) else None
            
            # ¿Se permite rival por ser GK?
            paso_permite_gk = bool(objetivo and objetivo.get("event") == "Goal Keeper")
            
            prox_gk_opt = bool(prox and prox.get("event") == "Goal Keeper" and prox.get("optional"))

            if not (paso_permite_gk or prox_gk_opt):
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
                if equipo_actual is None:
                    equipo_actual = evento["team_id"]
                            
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
                            ORDER BY e.ts_abs ASC
                            LIMIT 1
                        """, (evento["match_id"], evento["team_id"], evento["ts_abs"] + margen_tiempo))
                    shot = cursor2.fetchone()

                    if shot:
                        shdict = dict(shot)
                        
                        if "goal" in objetivo and bool(objetivo["goal"]) != bool(shdict.get("shot_goal")):
                            # no es el tipo de tiro que queremos (gol/no gol)
                            # reseteamos secuencia parcial
                            actual = []
                            continue
                        
                        if objetivo.get("outcome"):
                            if _norm(shdict.get("shot_outcome_name") or "") != _norm(objetivo["outcome"]):
                                actual = []
                                continue
                            
                        actual.append(shdict)
                            
                        ultimo_tiempo = shdict["ts_abs"]
                            
                        indice_obj += 1
                            
                        if indice_obj == len(secuencia):
                            resultados.append(actual.copy())
                            actual, indice_obj, ultimo_tiempo, equipo_actual = [], 0, None , None
                                
                            
                            
                        continue
                        
                

        if comprobar_evento(evento, objetivo, tolerancia=tolerancia):
            
            actual.append(evento)
            
            if equipo_actual is None:
                equipo_actual = evento["team_id"]
                
            ultimo_tiempo = evento["ts_abs"]
            indice_obj += 1
            
            if indice_obj == len(secuencia):
                resultados.append(actual.copy())
                actual = []
                indice_obj = 0
                ultimo_tiempo = None
            
            continue
                
        if objetivo.get("optional"):
            indice_obj += 1
                
            if indice_obj == len(secuencia):
                resultados.append(actual.copy())
                actual = []
                indice_obj = 0
                ultimo_tiempo = None
                equipo_actual = None
            continue
    conn.close()
    
    return resultados

    
