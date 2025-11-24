# Pruebas funcionales de frontend

Precondiciones comunes:
- API levantada en `http://localhost:8000`.
- Cliente React levantado en `http://localhost:5173`.
- Base de datos con datos de StatsBomb Open Data correctamente cargados.

---

## PF-10 – Carga inicial de filtros (competiciones, temporadas, equipos)

**Objetivo**  
Verificar que, al arrancar la aplicación, los desplegables de filtros se cargan y sólo
muestran combinaciones válidas.

**Pasos**

1. Abrir `http://localhost:5173` en el navegador.
2. Esperar a que se cargue la página principal.
3. Abrir los desplegables de competición, temporada y equipo.
4. Comprobar que:
   - aparecen competiciones y temporadas reales,
   - al seleccionar una competición, las temporadas disponibles son las correctas,
   - al seleccionar una temporada, los equipos disponibles tienen sentido.

**Resultado esperado**

- Los desplegables muestran sólo opciones válidas.
- No se ven opciones vacías o combinaciones imposibles.

**Resultado**  
- [ ] OK  (fecha: ____ / notas: ____)

---

## PF-11 – Filtrado en cascada (competición, temporada, equipo, jugador)

**Objetivo**  
Comprobar que los filtros se actualizan en cascada y que los jugadores corresponden
al equipo/temporada seleccionados.   

**Pasos**

1. Seleccionar una competición en el filtro correspondiente.
2. Seleccionar una temporada.
3. Seleccionar un equipo.
4. Abrir el desplegable de jugadores y comprobar que sólo aparecen jugadores de ese
   equipo y temporada.
5. Cambiar la competición o la temporada y verificar que:
   - se actualizan los equipos disponibles,
   - se ajusta automáticamente la lista de jugadores (no quedan jugadores de equipos
     o temporadas anteriores).

**Resultado esperado**

- Al cambiar un filtro de nivel superior se reajustan los dependientes.
- La lista de jugadores siempre corresponde al equipo y temporada actuales.

**Resultado**  
- [ ] OK  (fecha: ____ / notas: ____)

---

## PF-12 – Construcción de un patrón sencillo (pase + tiro) sobre el campo

**Objetivo**  
Verificar que el diseñador de jugadas sobre el campo refleja las elecciones del usuario
y construye un patrón válido para el backend.   

**Pasos**

1. En la página principal, ir al diseñador de jugadas (campo).
2. Añadir un primer evento de tipo `pass` (pase) en una zona del campo.
3. Añadir un segundo evento de tipo `shot` (disparo) en otra zona.
4. Si aplica, seleccionar un jugador implicado en alguno de los pasos.
5. Comprobar que la representación gráfica en el campo refleja:
   - el tipo de evento,
   - la dirección,
   - la zona seleccionada,
   - y, si procede, el jugador.
6. Revisar en el panel lateral (o en la estructura del patrón, si se muestra) que el
   patrón queda almacenado con esos pasos.

**Resultado esperado**

- El patrón se representa gráficamente mostrando las elecciones del usuario.
- El patrón queda listo para ser enviado al backend.

**Resultado**  
- [ ] OK  (fecha: ____ / notas: ____)

---

## PF-13 – Edición y eliminación de pasos del patrón

**Objetivo**  
Comprobar que las modificaciones sobre el patrón se reflejan tanto en el estado
interno como en la representación gráfica.   

**Pasos**

1. Construir un patrón con varios pasos (por ejemplo, 3–4 eventos).
2. Editar uno de los pasos (cambiar zona, tipo de evento, jugador, etc.).
3. Comprobar que:
   - el patrón se actualiza en la lista de pasos,
   - la representación en el campo cambia de acuerdo a la nueva configuración.
4. Eliminar uno de los pasos del patrón.
5. Verificar que desaparece de la lista de pasos y de la representación gráfica.

**Resultado esperado**

- Al modificar o borrar un paso, el estado interno del patrón y su representación
  se actualizan correctamente.

**Resultado**  
- [ ] OK  (fecha: ____ / notas: ____)

---

## PF-14 – Ejecución de búsqueda desde la interfaz con un patrón definido

**Objetivo**  
Comprobar el flujo completo: patrón → envío al backend → presentación de resultados.   

**Pasos**

1. Construir un patrón sobre el campo (por ejemplo, pase → tiro) y configurar filtros
   (competición, temporada y equipo).
2. Pulsar el botón para ejecutar la búsqueda.
3. Verificar que:
   - la interfaz muestra un estado de “cargando” mientras se hace la petición,
   - se presentan las jugadas devueltas, el resumen del patrón y el ranking de jugadores.
4. Lanzar una segunda búsqueda distinta sin recargar la página (por ejemplo, cambiando
   zonas o tipo de eventos) y comprobar que los resultados se actualizan correctamente.

**Resultado esperado**

- La consulta se envía al backend y la respuesta se muestra sin errores.
- Los resultados son coherentes con el patrón definido.
- Es posible lanzar varias búsquedas consecutivas sin recargar la página.

**Resultado**  
- [ ] OK  (fecha: ____ / notas: ____)

---

## PF-15 – Exploración de player insights desde el ranking de jugadores

**Objetivo**  
Verificar que el panel de *player insights* se abre correctamente y muestra información
consistente con la búsqueda original.   

**Pasos**

1. Ejecutar una búsqueda que genere un ranking de jugadores para algún rol.
2. En el ranking, seleccionar un jugador (por ejemplo, haciendo clic sobre su fila).
3. Comprobar que se abre el panel lateral de *player insights* para ese jugador.
4. Revisar que:
   - las estadísticas se refieren al contexto del patrón actual (no a otro),
   - las jugadas de ejemplo corresponden a ese jugador y a las jugadas devueltas
     en la búsqueda original.
5. Cerrar el panel de *player insights* y comprobar que se vuelve sin problemas
   a la vista principal de resultados.

**Resultado esperado**

- Se muestran estadísticas y ejemplos relacionados con el jugador y rol seleccionado.
- El usuario puede volver a la vista de resultados principal sin reejecutar la búsqueda.

**Resultado**  
- [ ] OK  (fecha: ____ / notas: ____)
