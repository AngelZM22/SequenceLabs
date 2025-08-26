import sqlite3

ZONES = {
    "own_half": lambda x, y: x < 60,
    "opponent_half": lambda x, y: x >= 60,
    "final_third": lambda x, y: x >= 80,

    # Área grande
    "box_right": lambda x, y: 102 <= x <= 120 and 18 <= y <= 62,
    "box_left": lambda x, y: 0 <= x <= 18 and 18 <= y <= 62,

    # Área pequeña
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

def motor_busqueda_avanzado(db_path='futbol.db', secuencia=None,  match_id=None, competition=None, tolerancia=10, margen_tiempo=30):
    
    secuencia, tipos = preprocesar_secuencia(secuencia).values()
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
        
    query_esqueleto= """
        SELECT e.event_id, e.match_id, e.type_name, e.play_pattern_name,
               e.ts_abs, e.team_id, c.competition_name,
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
    """
    
    
    params, conds = [], []
    
    if match_id:
        conds.append("e.match_id = ?")
        params.append(match_id)

    if competition:
        conds.append("c.competition_name = ?")
        params.append(competition)
    
    primer_evento = secuencia[0]
    
    if primer_evento.get("play_pattern"):
        conds.append("e.play_pattern_name = ?")
        params.append(primer_evento["play_pattern"])
    
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
        
        if partido_actual is None or partido_actual != evento["match_id"]:
            actual = []
            indice_obj = 0
            ultimo_tiempo = None
            partido_actual = evento["match_id"]
        
        if indice_obj >= len(secuencia):
            actual = []
            indice_obj = 0
            ultimo_tiempo = None
            continue
        
        objetivo = secuencia[indice_obj] if indice_obj < len(secuencia) else None
        
        if equipo_actual is None and objetivo and comprobar_evento(evento, objetivo, tolerancia):
            equipo_actual = evento["team_id"]

        if equipo_actual is not None and evento["team_id"] != equipo_actual:
            # Evento de otro equipo → lo ignoramos como ruido
            continue
        
        if objetivo.get("combo") and objetivo["event"] == "Pass→Shot" :
            if evento["type_name"] == "Pass" and evento.get("shot_assist") == 1:
                # Añadimos el pase
                actual.append(evento)

                # Buscar el Shot asociado en la misma jugada
                cursor2 = conn.cursor()
                cursor2.execute("""
                    SELECT e.event_id, e.match_id, e.type_name, e.ts_abs, e.team_id,
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
                    actual.append(dict(shot))

                # Avanzamos 1 posición en la secuencia (combo = 2 pasos de golpe)
                indice_obj += 1
                ultimo_tiempo = evento["ts_abs"]

                # Secuencia completa
                if indice_obj == len(secuencia):
                    resultados.append(actual.copy())
                    actual, indice_obj, ultimo_tiempo, equipo_actual = [], 0, None, None
            continue

        if comprobar_evento(evento, objetivo, tolerancia=tolerancia):
            
            if ultimo_tiempo is not None and (evento["ts_abs"] - ultimo_tiempo) > margen_tiempo:
                actual = []
                indice_obj = 0
                ultimo_tiempo = None
                continue
            
            actual.append(evento)
            ultimo_tiempo = evento["ts_abs"]
            indice_obj += 1
            
            if indice_obj == len(secuencia):
                resultados.append(actual.copy())
                actual = []
                indice_obj = 0
                ultimo_tiempo = None
                
            
            if indice_obj == len(secuencia):
                resultados.append(actual.copy())
                actual = []
                indice_obj = 0
                ultimo_tiempo = None
                
        else:
            if objetivo.get("optional"):
                indice_obj += 1
                
            else:
                actual = []
                indice_obj = 0
                ultimo_tiempo = None                    
    
    conn.close()
    return resultados
    
