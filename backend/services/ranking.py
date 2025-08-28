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