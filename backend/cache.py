from uuid import uuid4
from collections import OrderedDict
from typing import Any, Dict, List, Optional

# Cache simple en memoria: query_id -> resultados (lista de jugadas)
CACHE: "OrderedDict[str, List[List[dict]]]" = OrderedDict()

# Para no comernos la RAM en sesiones largas: máximo 20 búsquedas guardadas
MAX_CACHE = 20
def _cache_put(query_id: str, resultados: List[List[dict]]) -> None:
    # si excede, borra el más antiguo (orden de inserción en dict de Py3.7+)
    if len(CACHE) >= MAX_CACHE:
        CACHE.popitem(last=False)
    CACHE[query_id] = resultados
    
def _cache_get(query_id: str):
    return CACHE.get(query_id)