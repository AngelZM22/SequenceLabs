import sqlite3

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

EVENTOS_RUIDO = {
    "Pressure", "Duel", "Foul Committed", "Foul Won",
    "Player On", "Player Off", "Substitution",
    "Injury Stoppage", "Referee Ball-Drop", "Tactical Shift"
}   

def dentro_de_zona(x, y, objetivo, tolerancia=10):
    return abs(x - objetivo["start_x"]) <= tolerancia and abs(y - objetivo["start_y"]) <= tolerancia

def rango_coordenadas(x, y, target, tol=10):
    if target.get("start_x") is None or target.get("start_y") is None:
        return True  # Sin restricción de coordenadas
    return abs(x - target["start_x"]) <= tol and abs(y - target["start_y"]) <= tol

def comprobar_evento(evento, objetivo, tolerancia=10):
    
    
    # tipo de evento (puede ser lista)
    tipos = objetivo["event"] if isinstance(objetivo["event"], list) else [objetivo["event"]]
    if evento["type_name"] not in tipos:
        return False

    # si hay patrón de juego, comprobarlo
    if objetivo.get("play_pattern"):
        if not evento["play_pattern_name"] or evento["play_pattern_name"].lower() != objetivo["play_pattern"].lower():

            return False
    
    # si hay zona, comprobarla
    if objetivo.get("zone") and not dentro_de_zona(evento["start_x"], evento["start_y"], objetivo["zone"]):
        return False

    # si hay coords, comprobarlas
    if not rango_coordenadas(evento["start_x"], evento["start_y"], objetivo, tolerancia):
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
        if (actual.get("event") == "Pass" and
            siguiente and siguiente.get("event") == "Shot"):
            
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
    
    
    secuencia, tipos = preprocesar_secuencia(secuencia).values()
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
        
    query_esqueleto= """
        SELECT e.event_id, e.match_id, e.type_name, e.play_pattern_name,
               e.ts_abs, e.team_id, c.competition_name, e.player_name, e.player_id, 
               COALESCE(p.start_x, s.start_x, d.start_x, ca.start_x, du.start_x) AS start_x,
               COALESCE(p.start_y, s.start_y, d.start_y, ca.start_y, du.start_y) AS start_y, 
               p.shot_assist,
               p.shot_assist_id,
               s.outcome AS shot_outcome,
               d.outcome AS dribble_outcome,
               p.outcome_name AS pass_outcome
        FROM events e
        JOIN matches m ON m.match_id = e.match_id
        JOIN competitions c ON c.competition_id = m.competition_id
        LEFT JOIN passes   p ON p.event_id = e.event_id
        LEFT JOIN shots    s ON s.event_id = e.event_id
        LEFT JOIN dribbles d ON d.event_id = e.event_id
        LEFT JOIN carries  ca ON ca.event_id = e.event_id
        LEFT JOIN duels    du ON du.event_id = e.event_id
        LEFT JOIN goalkeeper gk ON gk.event_id = e.event_id
        LEFT JOIN interceptions inter ON inter.event_id = e.event_id
    """
    
    
    params, conds = [], []
    
    if match_id:
        conds.append("e.match_id = ?")
        params.append(match_id)

    if competition:
        conds.append("c.competition_name = ?")
        params.append(competition)
    
    if team_id:
        conds.append("e.team_id = ?")
        params.append(team_id)

    if play_pattern:
        conds.append("e.play_pattern_name = ?")
        params.append(play_pattern)
    
    if tipos:
        placeholders = ",".join(["?"] * len(tipos))
        conds.append(f"e.type_name IN ({placeholders})")
        params.extend(tipos)
        
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
            
            if evento["type_name"] == "Pass" and evento.get("shot_assist") == 1:
                
                if objetivo.get("play_pattern"):
                    ev_pp = (evento.get("play_pattern_name") or "").lower()
                    
                    if ev_pp != objetivo["play_pattern"].lower():
                        pass
                    
                    else:
                        actual.append(evento)
                        if equipo_actual is None:
                            equipo_actual = evento["team_id"]
                            
                        # Buscar el Shot asociado en la misma jugada
                        cursor2 = conn.cursor()
                        cursor2.execute("""
                            SELECT e.event_id, e.match_id, e.type_name, e.ts_abs, e.team_id,
                                e.player_name, e.player_id,
                                s.start_x, s.start_y
                            FROM events e
                            JOIN shots s ON s.event_id = e.event_id
                            WHERE e.match_id = ? AND e.team_id = ? 
                            AND e.type_name = 'Shot' 
                            AND e.ts_abs >= ?
                            ORDER BY e.ts_abs ASC
                            LIMIT 1
                        """, (evento["match_id"], evento["team_id"], evento["ts_abs"]))
                        shot = cursor2.fetchone()

                        if shot:
                            shdict = dict(shot)
                            actual.append(shdict)
                            
                            ultimo_tiempo = shdict["ts_abs"]
                            
                            indice_obj += 1
                            
                            if indice_obj == len(secuencia):
                                resultados.append(actual.copy())
                                actual, indice_obj, ultimo_tiempo, equipo_actual = [], 0, None , None
                                
                                continue
                            
                            continue
                        
                else:
                    
                    actual.append(evento)
                    
                    if equipo_actual is None:
                        equipo_actual = evento["team_id"]

                    # Buscar el Shot asociado en la misma jugada
                    cursor2 = conn.cursor()
                    cursor2.execute("""
                        SELECT e.event_id, e.match_id, e.type_name, e.ts_abs, e.team_id,
                            e.player_name, e.player_id,
                            s.start_x, s.start_y
                        FROM events e
                        JOIN shots s ON s.event_id = e.event_id
                        WHERE e.match_id = ? AND e.team_id = ? 
                        AND e.type_name = 'Shot' 
                        AND e.ts_abs >= ?
                        ORDER BY e.ts_abs ASC
                        LIMIT 1
                    """, (evento["match_id"], evento["team_id"], evento["ts_abs"]))
                    shot = cursor2.fetchone()
                    
                    if shot:
                            shdict = dict(shot)
                            actual.append(shdict)
                            
                            ultimo_tiempo = shdict["ts_abs"]
                            
                            indice_obj += 1
                            
                            if indice_obj == len(secuencia):
                                resultados.append(actual.copy())
                                actual, indice_obj, ultimo_tiempo, equipo_actual = [], 0, None , None
                                
                                continue
                            
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

    
