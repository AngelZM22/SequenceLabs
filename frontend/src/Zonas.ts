export type ZRect = { x: number; y: number; w: number; h: number };

// carriles (5 franjas verticales)
/*
const LANES = ["left_wing", "left_halfspace", "center", "right_halfspace", "right_wing"] as const;
const Y = [0, 16, 32, 48, 64, 80];
const thirds = [
  { id: "def", x0: 0,  x1: 40 },
  { id: "mid", x0: 40, x1: 80 },
  { id: "att", x0: 80, x1: 120 },
] as const;

// lista de claves
export const EXTENDED_ZONE_KEYS = thirds.flatMap(t =>
  LANES.map(l => `${t.id}_${l}` as const)
);

export const CLASSIC_ZONE_KEYS = [
  "own_half",
  "opponent_half",
  "final_third",
  "box_left",
  "box_right",
  "six_left",
  "six_right",
] as const;

export const ZONE_KEYS = [...EXTENDED_ZONE_KEYS, ...CLASSIC_ZONE_KEYS] as readonly string[];

// mapa de rectángulos (coincide con backend)
export const ZONE_RECTS: Record<string, ZRect> = (() => {
  const out: Record<string, ZRect> = {};

  // tercios × carriles
  for (const t of thirds) {
    for (let i = 0; i < LANES.length; i++) {
      const key = `${t.id}_${LANES[i]}`;
      out[key] = { x: t.x0, y: Y[i], w: t.x1 - t.x0, h: Y[i + 1] - Y[i] };
    }
  }

  // clásicas
  out["own_half"]      = { x: 0,   y: 0,  w: 60, h: 80 };
  out["opponent_half"] = { x: 60,  y: 0,  w: 60, h: 80 };
  out["final_third"]   = { x: 80,  y: 0,  w: 40, h: 80 };

  // áreas
  out["box_left"]  = { x: 0,   y: 18, w: 18,  h: 44 };
  out["box_right"] = { x: 102, y: 18, w: 18,  h: 44 };
  out["six_left"]  = { x: 0,   y: 30, w: 6,   h: 20 };
  out["six_right"] = { x: 114, y: 30, w: 6,   h: 20 };

  out["corner_top_left"]        = { x: 0,       y:0 ,   w:2,    h:2}
  out["corner_bottom_left"]     = { x: 0,       y:78,   w:2,    h:80}
  out["corner_top_right"]       = { x: 118,     y:0,    w:120,  h:2}
  out["corner_bottom_right"]    = { x: 118,     y:78,   w:120,  h:80} 

  return out;
})();*/


export const edges_x = [0, 18, 40, 60, 80, 102, 120];
export const edges_y = [0, 18, 62, 80];

export const x_keys = Array.from({ length: 3 }, (_, r) =>
  Array.from({ length: 6 }, (_, c) => `g_r${r + 1}_c${c + 1}`)
).flat();

export const BASE_RECTS: Record<string, ZRect> = (() => {
  const out: Record<string, ZRect> = {};
  for (let r = 0; r < 3; r++) {
    for (let c = 0; c < 6; c++) {
      const x0 = edges_x[c];
      const x1 = edges_x[c + 1];
      const y0 = edges_y[r];
      const y1 = edges_y[r + 1];
      const key = `g_r${r + 1}_c${c + 1}`;
      out[key] = { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
    }
  }
  return out;

})();

export const CLASSIC_ZONE_KEYS = [
  "own_half",
  "opponent_half",
  "final_third",
  "box_left",
  "box_right",
  "six_left",
  "six_right",
] as const;

export const CLASSIC_RECTS: Record<string, ZRect> = {
  // clásicas
  "own_half"      : { x: 0,   y: 0,  w: 60, h: 80 },
  "opponent_half" : { x: 60,  y: 0,  w: 60, h: 80 },
  "final_third"   : { x: 80,  y: 0,  w: 40, h: 80 },

  // áreas
  "box_left"  : { x: 0,   y: 18, w: 18,  h: 44 },
  "box_right" : { x: 102, y: 18, w: 18,  h: 44 },
  "six_left"  : { x: 0,   y: 30, w: 6,   h: 20 },
  "six_right" : { x: 114, y: 30, w: 6,   h: 20 }
};

export const ZONE_RECTS: Record<string, ZRect> = {
  ...BASE_RECTS,
  ...CLASSIC_RECTS,
};

export const ZONE_KEYS =  [...x_keys, ...CLASSIC_ZONE_KEYS] as const;  

export function zoneLabel(id: string): string {
  const classic: Record<string, string> = {
    own_half: 'Mitad propia',
    opponent_half: 'Mitad rival',
    final_third: 'Último tercio',
    box_left: 'Área izquierda',
    box_right: 'Área derecha',
    six_left: 'Área pequeña izda.',
    six_right: 'Área pequeña dcha.',
  };
  if (classic[id]) return classic[id];

  const m = /^g_r(\d+)_c(\d+)$/.exec(id);
  if (m) {
    const r = parseInt(m[1], 10); // 1..3
    const c = parseInt(m[2], 10); // 1..6
    const ROWS = ['Superior', 'Central', 'Inferior'];
    const COLS = ['Banda izda', 'Medio-izda', 'Centro izda', 'Centro dcha', 'Medio-dcha', 'Banda dcha'];
    return `${ROWS[r - 1]} · ${COLS[c - 1]}`;
  }
  return id; // fallback por si añades algo nuevo
}
type ZoneDict = { x_min: number; x_max: number; y_min: number; y_max: number };

export function zoneLabelFromSpec(z?: string | ZoneDict): string {
  if (!z) return '';
  if (typeof z === 'string') return zoneLabel(z);
  return `Rect (${z.x_min}-${z.x_max}, ${z.y_min}-${z.y_max})`;
}