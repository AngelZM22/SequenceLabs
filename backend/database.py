import sqlite3
import json
import os
import glob
from uuid import uuid4

from typing import Any, Dict, List, Optional


# Rutas del proyecto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_ROOT, "data","futbol.db")
JSON_PATH = os.path.join(PROJECT_ROOT, "data")

def conectar():
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    print("Intentando abrir base de datos en:", DATA_PATH)
    conn = sqlite3.connect(DATA_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")   
    return conn

def crear_tablas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    match_id INTEGER,
    team_id INTEGER,
    team_name TEXT,
    player_id INTEGER,
    player_name TEXT,
    type_id INTEGER,
    type_name TEXT,
    period INTEGER,
    minute INTEGER,
    second INTEGER,
    timestamp TEXT,
    ts_abs REAL,
    possession INTEGER,
    possession_team_id INTEGER,
    possession_team_name TEXT,
    play_pattern_id INTEGER,
    play_pattern_name TEXT, 
    duration REAL,
    FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS passes (
        event_id TEXT PRIMARY KEY,
        receiver_name TEXT,
        start_x REAL,
        start_y REAL,
        end_x REAL,
        end_y REAL,
        pass_type TEXT,
        height TEXT,
        cross BOOLEAN,
        body_part TEXT,
        shot_assist BOOLEAN,
        shot_assist_id TEXT,
        goal_assist BOOLEAN,
        outcome_name TEXT,
        FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS shots (
        event_id TEXT PRIMARY KEY,
        goal BOOLEAN,
        shot_type TEXT,
        start_x REAL,
        start_y REAL,
        end_x REAL,
        end_y REAL,
        body_part TEXT,
        first_time BOOLEAN,
        technique TEXT,
        outcome TEXT,
        FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS dribbles (
        event_id TEXT PRIMARY KEY,
        start_x REAL,
        start_y REAL,
        end_x REAL,
        end_y REAL,
        outcome TEXT,
        nutmeg BOOLEAN,
        FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS carries (
        event_id TEXT PRIMARY KEY,
        start_x REAL,
        start_y REAL,
        end_x REAL,
        end_y REAL,
        FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS duels (
        event_id TEXT PRIMARY KEY,
        start_x REAL,
        start_y REAL,
        duel_type TEXT,
        outcome TEXT,
        counterpress BOOLEAN,
        FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS goalkeeper (
        event_id TEXT PRIMARY KEY,
        gk_type TEXT,
        technique TEXT,
        body_part TEXT,
        outcome TEXT,
        FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS interceptions (
        event_id TEXT PRIMARY KEY,
        outcome TEXT,
        FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS fouls_committed (
        event_id TEXT PRIMARY KEY,
        offensive BOOLEAN,
        penalty BOOLEAN,
        card TEXT,
        FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS fouls_won (
        event_id TEXT PRIMARY KEY,
        advantage BOOLEAN,
        penalty BOOLEAN,
        FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS ball_receipts (
    event_id TEXT PRIMARY KEY,
    start_x REAL,
    start_y REAL,
    outcome TEXT,                
    FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS ball_recoveries (
        event_id TEXT PRIMARY KEY,
        start_x REAL,
        start_y REAL,
        recovery_failure BOOLEAN,    -- True si falla la recuperación (si viene en datos)
        offensive BOOLEAN,           -- si viene en ball_recovery.offensive
        counterpress BOOLEAN,        -- hereda del root event.get("counterpress", False)
        FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
    )''')
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS related_events (
        event_id TEXT NOT NULL,
        related_event_id TEXT NOT NULL,
        PRIMARY KEY (event_id, related_event_id),
        FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE,
        FOREIGN KEY(related_event_id) REFERENCES events(event_id) ON DELETE CASCADE
    );
    """)

    cursor.execute('''CREATE TABLE IF NOT EXISTS competitions (
        competition_id INTEGER,
        season_id INTEGER,
        competition_name TEXT,
        competition_gender TEXT,
        competition_youth TEXT,
        competition_international BOOLEAN,
        match_updated TIMESTAMP, 
        match_updated_360 TIMESTAMP, 
        match_available TIMESTAMP, 
        match_available_360 TIMESTAMP, 
        season_name TEXT,
        country_name TEXT,
        PRIMARY KEY (competition_id, season_id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS matches (
        match_id INTEGER PRIMARY KEY,
        match_date TEXT,
        home_team TEXT,
        away_team TEXT,
        home_score INTEGER,
        away_score INTEGER,
        competition_id INTEGER,
        season_id INTEGER,
        FOREIGN KEY (competition_id, season_id) REFERENCES competitions(competition_id, season_id) ON DELETE CASCADE
    )''')
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS player_match_team (
        player_id INTEGER NOT NULL,
        match_id INTEGER NOT NULL,
        team_id INTEGER NOT NULL,
        jersey_number INTEGER,
        position_name TEXT,
        match_date TEXT,
        PRIMARY KEY (player_id, match_id),
        FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE
    );
    """)

    cursor.execute('''CREATE TABLE IF NOT EXISTS three_sixty (
        event_uuid TEXT PRIMARY KEY,
        visible_area TEXT,
        FOREIGN KEY (event_uuid) REFERENCES events(event_id) ON DELETE CASCADE
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS freeze_frame (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_uuid TEXT,
        teammate INTEGER,
        actor INTEGER,
        keeper INTEGER,
        location_x REAL,
        location_y REAL,
        FOREIGN KEY (event_uuid) REFERENCES three_sixty(event_uuid) ON DELETE CASCADE
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS lineup (
        match_id INTEGER NOT NULL,
        team_id INTEGER NOT NULL,
        team_name TEXT,
        player_id INTEGER NOT NULL,
        player_name TEXT,
        jersey_number INTEGER,
        position_name TEXT,
        PRIMARY KEY (match_id, player_id),
        FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE
    )''')
    
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comp_season (
      competition_id INTEGER NOT NULL,
      season_id      INTEGER NOT NULL,
      competition_name TEXT NOT NULL,
      season_name      TEXT NOT NULL,
      PRIMARY KEY (competition_id, season_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS team_comp_season (
      competition_id INTEGER NOT NULL,
      season_id      INTEGER NOT NULL,
      team_id        INTEGER NOT NULL,
      team_name      TEXT NOT NULL,
      PRIMARY KEY (competition_id, season_id, team_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS player_team_season (
      team_id    INTEGER NOT NULL,
      season_id  INTEGER NOT NULL,
      player_id  INTEGER NOT NULL,
      player_name TEXT,
      PRIMARY KEY (team_id, season_id, player_id)
    )
    """)

    conn.commit()
    conn.close()

def create_search_indexes():
    
    # Índices para optimizar consultas
    conn = conectar()
    cursor = conn.cursor()

    # EVENTS: filtros + ordenación del motor
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_match_time ON events(match_id, ts_abs);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_match_team_time ON events(match_id, team_id, ts_abs)")
    
    # Si filtras sólo por team_id (sin match), ayuda 
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_team_match_time ON events(team_id, match_id, ts_abs)")
    
    # Tipos y patrones: (IN sobre type_name) y a veces play_pattern_name
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type_pattern ON events(type_name, play_pattern_name)")
    
    # Consultas por patron sin tipo
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_play_pattern ON events(play_pattern_name)")
    
    # Busquedas por jugador
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_player_match_time ON events(player_id, match_id, ts_abs)")
    
    # Joins/Consultas auxiliares
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(type_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_match_poss_time ON events(match_id, possession, ts_abs)")
    
    # Related events
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_related_event ON related_events(event_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_related_related ON related_events(related_event_id)")
    
    # Lineup / player_match_team
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lineup_match_team ON lineup(match_id, team_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pmt_player ON player_match_team(player_id)") 
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pmt_match ON player_match_team(match_id)")
    
    # Matches
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_comp_season ON matches(competition_id, season_id)")

    # Ball Receipts
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ball_receipts_event ON ball_receipts(event_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ball_receipts_outcome ON ball_receipts(outcome)")
    
    # Ball Recoveries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ball_recoveries_event ON ball_recoveries(event_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ball_recoveries_failure ON ball_recoveries(recovery_failure)")
    
    # Competiciones, equipos, jugadores
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cs_name ON comp_season(competition_name, season_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tcs_cs ON team_comp_season(competition_id, season_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pts_team_season ON player_team_season(team_id, season_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_comp_season_date ON matches(competition_id, season_id, match_date)")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_comp_season ON matches(competition_id, season_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_team ON events(team_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_player ON events(player_id)")

    
    conn.commit()
    conn.close()
    print("Índices creados correctamente")
    
def importar_json():
    conn = conectar()
    cursor = conn.cursor()

    # Limpiar datos previos
    cursor.executescript("""
    DELETE FROM freeze_frame;
    DELETE FROM three_sixty;
    DELETE FROM lineup;
    DELETE FROM matches;
    DELETE FROM competitions;
    DELETE FROM events;
    DELETE FROM shots;
    DELETE FROM passes;
    DELETE FROM carries;
    DELETE FROM dribbles;
    DELETE FROM interceptions;
    DELETE FROM goalkeeper;
    DELETE FROM duels;
    DELETE FROM fouls_committed;
    DELETE FROM fouls_won; 
    DELETE FROM ball_receipts;
    DELETE FROM ball_recoveries; 
    """)

    # Importar competiciones
    with open(os.path.join(JSON_PATH, "competitions.json"), "r", encoding="utf-8") as f:
        competitions = json.load(f)
        for comp in competitions:
            cursor.execute("""
            INSERT OR IGNORE INTO competitions (
                competition_id, competition_name, 
                country_name, 
                season_id, season_name,
                competition_gender, competition_youth, competition_international,
                match_updated, match_updated_360,
                match_available, match_available_360
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (comp["competition_id"], comp["competition_name"], 
                 comp["country_name"],
                 comp["season_id"], comp["season_name"], 
                 comp.get("competition_gender"),comp.get("competition_youth"), comp.get("competition_international"),
                 comp.get("match_updated"), comp.get("match_updated_360"),
                 comp.get("match_available"), comp.get("match_available_360"))
            )


    # Importar partidos
    for archivo in glob.glob(os.path.join(JSON_PATH,"matches","*","*.json")):
        with open(archivo,"r",encoding="utf-8") as f:
            matches = json.load(f)
            for match in matches:
                cursor.execute("""
                    INSERT OR IGNORE INTO matches ( 
                    match_id, match_date, 
                    home_team, away_team, 
                    home_score, away_score,
                    competition_id, season_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                        match["match_id"], match["match_date"],
                        match["home_team"]["home_team_name"], match["away_team"]["away_team_name"],
                        match["home_score"], match["away_score"],
                        match["competition"]["competition_id"],match["season"]["season_id"]
                        ))


    # Importar eventos
    for archivo in glob.glob(os.path.join(JSON_PATH,"events","*.json")):
        with open(archivo, "r", encoding="utf-8") as f:
            events = json.load(f)
            match_id = int(os.path.splitext(os.path.basename(archivo))[0])
            related_buffer = []
            for event in events:
                event_id = str(event.get("id") or uuid4())
                player = event.get("player", {})
                possession_team = event.get("possession_team", {})
                play_pattern = event.get("play_pattern", {})
                team = event.get("team", {})
                type = event["type"]["name"]
                related = event.get('related_events', [])
                base_time = {1: 0, 2: 45*60, 3: 90*60, 4: 105*60}
                ts_abs = base_time.get(event.get("period"), 0) \
                            + (event.get("minute") or 0) * 60 \
                            + (event.get("second") or 0)

                
                cursor.execute('''INSERT INTO events (
                    event_id, match_id,
                    team_id, team_name,
                    player_id, player_name,
                    type_id, type_name,
                    period,
                    minute, second,
                    timestamp,
                    ts_abs,
                    possession, possession_team_id, possession_team_name,
                    play_pattern_id, play_pattern_name,
                    duration
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                    event_id,
                    match_id,
                    team.get("id"),
                    team.get("name"),
                    player.get("id"),
                    player.get("name"),
                    event.get("type", {}).get("id"),
                    event.get("type", {}).get("name"),
                    event.get("period"),
                    event.get("minute"),
                    event.get("second"),
                    event.get("timestamp"),
                    ts_abs,
                    event.get("possession"),
                    possession_team.get("id"),
                    possession_team.get("name"),
                    play_pattern.get("id"),
                    play_pattern.get("name"),
                    event.get("duration")
                    ))
                
                
                if related:
                    for rel in related:
                        #cursor.execute("""
                        #INSERT OR IGNORE INTO related_events (event_id, related_event_id)
                        #VALUES (?, ?)
                        #""", (event_id, rel))
                        related_buffer.append((event_id, rel))
                
                if event.get("tactics") and event["tactics"].get("lineup"):
                    for player in event["tactics"]["lineup"]:
                        
                        if player.get("id") is None:                # Evitar insertar jugadores sin ID, los jugadores sin ID son fallos.
                            continue
                    
                        cursor.execute('''INSERT INTO lineup (match_id, team_id, team_name, player_id, player_name, jersey_number, position_name) VALUES (?, ?, ?, ?, ?, ?, ?)''', (
                            match_id,
                            team.get("id"),
                            team.get("name"),
                            player.get("id"),
                            player.get("name"),
                            player.get("jersey_number"),
                            player.get("position",{}).get("name")
                        ))
            
                elif type == "Pass":
                    
                    loc = event.get("location", [None, None])
                    end_loc = event.get("pass",{}).get("end_location",[None, None])
                    pass_type = event.get("pass",{}).get("type",{}).get("name")
                    height = event.get("pass", {}).get("height", {}).get("name")
                    cross = event.get("pass", {}).get("cross", False)
                    body_part = event.get("pass", {}).get("body_part", {}).get("name")
                    shot_assist_id = event.get("pass", {}).get("assisted_shot_id", None)
                    shot_assist = event.get("pass", {}).get("shot_assist", False)
                    goal_assist = event.get("pass", {}).get("goal_assist", False)
                    outcome_name = event.get("pass", {}).get("outcome", {}).get("name")
                    cross = event.get("pass", {}).get("cross", False)
                    cursor.execute('''INSERT OR IGNORE INTO passes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                        event_id,
                        event.get("pass",{}).get("recipient",{}).get("name"),
                        loc[0], loc[1],
                        end_loc[0], end_loc[1],
                        pass_type,
                        height,
                        cross,
                        body_part,
                        shot_assist,
                        shot_assist_id,
                        goal_assist,
                        outcome_name,
                    ))    
                elif type == "Shot":
                    loc = event.get("location", [None, None])
                    end_loc = event.get("shot",{}).get("end_location",[None, None])
                    body_part = event.get("shot", {}).get("body_part", {}).get("name")
                    first_time = event.get("shot", {}).get("first_time", False)
                    technique = event.get("shot", {}).get("technique", {}).get("name")
                    outcome = event.get("shot", {}).get("outcome", {}).get("name")
                    shot_type = event.get("shot", {}).get("type", {}).get("name")
                    
                    cursor.execute('''INSERT OR IGNORE INTO shots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                        event_id,
                        outcome == "Goal",
                        shot_type,
                        loc[0], loc[1],
                        end_loc[0], end_loc[1],
                        body_part,
                        first_time,
                        technique,
                        outcome
                    ))
                    
                elif type == "Dribble":
                    loc = event.get("location", [None, None])
                    end_loc = event.get("dribble",{}).get("end_location",[None, None])
                    outcome = event.get("dribble",{}).get("outcome",{}).get("name")
                    nutmeg = event.get("dribble", {}).get("nutmeg", False)
                    cursor.execute('''INSERT OR IGNORE INTO dribbles VALUES (?, ?, ?, ?, ?, ?, ?)''', (
                        event_id,
                        loc[0], loc[1],
                        end_loc[0], end_loc[1],
                        outcome,
                        nutmeg
                    ))
                    
                elif type == "Carry":
                    loc = event.get("location", [None, None])
                    end_loc = event.get("carry",{}).get("end_location",[None, None])
                    cursor.execute('''INSERT OR IGNORE INTO carries VALUES (?, ?, ?, ?, ?)''', (
                        event_id,
                        loc[0], loc[1],
                        end_loc[0], end_loc[1]
                    ))
                    
                elif type == "Duel":
                    loc = event.get("location", [None, None])
                    duel_type = event.get("duel", {}).get("type")
                    if isinstance(duel_type, dict):
                        duel_type = duel_type.get("name")
                    outcome = event.get("duel",{}).get("outcome",{}).get("name")
                    cursor.execute('''INSERT OR IGNORE INTO duels VALUES (?, ?, ?, ?, ?, ?)''', (
                        event_id,
                        loc[0], loc[1],
                        duel_type,
                        outcome,
                        event.get("counterpress",False)
                    ))
                elif type == "Goal Keeper":
                    portero = event.get("goalkeeper",{})
                    cursor.execute('''INSERT OR IGNORE INTO goalkeeper VALUES (?, ?, ?, ?, ?)''', (
                        event_id,
                        portero.get("type",{}).get("name"),
                        portero.get("technique",{}).get("name"),
                        portero.get("body_part",{}).get("name"),
                        portero.get("outcome",{}).get("name")
                    ))
                elif type in ("Ball Receipt", "Ball Receipt*"):
                    loc = event.get("location", [None, None])
                    br = (event.get("ball_receipt", {}) or {})
                    outcome_name = (br.get("outcome", {}) or {}).get("name")  

                    cursor.execute('''INSERT OR IGNORE INTO ball_receipts VALUES (?, ?, ?, ?)''', (
                        event_id,
                        loc[0], loc[1],
                        outcome_name
                    ))

                elif type == "Ball Recovery":
                    loc = event.get("location", [None, None])
                    rec = (event.get("ball_recovery", {}) or {})
                    failure = bool(rec.get("recovery_failure", False))
                    offensive = bool(rec.get("offensive", False))
                    counterpress = bool(event.get("counterpress", False))

                    cursor.execute('''INSERT OR IGNORE INTO ball_recoveries VALUES (?, ?, ?, ?, ?, ?)''', (
                        event_id,
                        loc[0], loc[1],
                        failure,
                        offensive,
                        counterpress
                    ))  
                    
                elif type == "Interception":
                    outcome = event.get("interception",{}).get("outcome",{}).get("name")
                    cursor.execute('''INSERT OR IGNORE INTO interceptions VALUES (?, ?)''', (
                        event_id, outcome
                    ))
                elif type == "Foul Committed":
                    foul = event.get("foul_committed",{})
                    cursor.execute('''INSERT OR IGNORE INTO fouls_committed VALUES (?, ?, ?, ?)''', (
                        event_id,
                        foul.get("offensive",False),
                        foul.get("penalty",False),
                        foul.get("card",{}).get("name")   
                    ))
                elif type == "Foul Won":
                    foul = event.get("foul_won",{})
                    cursor.execute('''INSERT OR IGNORE INTO fouls_won VALUES (?, ?, ?)''', (
                        event_id,
                        foul.get("advantage",False),
                        foul.get("penalty",False),  
                    ))
        # Insertar relaciones cuando TODOS los events existen
        cursor.executemany("""
            INSERT OR IGNORE INTO related_events (event_id, related_event_id)
            VALUES (?, ?)
        """, related_buffer)

                        
    for archivo in glob.glob(os.path.join(JSON_PATH,"three-sixty","*.json")):
        try:                
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error en {archivo}:{e}")
            
        for entry in data:
            event_uuid = entry.get("event_uuid")
            if not event_uuid:
                continue  # nada que referenciar

            # ¿existe el evento?
            cursor.execute("SELECT 1 FROM events WHERE event_id = ? LIMIT 1", (event_uuid,))
            if cursor.fetchone() is None:
                # Opcional: log para depurar qué se queda fuera
                # print("360 sin evento base:", archivo, event_uuid)
                continue

            visible_area = json.dumps(entry.get("visible_area"))

            cursor.execute(
                '''INSERT OR IGNORE INTO three_sixty (event_uuid, visible_area) VALUES (?, ?)''',
                (event_uuid, visible_area)
            )

            for frame in entry.get("freeze_frame", []):
                cursor.execute('''INSERT OR IGNORE INTO freeze_frame
                                (event_uuid, teammate, actor, keeper, location_x, location_y)
                                VALUES (?, ?, ?, ?, ?, ?)''', (
                    event_uuid,
                    int(frame.get("teammate", False)),
                    int(frame.get("actor", False)),
                    int(frame.get("keeper", False)),
                    frame["location"][0],
                    frame["location"][1]
                ))
                    
    cursor.execute("""
    INSERT OR REPLACE INTO player_match_team (player_id, match_id, team_id, jersey_number, position_name, match_date)
    SELECT l.player_id, l.match_id, l.team_id, l.jersey_number, l.position_name, m.match_date
    FROM lineup l
    JOIN matches m ON m.match_id = l.match_id
    """)
    
    # Completar faltantes desde events (sin dorsal)
    cursor.execute("""
    INSERT OR IGNORE INTO player_match_team (player_id, match_id, team_id, match_date)
    SELECT DISTINCT e.player_id, e.match_id, e.team_id, m.match_date
    FROM events e
    JOIN matches m ON m.match_id = e.match_id
    WHERE e.player_id IS NOT NULL
    """)
    

    conn.commit()
    conn.close()
    refrescar()
    print("Datos importados correctamente.")



## ===================      Tablas  Derivadas       ================================= ##

def refrescar_comp_season():          # Vaciamos y rellenamos desde matches + competitions
    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM comp_season")
    cur.execute("""
      INSERT OR IGNORE INTO comp_season(competition_id, season_id, competition_name, season_name)
      SELECT DISTINCT 
             m.competition_id, 
             m.season_id,
             COALESCE(c.competition_name, '') AS competition_name,
             COALESCE(c.season_name,      '') AS season_name
      FROM matches m
      LEFT JOIN competitions c
        ON c.competition_id = m.competition_id AND c.season_id = m.season_id
      WHERE m.competition_id IS NOT NULL AND m.season_id IS NOT NULL
    """)
    conn.commit(); conn.close()


def refrescar_team_comp_season():             # Equipos que participaron en una competicion (derivado de events + matches)

    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM team_comp_season")
    cur.execute("""
      INSERT OR IGNORE INTO team_comp_season(competition_id, season_id, team_id, team_name)
      SELECT DISTINCT m.competition_id, m.season_id, e.team_id, e.team_name
      FROM events e
      JOIN matches m ON m.match_id = e.match_id
      WHERE e.team_id IS NOT NULL AND e.team_name IS NOT NULL
        AND m.competition_id IS NOT NULL AND m.season_id IS NOT NULL
    """)
    conn.commit(); conn.close()


def refrescar_player_team_season():               # Jugadores que jugaron en equipos, se rellena desde lineup (plantillas), sino desde events
    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM player_team_season")
    
    cur.execute("""
      INSERT OR IGNORE INTO player_team_season(team_id, season_id, player_id, player_name)
      SELECT DISTINCT l.team_id, m.season_id, l.player_id, COALESCE(l.player_name, e.player_name)
      FROM lineup l
      JOIN matches m ON m.match_id = l.match_id
      LEFT JOIN events e ON e.player_id = l.player_id AND e.team_id = l.team_id
      WHERE l.player_id IS NOT NULL AND l.team_id IS NOT NULL AND m.season_id IS NOT NULL
    """)
    cur.execute("""
      INSERT OR IGNORE INTO player_team_season(team_id, season_id, player_id, player_name)
      SELECT DISTINCT e.team_id, m.season_id, e.player_id, e.player_name
      FROM events e
      JOIN matches m ON m.match_id = e.match_id
      WHERE e.player_id IS NOT NULL AND e.team_id IS NOT NULL AND m.season_id IS NOT NULL
    """)
    conn.commit(); conn.close()
    
def refrescar():
    refrescar_comp_season()
    refrescar_team_comp_season()
    refrescar_player_team_season()


# HELPERS

def options_competitions(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT competition_id, competition_name
        FROM comp_season
        ORDER BY competition_name
    """)
    return [{"id": r[0], "label": r[1]} for r in cur.fetchall()]


def options_seasons(conn, competition_id: Optional[int] = None):
    cur = conn.cursor()
    if competition_id is None:
        cur.execute("""
          SELECT DISTINCT season_id,
                 COALESCE(season_name, CAST(season_id AS TEXT)) AS label
          FROM comp_season
          ORDER BY label
        """)
    else:
        cur.execute("""
          SELECT DISTINCT season_id,
                 COALESCE(season_name, CAST(season_id AS TEXT)) AS label
          FROM comp_season
          WHERE competition_id = ?
          ORDER BY label
        """, (competition_id,))
    return [{"id": r[0], "label": r[1]} for r in cur.fetchall()]


def options_teams(conn, competition_id: Optional[int] = None, season_id: Optional[int] = None):
    cur = conn.cursor()
    qs = ["SELECT DISTINCT team_id, team_name FROM team_comp_season WHERE 1=1"]
    args: list[int] = []
    if competition_id is not None:
        qs.append("AND competition_id = ?"); args.append(competition_id)
    if season_id is not None:
        qs.append("AND season_id = ?"); args.append(season_id)
    qs.append("ORDER BY team_name")
    cur.execute("\n".join(qs), tuple(args))
    return [{"id": r[0], "label": r[1]} for r in cur.fetchall()]


def options_players(conn, team_id: Optional[int] = None, season_id: Optional[int] = None):
    cur = conn.cursor()
    qs = ["SELECT DISTINCT player_id, COALESCE(player_name,'') AS label FROM player_team_season WHERE 1=1"]
    args: list[int] = []
    if team_id is not None:
        qs.append("AND team_id = ?"); args.append(team_id)
    if season_id is not None:
        qs.append("AND season_id = ?"); args.append(season_id)
    qs.append("ORDER BY label")
    cur.execute("\n".join(qs), tuple(args))
    return [{"id": r[0], "label": r[1]} for r in cur.fetchall()]


def options_matches(conn,
                    competition_id: Optional[int] = None,
                    season_id: Optional[int] = None,
                    team_id: Optional[int] = None) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    qs = ["""
      SELECT m.match_id,
             (COALESCE(DATE(m.match_date),'') || ' · ' ||
              COALESCE(m.home_team,'Home') || ' vs ' || COALESCE(m.away_team,'Away')) AS label
      FROM matches m
      WHERE 1=1
    """]
    args: List[int] = []

    if competition_id is not None:
        qs.append("AND m.competition_id = ?")
        args.append(competition_id)

    if season_id is not None:
        qs.append("AND m.season_id = ?")
        args.append(season_id)

    # ← CAMBIO CLAVE: filtrar por equipo usando player_match_team (no hay home_team_id/away_team_id en matches)
    if team_id is not None:
        qs.append("""
          AND EXISTS (
            SELECT 1
            FROM player_match_team pmt
            WHERE pmt.match_id = m.match_id
              AND pmt.team_id = ?
          )
        """)
        args.append(team_id)

    qs.append("ORDER BY m.match_date, m.match_id")
    cur.execute("\n".join(qs), tuple(args))
    return [{"id": r[0], "label": r[1]} for r in cur.fetchall()]






if __name__ == "__main__":
    crear_tablas()
    importar_json()
    refrescar()
    create_search_indexes()
