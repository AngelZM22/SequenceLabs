-- SQLite
-- ✅ Crear índices para acelerar búsquedas por partido, evento y timestamp
CREATE INDEX IF NOT EXISTS idx_events_match_possession_time ON events(match_id, possession, timestamp);
CREATE INDEX IF NOT EXISTS idx_dribbles_event_id ON dribbles(event_id);
CREATE INDEX IF NOT EXISTS idx_passes_event_id ON passes(event_id);
CREATE INDEX IF NOT EXISTS idx_shots_event_id ON shots(event_id);

-- ✅ Probar búsqueda de secuencias reales (regate en banda ➜ centro ➜ remate de cabeza sin gol)
WITH jugadas AS (
    SELECT
        e1.player_name AS regateador,
        e2.player_name AS pasador,
        e3.player_name AS rematador,
        s.goal
    FROM events e1
    JOIN dribbles d ON d.event_id = e1.event_id
    JOIN events e2 ON e2.match_id = e1.match_id
                   AND e2.possession = e1.possession
                   AND strftime('%s', '1970-01-01T' || e2.timestamp) BETWEEN strftime('%s', '1970-01-01T' || e1.timestamp) AND strftime('%s', '1970-01-01T' || e1.timestamp) + 30
    JOIN passes p ON p.event_id = e2.event_id
                 AND (p.cross = 1 OR p.height = 'High Pass')
    JOIN events e3 ON e3.match_id = e2.match_id
                   AND e3.possession = e2.possession
                   AND strftime('%s', '1970-01-01T' || e3.timestamp) BETWEEN strftime('%s', '1970-01-01T' || e2.timestamp) AND strftime('%s', '1970-01-01T' || e2.timestamp) + 10
    JOIN shots s ON s.event_id = e3.event_id
    WHERE d.outcome = 'Complete'
      AND d.start_x > 66
      AND d.start_y BETWEEN 0 AND 20
      AND s.body_part = 'Head'
      AND s.goal = 0
)
SELECT * FROM jugadas
LIMIT 20;


