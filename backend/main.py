import sqlite3
import json
import os
import glob
from uuid import uuid4

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(PROJECT_ROOT, "data","futbol.db")


def conectar():
    return sqlite3.connect(DATA_PATH, check_same_thread=False)

def prueba():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print(cursor.fetchall())
    cursor.execute("SELECT COUNT(*) FROM events")
    print(cursor.fetchall())
    cursor.execute("SELECT COUNT(*) FROM matches")
    print(cursor.fetchall())
    cursor.execute("SELECT COUNT(*) FROM freeze_frame")
    print(cursor.fetchall())
    
if __name__ == "__main__":
    conectar()
    prueba()
