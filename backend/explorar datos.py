import sqlite3
import json
import os
import glob
import pandas as pd
from motorbusqueda import motor_busqueda_avanzado
from uuid import uuid4

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(PROJECT_ROOT, "data","futbol.db")


def conectar():
    return sqlite3.connect(DATA_PATH, check_same_thread=False)

def prueba():
    conn = sqlite3.connect("c:/Users/angel/Desktop/VS-workspace/Trabajo-fin-de-grado/data/futbol.db")
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT type_name FROM events ORDER BY type_name")
    print(cur.fetchall())
    
    # Ver 10 pases con sus coords
    cur.execute("""
    SELECT e.type_name, p.start_x, p.start_y, p.end_x, p.end_y 
    FROM passes p
    JOIN events e ON e.event_id = p.event_id
    LIMIT 10
    """)
    print(cur.fetchall())

    # Ver 10 tiros con coords
    cur.execute("""
    SELECT e.type_name, s.start_x, s.start_y, s.end_x, s.end_y 
    FROM shots s
    JOIN events e ON e.event_id = s.event_id
    LIMIT 10
    """)
    print(cur.fetchall())
    
    cur.execute("SELECT DISTINCT play_pattern_name FROM events WHERE play_pattern_name IS NOT NULL")
    print(cur.fetchall())
    
    pattern = [
    {"event": "Pass"},
    {"event": "Shot"}
    ]

    res = motor_busqueda_avanzado("c:/Users/angel/Desktop/VS-workspace/Trabajo-fin-de-grado/data/futbol.db", pattern, margen_tiempo=300)
    print(len(res))

def bandaderecharegatecentrocabezazogol():
    
    
    conn = conectar()
    cursor = conn.cursor()
    query = """
          WITH eventos_consecutivos AS (
    SELECT
        e1.event_id AS dribble_id,
        e2.event_id AS pass_id,
        e3.event_id AS shot_id,
        e1.player_name AS regateador,
        e2.player_name AS pasador,
        e3.player_name AS rematador,
        s.goal
    FROM events e1
    JOIN dribbles d ON d.event_id = e1.event_id
    JOIN events e2 ON e2.match_id = e1.match_id
                   AND e2.possession = e1.possession
                   AND (strftime('%s', '1970-01-01T' || e2.timestamp)) > (strftime('%s', '1970-01-01T' || e1.timestamp))
                   AND (strftime('%s', '1970-01-01T' || e2.timestamp)) <= (strftime('%s', '1970-01-01T' || e1.timestamp)) + 30 -- 30 segundos margen
    JOIN passes p ON p.event_id = e2.event_id
                  AND (p.cross = 1 OR p.height = 'High Pass')
    JOIN events e3 ON e3.match_id = e2.match_id
                   AND e3.possession = e2.possession
                   AND (strftime('%s', '1970-01-01T' || e3.timestamp)) > (strftime('%s', '1970-01-01T' || e2.timestamp))
                   AND (strftime('%s', '1970-01-01T' || e3.timestamp)) <= (strftime('%s', '1970-01-01T' || e2.timestamp)) + 10
    JOIN shots s ON s.event_id = e3.event_id
    WHERE d.outcome = 'Complete'
      AND d.start_x > 66
      AND d.start_y BETWEEN 0 AND 20
      AND s.body_part = 'Head'
)
SELECT * FROM eventos_consecutivos
LIMIT 20;






            """
    df = pd.read_sql(query, conn)
    print(df)
    conn.close()
    return df

def detectar_secuencias_flexibles(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
    SELECT 
        e.event_id,
        e.match_id,
        e.possession,
        e.timestamp,
        e.type_name,
        e.player_name
    FROM events e
    ORDER BY e.match_id, e.possession, e.timestamp
    """

    df = pd.read_sql(query, conn)

    secuencias = []

    # Recorremos todos los eventos
    for i, row in df.iterrows():
        if row['type_name'] == 'Dribble':
            start_time = row['timestamp']
            match_id = row['match_id']
            possession = row['possession']
            regateador = row['player_name']

            for j in range(i+1, min(i+7, len(df))):  # buscar en los 6 eventos siguientes máximo
                next_event = df.iloc[j]

                if next_event['match_id'] != match_id or next_event['possession'] != possession:
                    break  # se cambia de jugada

                if next_event['type_name'] == 'Pass':
                    pasador = next_event['player_name']

                    for k in range(j+1, min(j+7, len(df))):  # buscar shot después
                        next_shot = df.iloc[k]

                        if next_shot['match_id'] != match_id or next_shot['possession'] != possession:
                            break

                        if next_shot['type_name'] == 'Shot':
                            rematador = next_shot['player_name']

                            secuencias.append({
                                'regateador': regateador,
                                'pasador': pasador,
                                'rematador': rematador
                            })
                            break
                    break

    conn.close()
    return pd.DataFrame(secuencias)



if __name__ == "__main__":
    
    #conectar()
    #df_secuencias = detectar_secuencias_flexibles(DATA_PATH)
    #print(df_secuencias)
    prueba()