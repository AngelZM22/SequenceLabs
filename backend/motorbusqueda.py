import sqlite3

def dentro_de_zona(x, y, objetivo, tolerancia=10):
    return abs(x - objetivo["start_x"]) <= tolerancia and abs(y - objetivo["start_y"]) <= tolerancia

def motor_busqueda(db_path='futbol.db', sequence, match_id=None, tolerancia=10, margen_tiempo=30):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if match_id:
        cursor.execute("""
            SELECT id, match_id, event_type, x, y, timestamp 
            FROM events WHERE match_id = ? ORDER BY timestamp
        """, (match_id,))
    else:
        cursor.execute("SELECT id, match_id, event_type, x, y, timestamp FROM events ORDER BY timestamp")
    
    eventos = cursor.fetchall()
    
    
    resultados = []
    indice= 0
    actual = []
    
    for e in eventos:
        objetivo = sequence[indice]
        if e["type_name"] == objetivo["event"] and dentro_de_zona(e["x_start"], e["y_start"], objetivo, tolerancia):
            if i == 0:
                comienza_accion = e["timestamp"]
            else:
                if (e["timestamp"] - objetivo["timestamp"]) > margen_tiempo:
                    i = 0
                    actual = []
                    continue
            
            actual.append(dict(e))
            i += 1
                
            if i == len(sequence):
                resultados.append(actual.copy())
                i = 0
                actual = []
            else:
                i = 0
                actual = []
    
    conn.close()
    return resultados
    
