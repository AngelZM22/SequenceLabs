# Pruebas funcionales de backend (sección 5.1)

Precondiciones comunes a todas las pruebas:
- Base de datos generada con `python database.py`.
- API levantada en `http://localhost:8000` con `uvicorn main_api:app --reload --port 8000`.
- Datos de StatsBomb Open Data correctamente importados.

---

## PF-01 – Patrón simple de un único evento (tiro)

**Objetivo**  
Comprobar que el endpoint de búsqueda devuelve jugadas con un único evento de tipo `shot`
y que el número de jugadas coincide con el número de tiros registrados.

**Pasos**

1. Hacer una petición `POST /search` (por Postman, curl o desde la propia interfaz)
   con un patrón formado solo por un evento de tipo `shot` y sin filtros de
   competición/equipo/jugador.
2. Extraer del resultado el número de jugadas devueltas.
3. Ejecutar en SQLite: `SELECT COUNT(*) FROM shots;` para obtener el número de tiros
   en el conjunto de datos.
4. Revisar una muestra de jugadas y comprobar que cada una sólo contiene un evento
   de tipo tiro.

**Resultado esperado**

- Todas las jugadas devueltas tienen un único evento de tipo tiro.
- El número de jugadas coincide con `COUNT(*) FROM shots`.

**Resultado**  
- [X] OK  (fecha: 25/11/2025)
- Verificación: UI + consulta SQL de `events`/`shots`
- Evidencias: captura en `tests/img/pf-01.pdf`, `tests/img/pf-01dbeaver.png`

---

## PF-02 – Patrón de pase seguido de tiro (competiciones/temporadas acotadas)

**Objetivo**  
Verificar que la búsqueda respeta el orden pase → tiro, que ambos eventos pertenecen
al mismo equipo y que los partidos están dentro de la competición y temporada indicadas.

**Pasos**

1. Elegir una competición y temporada concretas (por ejemplo, usando los endpoints de
   opciones o los filtros en la interfaz).
2. Lanzar una búsqueda con un patrón de dos pasos:
   - evento 1: `pass`
   - evento 2: `shot`
   y filtrando por la competición y temporada elegidas.
3. En los resultados, tomar varias jugadas de muestra y comprobar:
   - que siempre aparece un pase seguido de un tiro,
   - que ambos eventos pertenecen al mismo equipo,
   - que el `match_id` de las jugadas corresponde a partidos de esa competición y
     temporada (puede verificarse cruzando con la tabla `matches`).

**Resultado esperado**

- Todas las jugadas respetan el orden pase → tiro del mismo equipo.
- Todos los partidos devueltos pertenecen a la competición y temporada filtradas.

**Resultado**  
- [X] OK  (fecha: 25/11/2025)
- Evidencias: captura en `tests/img/pf-02.pdf`, donde se respetan los filtros (solo se muestra Bundesliga)

---

## PF-03 – Patrón con restricciones espaciales (zonas del campo)

**Objetivo**  
Comprobar que el motor respeta las zonas del campo definidas en el patrón.

**Pasos**

1. Definir un patrón con dos eventos (por ejemplo, pase → tiro) donde:
   - el primer evento empiece en una zona concreta del campo,
   - el segundo evento tenga lugar en otra zona específica.
   (Se puede hacer desde la interfaz usando las zonas del diseñador de jugadas).
2. Ejecutar la búsqueda.
3. Para varias jugadas de muestra, comparar las coordenadas de inicio/fin de los eventos
   con las zonas configuradas (usando la BD o lo que muestra la interfaz).

**Resultado esperado**

- Las coordenadas de los eventos se encuentran dentro de los rangos asociados
  a las zonas definidas en el patrón.
- No aparecen jugadas que incumplan las condiciones espaciales.

**Resultado**  
- [X] OK  (fecha: 25/11/2025)
- Evidencias: captura en `tests/img/pf-03.pdf`, se chequea por video a través de esta URL: https://www.youtube.com/watch?v=PzdJ-IOlKsE

---

## PF-04 – Patrón filtrado por jugador

**Objetivo**  
Verificar que el filtrado por jugador funciona y respeta el rol definido.

**Pasos**

1. Seleccionar un jugador concreto (por ejemplo, desde los filtros de la interfaz).
2. Definir un patrón donde ese jugador participe en uno de los eventos (por ejemplo,
   como pasador o rematador).
3. Ejecutar la búsqueda.
4. Para varias jugadas de ejemplo, comprobar que:
   - el jugador aparece en el evento y rol indicado,
   - no se incluyen acciones de otros jugadores en ese rol.

**Resultado esperado**

- En todas las jugadas devueltas aparece el jugador seleccionado en el rol indicado.
- No se incluyen acciones de otros jugadores en esa posición.

**Resultado**  
- [X] OK  (fecha: 25/11/2025)
- Evidencias: captura en `tests/img/pf-04.pdf`, donde solo se incluyen acciones de un jugador para ese rol (el filtrado)

---

