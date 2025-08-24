import sqlite3
import json
import os
import glob
from uuid import uuid4

# Rutas del proyecto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_ROOT, "data","futbol.db")
JSON_PATH = os.path.join(PROJECT_ROOT, "data")

def conectar():
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    print("Intentando abrir base de datos en:", DATA_PATH)
    return sqlite3.connect(DATA_PATH, check_same_thread=False)

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
    duration REAL
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
        length REAL,
        angle REAL,
        switch REAL,
        FOREIGN KEY (event_id) REFERENCES events(event_id)
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
        FOREIGN KEY (event_id) REFERENCES events(event_id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS dribbles (
        event_id TEXT PRIMARY KEY,
        start_x REAL,
        start_y REAL,
        end_x REAL,
        end_y REAL,
        outcome TEXT,
        nutmeg BOOLEAN,
        FOREIGN KEY (event_id) REFERENCES events(event_id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS carries (
        event_id TEXT PRIMARY KEY,
        start_x REAL,
        start_y REAL,
        end_x REAL,
        end_y REAL,
        FOREIGN KEY (event_id) REFERENCES events(event_id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS duels (
        event_id TEXT PRIMARY KEY,
        start_x REAL,
        start_y REAL,
        duel_type TEXT,
        outcome TEXT,
        counterpress BOOLEAN,
        FOREIGN KEY (event_id) REFERENCES events(event_id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS goalkeeper (
        event_id TEXT PRIMARY KEY,
        gk_type TEXT,
        technique TEXT,
        body_part TEXT,
        outcome TEXT,
        FOREIGN KEY (event_id) REFERENCES events(event_id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS interceptions (
        event_id TEXT PRIMARY KEY,
        outcome TEXT,
        FOREIGN KEY (event_id) REFERENCES events(event_id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS fouls_committed (
        event_id TEXT PRIMARY KEY,
        offensive BOOLEAN,
        penalty BOOLEAN,
        card TEXT,
        FOREIGN KEY (event_id) REFERENCES events(event_id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS fouls_won (
        event_id TEXT PRIMARY KEY,
        advantage BOOLEAN,
        penalty BOOLEAN,
        FOREIGN KEY (event_id) REFERENCES events(event_id)
    )''')
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS related_events (
        event_id TEXT NOT NULL,
        related_event_id TEXT NOT NULL,
        PRIMARY KEY (event_id, related_event_id),
        FOREIGN KEY(event_id) REFERENCES events(event_id),
        FOREIGN KEY(related_event_id) REFERENCES events(event_id)
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
        FOREIGN KEY (competition_id, season_id) REFERENCES competitions(competition_id, season_id)
    )''')
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS player_match_team (
        player_id INTEGER NOT NULL,
        match_id INTEGER NOT NULL,
        team_id INTEGER NOT NULL,
        jersey_number INTEGER,
        position_name TEXT,
        match_date TEXT,
        PRIMARY KEY (player_id, match_id)
    );
    """)

    cursor.execute('''CREATE TABLE IF NOT EXISTS three_sixty (
        event_uuid TEXT PRIMARY KEY,
        visible_area TEXT,
        FOREIGN KEY (event_uuid) REFERENCES events(event_id)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS freeze_frame (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_uuid TEXT,
        teammate INTEGER,
        actor INTEGER,
        keeper INTEGER,
        location_x REAL,
        location_y REAL,
        FOREIGN KEY (event_uuid) REFERENCES three_sixty(event_uuid)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS lineup (
        match_id INTEGER NOT NULL,
        team_id INTEGER NOT NULL,
        team_name TEXT,
        player_id INTEGER NOT NULL,
        player_name TEXT,
        jersey_number INTEGER,
        position_name TEXT,
        PRIMARY KEY (match_id, player_id)
    )''')
    
    # Índices para optimizar consultas
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_name ON events(player_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_id ON events(match_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_type_name ON events(type_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_match_ts ON events(match_id, ts_abs)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_match_player_ts ON events(match_id, player_id, ts_abs)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_match_poss_ts ON events(match_id, possession, ts_abs)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(type_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_related_event ON related_events(event_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_related_related ON related_events(related_event_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lineup_match_team ON lineup(match_id, team_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pmt_player ON player_match_team(player_id)")
    
    conn.commit()
    conn.close()

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
            for event in events:
                event_id = str(uuid4())
                player = event.get("player", {})
                possession_team = event.get("possession_team", {})
                play_pattern = event.get("play_pattern", {})
                team = event.get("team", {})
                type = event["type"]["name"]
                related = event.get('related_events', [])
                base_time = {1: 0, 2: 45*60, 3: 90*60, 4: 105*60}
                ts_abs = base_time.get(event.get("period"), 0) + (event.get("minute") or 0) * 60 + (event.get("second" or 0))
                
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
                        cursor.execute("""
                        INSERT OR IGNORE INTO related_events (event_id, related_event_id)
                        VALUES (?, ?)
                        """, (event_id, rel))
                
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
                    shot_assist = event.get("pass", {}).get("shot_assist", False)
                    length = event.get("pass", {}).get("length", None)
                    angle = event.get("pass", {}).get("angle", None)
                    switch = event.get("pass", {}).get("switch", False)
                    cursor.execute('''INSERT OR IGNORE INTO passes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ? ,?, ?, ?, ?)''', (
                        event_id,
                        event.get("pass",{}).get("recipient",{}).get("name"),
                        loc[0], loc[1],
                        end_loc[0], end_loc[1],
                        pass_type,
                        height,
                        cross,
                        body_part,
                        shot_assist,
                        length,
                        angle,
                        switch
                    ))    
                elif type == "Shot":
                    loc = event.get("location", [None, None])
                    end_loc = event.get("shot",{}).get("end_location",[None, None])
                    body_part = event.get("shot", {}).get("body_part", {}).get("name")
                    first_time = event.get("shot", {}).get("first_time", False)
                    technique = event.get("shot", {}).get("technique", {}).get("name")
                    outcome = event.get("shot", {}).get("outcome", {}).get("name")
                    cursor.execute('''INSERT OR IGNORE INTO shots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                        event_id,
                        event.get("shot",{}).get("outcome",{}).get("name") == "Goal",
                        event.get("shot",{}).get("outcome",{}).get("name"),
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
                        
    for archivo in glob.glob(os.path.join(JSON_PATH,"three-sixty","*.json")):
        try:                
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error en {archivo}:{e}")
            
            for entry in data:
                event_uuid = entry.get("event_uuid")
                visible_area = json.dumps(entry.get("visible_area"))
                    
                cursor.execute('''INSERT OR IGNORE INTO three_sixty (event_uuid, visible_area) VALUES (?, ?)''', (event_uuid, visible_area))
                    
                for frame in entry.get("freeze_frame", []):
                    cursor.execute('''INSERT OR IGNORE INTO freeze_frame (event_uuid, teammate, actor, keeper, location_x, location_y) 
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
    print("Datos importados correctamente.")


if __name__ == "__main__":
    crear_tablas()
    importar_json()
