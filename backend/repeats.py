# repeats.py
from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional, Callable

NormMap = Dict[int, Dict[str, Any]]  # match_id -> info del partido

def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()

def _etype(ev: Dict[str, Any]) -> str:
    """Tipo normalizado (pass, shot, dribble, ...)."""
    return _norm(ev.get("type_name") or ev.get("type") or "")

def _label_event(ev: Dict[str, Any]) -> str:
    """
    Etiqueta corta y legible de un evento para el encabezado del patrón.
    Nota: para 'shot' NO ponemos el outcome aquí (se usa sólo en ocurrencias).
    """
    t = _etype(ev)
    name = ev.get("player_name") or "?"
    if t == "pass":
        rec = ev.get("pass_receiver_name") or ev.get("pass_recipient_name") or "?"
        return f"Pass({name}→{rec})"
    if t == "shot":
        return f"Shot({name})"  # sin outcome
    if t == "dribble":
        return f"Dribble({name})"
    if t == "duel":
        return f"Duel({name})"
    if t == "ball receipt":
        return f"Ball Receipt({name})"
    if t in ("goalkeeper", "goal keeper"):
        return f"Goalkeeper({name})"
    if t == "interception":
        return f"Interception({name})"
    return f"{ev.get('type_name') or 'Event'}({name})"

def _sig_event_aggregate(ev: Dict[str, Any]) -> Tuple:
    """
    Firma por evento para AGRUPAR: tiro sin outcome (así sumamos todos los tiros).
    Añadimos receptor en los pases si viene disponible.
    """
    t = _etype(ev)
    pid = ev.get("player_id") or 0
    if t == "pass":
        rec = (ev.get("pass_receiver_name") or ev.get("pass_recipient_name") or "")
        return ("pass", pid, _norm(rec))
    if t == "shot":
        return ("shot", pid)  # <- outcome fuera de la firma (clave del agregado)
    return (t, pid)

# Conjuntos útiles para métricas (StatsBomb outcome names más comunes)
_ON_TARGET = {"goal", "saved", "saved to safety"}
_GOAL = {"goal"}

def _occurrence_label(mm: Dict[str, Any] | None, minute: Optional[int]) -> Optional[str]:
    """'Local vs Visitante · Temporada — min X' si hay datos."""
    if not mm:
        return None
    home = mm.get("home_team") or mm.get("home_team_name") or "?"
    away = mm.get("away_team") or mm.get("away_team_name") or "?"
    sname = mm.get("season_name")
    label = f"{home} vs {away}"
    if sname:
        label += f" · {sname}"
    if isinstance(minute, int):
        label += f" — min {minute}"
    return label

def group_repeats_aggregated(
    resultados: List[List[Dict[str, Any]]],
    match_info_map: NormMap,
    build_youtube_query: Callable[[List[Dict[str, Any]], NormMap], Optional[str]],
    max_groups: int = 25,
    max_occurrences: int = 15,
) -> List[Dict[str, Any]]:
    """
    Agrupa *cualquier* secuencia por firma agregada (tiro sin outcome),
    calcula métricas de tiros y devuelve top grupos con ocurrencias.

    Devuelve lista de grupos:
      - key: id estable
      - label: 'Pass(Messi→Suárez) > Shot(Suárez)'
      - tokens: ['Pass(Messi→Suárez)', 'Shot(Suárez)']
      - count: nº de repeticiones
      - stats: {shots, on_target, goals, pct_on_target, pct_goals}
      - occurrences: [{match_id, minute, label, shot_outcome, preview, youtube_search}]
    """
    grupos: Dict[Tuple, Dict[str, Any]] = {}

    for seq in resultados:
        firma = tuple(_sig_event_aggregate(e) for e in seq)
        tokens = [_label_event(e) for e in seq]

        g = grupos.get(firma)
        if not g:
            g = {
                "key": str(hash(firma)),
                "label": " > ".join(tokens),
                "tokens": tokens,
                "count": 0,
                "stats": {"shots": 0, "on_target": 0, "goals": 0},
                "occurrences": [],
            }
            grupos[firma] = g

        g["count"] += 1

        # localizar el tiro de la secuencia (si existe)
        shot = next((e for e in seq if _etype(e) == "shot"), None)
        shot_out_norm = _norm(shot.get("shot_outcome_name")) if shot else ""
        if shot:
            g["stats"]["shots"] += 1
            if shot_out_norm in _ON_TARGET:
                g["stats"]["on_target"] += 1
            if shot_out_norm in _GOAL:
                g["stats"]["goals"] += 1

        # datos para la ocurrencia
        match_id = next((e.get("match_id") for e in seq if e.get("match_id") is not None), None)
        minute   = next((e.get("minute")   for e in seq if isinstance(e.get("minute"), int)), None)
        event_ids = ";".join([str(e.get("event_id")) for e in seq if e.get("event_id")])

        mm = match_info_map.get(match_id or -1) or {}
        occ = {
            "match_id": match_id,
            "minute": minute,
            "label": _occurrence_label(mm, minute),
            "shot_outcome": shot.get("shot_outcome_name") if shot else None,
            "preview": (f"/render/play?match_id={match_id}&event_ids={event_ids}"
                        if match_id and event_ids else None),
            "youtube_search": build_youtube_query(seq, match_info_map),
        }
        g["occurrences"].append(occ)

    # ordenar y limitar
    repeats = list(grupos.values())
    for g in repeats:
        s = g["stats"]
        shots = max(s["shots"], 1)  # evitar división por cero
        s["pct_on_target"] = round(s["on_target"] / shots * 100, 2)
        s["pct_goals"]     = round(s["goals"]     / shots * 100, 2)
        if len(g["occurrences"]) > max_occurrences:
            g["occurrences"] = g["occurrences"][:max_occurrences]

    repeats.sort(key=lambda x: (-x["count"], x["label"]))
    return repeats[:max_groups]
