from uuid import uuid4
from typing import Any, Dict, List, Optional

# Cache simple en memoria: query_id -> resultados (lista de jugadas)
CACHE: Dict[str, List[List[dict]]] = {}

# Para no comernos la RAM en sesiones largas: máximo 20 búsquedas guardadas
MAX_CACHE = 20
def _cache_put(query_id: str, resultados: List[List[dict]]):
    global CACHE
    # si excede, borra el más antiguo (orden de inserción en dict de Py3.7+)
    if len(CACHE) >= MAX_CACHE:
        oldest = next(iter(CACHE))
        CACHE.pop(oldest, None)
    CACHE[query_id] = resultados