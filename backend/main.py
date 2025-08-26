import sqlite3
import json
import os
import glob
import time
from uuid import uuid4
from datetime import datetime, timedelta
from math import sqrt
from motorbusqueda import motor_busqueda_avanzado

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(PROJECT_ROOT, "data","futbol.db")


# Ejemplos de patrones de búsqueda
pattern1 = [
    {"event": "Pass", "play_pattern": "From Corner"},
    {"event": "Shot"}
]



pattern2 = [
    {"event": "Carry", "start_x": 90, "start_y": 35, "tolerance": 32},
    {"event": "Pass", "start_x": 60, "start_y": 40, "tolerance": 20},
    {"event": "Shot", "start_x": 116, "start_y": 40, "tolerance": 25}
]

pattern3 = [
    {"event": "Ball Recovery"},
    {"event": "Pass", "start_x": 30, "tolerance": 20},  # pase desde campo propio
    {"event": "Shot", "start_x": 110, "tolerance": 15}  # tiro cerca de portería rival
    
]

pattern4 = [
    {"event": "Pass", "start_x": 60, "start_y": 40, "tolerance": 15},
    {"event": "Dribble"},  # el motor añadirá Carry después automáticamente
    {"event": "Shot"}
]


def conectar():
    return sqlite3.connect(DATA_PATH, check_same_thread=False)

def prueba():
    inicio = time.time()
    resultados = motor_busqueda_avanzado("c:/Users/angel/Desktop/VS-workspace/Trabajo-fin-de-grado/data/futbol.db", pattern2, competition="La Liga", margen_tiempo=120)
    fin= time.time()

    print(f"Encontradas {len(resultados)} jugadas")
    print(f"Tiempo de búsqueda: {fin - inicio:.2f} segundos")  
    print("Ejemplos:")
    print("--------------")
    print(resultados[0])
    print("--------------") 
    
    for i, jugada in enumerate(resultados[:3]):  # mostramos 3 jugadas de ejemplo
        print(f"\nJugada {i+1}:")
        for ev in jugada:
            print(f"  {ev['type_name']} en ({ev['start_x']}, {ev['start_y']}) - patrón {ev.get('play_pattern_name', 'N/A')}")
    
if __name__ == "__main__":
    conectar()
    prueba()
