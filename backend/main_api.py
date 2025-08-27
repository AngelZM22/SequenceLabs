from typing import List, Optional, Union, Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import Counter
from motorbusqueda import motor_busqueda_avanzado
import os

# Ajusta esta ruta a tu BBDD
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "futbol.db")


app = FastAPI(title="TFG Fútbol API")

# CORS: permite peticiones desde Vite (puerto 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EventFilter(BaseModel):
    event: Union[str, List[str]]
    play_pattern: Optional[Union[str, List[str]]] = None
    start_x: Optional[float] = None
    start_y: Optional[float] = None
    tolerance: Optional[int] = None
    zone: Optional[Dict[str, float]] = None
    optional: Optional[bool] = None

class SearchRequest(BaseModel):
    pattern: List[EventFilter]
    match_id: Optional[int] = None
    team_id: Optional[int] = None
    play_pattern: Optional[str] = None
    competition: Optional[str] = None
    tolerancia: Optional[int] = 10
    margen_tiempo: Optional[int] = 30

def construir_ranking(secuencias: list[list[dict]]) -> dict[str, list[dict]] :
    tiradores = Counter()
    asistentes = Counter()
    pasadores_previos = Counter()
    recuperadores = Counter()
    regateadores = Counter()
    porteros = Counter()
    
    for jugada in secuencias:
        for ev in jugada:
            tipo = ev.get("type_name")
            jugador = ev.get("player_name")
            
            if tipo == "Shot":
                tiradores[jugador] += 1
            
            elif tipo == "Pass":
                if ev.get("shot_assist"):
                    asistentes[jugador] += 1
                else:
                    pasadores_previos[jugador] += 1
                    
            elif tipo in ("Dribble"):
                regateadores[jugador] += 1
                
            elif tipo in ("Ball Recovery", "Interception"):
                recuperadores[jugador] += 1

            elif tipo == "Goal Keeper":
                porteros[jugador] += 1
                
    def top10(counter):
        return [{"player": p, "count": c} for p, c in counter.most_common(10)]
    
    ranking = {}
    
    if tiradores:
        ranking["tiradores"] = top10(tiradores)
    if asistentes:
        ranking["asistentes"] = top10(asistentes)
    if pasadores_previos:
        ranking["pasadores_previos"] = top10(pasadores_previos)
    if recuperadores:
        ranking["recuperadores"] = top10(recuperadores)
    if regateadores:
        ranking["regateadores"] = top10(regateadores)
    if  porteros:
        ranking["porteros"] = top10(porteros)
        
    return ranking
            
    
        
@app.get("/status")
def status():
    return {"ok": True}

@app.post("/buscar")
def buscar(req: SearchRequest) -> Any:
    try:
        secuencia = [e.model_dump(exclude_none=True) for e in req.pattern]
        resultados = motor_busqueda_avanzado(
            db_path=DB_PATH,
            secuencia=secuencia,
            match_id=req.match_id,
            team_id=req.team_id,                     
            play_pattern=req.play_pattern,
            competition=req.competition,
            tolerancia=req.tolerancia,
            margen_tiempo=req.margen_tiempo,
        )

        # Limitar para evitar sobrecarga
        return {
            "total": len(resultados),
            "ejemplos": resultados[:3],  # solo una jugada, ejemplo
            "ranking": construir_ranking(resultados)
        }

    except Exception as e:
        import traceback
        print("ERROR EN BUSCAR:", traceback.format_exc())
        return {"error": str(e)}