## PF-05 – Patrón sin resultados (patrón muy restrictivo)

**Objetivo**  
Comprobar que la API gestiona correctamente patrones que no devuelven jugadas.

**Pasos**

1. Definir un patrón intencionadamente raro (por ejemplo, combinación de eventos poco
   frecuente en una zona muy concreta del campo, con filtros de jugador/equipo).
2. Ejecutar la búsqueda.
3. Observar que la API responde sin errores.

**Resultado esperado**

- La API responde con éxito (HTTP 200).
- El cuerpo de respuesta indica 0 jugadas.
- No se producen errores ni trazas inesperadas en el backend.

**Resultado**  
- [X] OK  (fecha: 25/11/2025)
- Evidencias: captura en `tests/img/pf-05.pdf`, no devuelve resultados y no se corrompe


---

## PF-06 – Cálculo del resumen global de una consulta

**Objetivo**  
Validar que el resumen global (estadísticas agregadas) coincide con los datos devueltos.

**Pasos**

1. Ejecutar una búsqueda con un patrón sencillo (por ejemplo, pase → tiro).
2. Anotar el número de jugadas devueltas.
3. Revisar el resumen global (goles, tiros, etc.) que devuelve la API o muestra la UI.
4. Tomar una muestra de jugadas y recalcular manualmente algunas métricas
   (por ejemplo, cuántos goles hay en esa muestra) para comprobar consistencia.

**Resultado esperado**

- El número de jugadas del resumen coincide con las jugadas devueltas.
- Las estadísticas agregadas son coherentes y se pueden reproducir a partir de
  una muestra revisada manualmente.

**Resultado**  
- [X] OK  (fecha: 25/11/2025)
- Evidencias: captura en `tests/img/pf-06.pdf`, se filtra por un equipo, partido y un solo evento y devuelve resultados consistentes.


---

## PF-07 – Cálculo del ranking de jugadores

**Objetivo**  
Comprobar que el ranking ordena correctamente a los jugadores según sus apariciones
en el patrón.

**Pasos**

1. Ejecutar una búsqueda que devuelva un volumen razonable de jugadas.
2. Consultar el ranking de jugadores por rol devuelto por el backend.
3. Escoger uno o varios jugadores del top del ranking.
4. Contar manualmente, sobre una muestra de jugadas, cuántas veces aparecen en ese patrón
   y verificar que el orden tiene sentido (más apariciones → mejor posición).

**Resultado esperado**

- El orden de los jugadores refleja coherentemente su número de apariciones.
- La comprobación manual sobre una muestra coincide con el ranking.

**Resultado**  
- [X] OK  (fecha: 25/11/2025)
- Evidencias: captura en `tests/img/pf-07.pdf`, se filtra por goleadores del barcelona en 2019/20 y cuadra con resultados oficiales, hay que tener en cuenta que no están todos los partidos del barcelona de esa liga.


---

## PF-08 – Player insights para un jugador y rol concreto

**Objetivo**  
Validar que las estadísticas específicas de un jugador y las jugadas de ejemplo son
coherentes con la búsqueda original.

**Pasos**

1. Ejecutar una búsqueda que genere un ranking de jugadores para un rol concreto.
2. Seleccionar un jugador desde el ranking (en el frontend) o llamar al endpoint
   correspondiente de player insights para ese jugador y rol.
3. Revisar las estadísticas que se muestran (goles, tiros, contribución al patrón, etc.).
4. Verificar que las jugadas de ejemplo mostradas pertenecen a la misma búsqueda
   y al jugador/rol seleccionado.

**Resultado esperado**

- Las estadísticas y jugadas de ejemplo corresponden al jugador y rol analizados
  dentro de esa búsqueda concreta.

**Resultado**  
- [X] OK  (fecha: 25/11/2025)
- Evidencias: captura en `tests/img/pf-08.png`, cuadra con resultados oficiales.

---

## PF-09 – Detección de repeticiones de patrones recurrentes

**Objetivo**  
Comprobar que el módulo de repeticiones agrupa adecuadamente patrones equivalentes.

**Pasos**

1. Ejecutar una búsqueda sobre un patrón que tenga muchas ocurrencias (por ejemplo,
   una combinación típica como pase → centro → remate).
2. Lanzar la funcionalidad de detección de repeticiones (endpoint o funcionalidad
   de UI que agrupa patrones similares).
3. Revisar varias agrupaciones devueltas:
   - comprobar que comparten estructura (mismo orden de eventos),
   - comprobar que representan jugadas equivalentes en momentos o partidos distintos.

**Resultado esperado**

- Las agrupaciones muestran patrones con estructura similar.
- Cada grupo representa jugadas equivalentes en distintos contextos.

**Resultado**  
- [X] OK  (fecha: 25/11/2025)
- Evidencias: captura en `tests/img/pf-09.pdf`, comprobamos el caso de Budimir con el Osasuna por vídeo
  a través de este link: https://www.youtube.com/watch?v=cKOSvTDluOk, y todo cuadra.
