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
    related_event TEXT,
    period INTEGER,
    timestamp TEXT,
    minute INTEGER,
    second INTEGER,
    type_id INTEGER,
    type_name TEXT,
    possession INTEGER,
    possession_team_id INTEGER,
    possession_team_name TEXT,
    play_pattern_id INTEGER,
    play_pattern_name TEXT,
    team_id INTEGER,
    team_name TEXT,
    player_name TEXT,
    jersey_number INTEGER,
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT,
        player_id INTEGER,
        player_name TEXT,
        position_id INTEGER,
        position_name TEXT,
        jersey_number INTEGER,
        FOREIGN KEY (event_id) REFERENCES events(event_id)
    )''')
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_name ON events(player_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_id ON events(match_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_type_name ON events(type_name)")

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
                
                cursor.execute('''INSERT INTO events (
                    event_id, match_id,
                    related_event,
                    period, timestamp,
                    minute, second,
                    type_id, type_name,
                    possession, possession_team_id, possession_team_name,
                    play_pattern_id, play_pattern_name,
                    team_id, team_name,
                    player_name, jersey_number,
                    duration
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                    event_id,
                    match_id,
                    event.get("related_event",{}).get("id"),
                    event.get("period"),
                    event.get("timestamp"),
                    event.get("minute"),
                    event.get("second"),
                    event.get("type", {}).get("id"),
                    event.get("type", {}).get("name"),
                    event.get("possession"),
                    possession_team.get("id"),
                    possession_team.get("name"),
                    play_pattern.get("id"),
                    play_pattern.get("name"),
                    team.get("id"),
                    team.get("name"),
                    player.get("name"),
                    player.get("jersey_number"),
                    event.get("duration")
                    ))
                
                if event.get("tactics") and event["tactics"].get("lineup"):
                    for player in event["tactics"]["lineup"]:
                        cursor.execute('''INSERT INTO lineup (event_id, player_id, player_name, position_id, position_name, jersey_number) VALUES (?, ?, ?, ?, ?, ?)''', (
                            event_id,
                            player["player"].get("id"),
                            player["player"].get("name"),
                            player["position"].get("id"),
                            player["position"].get("name"),
                            player.get("jersey_number")
                        ))
                        
                type = event["type"]["name"]
            
                if type == "Pass":
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
                    end_loc = event.get("dribble",{}).get("end_location",[None, None])
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
                        foul.get("Advantage",False),
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

    conn.commit()
    conn.close()
    print("Datos importados correctamente.")

if __name__ == "__main__":
    crear_tablas()
    importar_json()
