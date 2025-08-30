import unicodedata
import re

SUCCESS_OUTCOMES = {"won", "success", "successful", "complete"}  # amplía si lo necesitas

def _norm(s: str) -> str:
    if not s:
        return ""
    s = s.strip().lower()
    # quita acentos
    s = "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )
    # colapsa espacios múltiples
    s = re.sub(r"\s+", " ", s)
    return s

def norm_equals(a: str, b: str) -> bool:
    return _norm(a) == _norm(b)

def norm_in(s1: str, s2: str) -> bool:
    return _norm(s1) in _norm(s2)


def _outcome_of(ev) -> str:
    t = _norm(ev.get("type_name"))
    if t == "shot":
        return _norm(ev.get("shot_outcome_name") or ev.get("shot_outcome"))
    if t == "pass":
        return _norm(ev.get("pass_outcome_name"))
    if t == "dribble":
        return _norm(ev.get("dribble_outcome_name"))
    if t == "duel":
        return _norm(ev.get("duel_outcome_name"))
    if t == "interception":
        return _norm(ev.get("interception_outcome_name"))
    return _norm(ev.get("outcome_name") or "")

def matches_outcome(ev, desired: str) -> bool:
    des = _norm(desired)
    t = _norm(ev.get("type_name"))
    if t == "shot" and des in {"goal", "gol"}:
        return is_goal(ev)
    return _outcome_of(ev) == des

def is_shot(ev):
    return _norm(ev.get("type_name")) == "shot"


def is_goal(ev) -> bool:
    # 1) preferimos el booleano
    if "shot_goal" in ev and ev["shot_goal"] is not None:
        return bool(ev["shot_goal"])
    # 2) fallback si por lo que sea no viene (compat)
    out = _norm(ev.get("shot_outcome_name") or ev.get("shot_outcome"))
    return out == "goal"

def is_success(ev) -> bool:
    t = _norm(ev.get("type_name"))
    if t == "shot":
        # Para tiros, consideramos "éxito" == gol (ajústalo si quieres otra semántica)
        return is_goal(ev)
    return _outcome_of(ev) in SUCCESS_OUTCOMES

def is_duel_won(evento) -> bool:
    return (evento.get("type_name") == "Duel") and is_success(evento)

def is_interception_success(evento) -> bool:
    return (evento.get("type_name") == "Interception") and is_success(evento)

def possession_change(evento) -> bool:
    # Si ya calculas esto, llama a tu flag; si no lo tienes, aproxima:
    # cambio si team_id del siguiente evento es distinto y el actual fue defensivo/ganado.
    return bool(evento.get("possession_change") == True)

def is_recovery(evento) -> bool:
    # Intercepción exitosa o duelo/tackle ganado con cambio de posesión
    if is_interception_success(evento):
        return True
    if is_duel_won(evento) and possession_change(evento):
        return True
    # Puedes añadir "Ball Recovery" si existe en tus datos como evento específico:
    if (evento.get("type_name") == "Ball Recovery") and is_success(evento):
        return True
    return False

