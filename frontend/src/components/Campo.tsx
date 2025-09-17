import React, {useState } from "react";
import type { EventFilter } from "../types";
import { ZONE_RECTS } from "../Zonas";
import { EVENT_ICONS } from "../eventIcons";

export type IconPack = Record<
  string,
  { url: string; size?: number; dx?: number; dy?: number }
>;


type Mode = "coords" | "zone" | "segment";

type Props = {
    steps : EventFilter[];
    selectedIndex : number | null;
    onSelect: (i: number | null) => void;
    onChange: (steps: EventFilter[]) => void;

    mode ?: Mode;
    snapZones ?: boolean;
    showTolerance ?: boolean;

    width ?: number;
    flip ?: boolean;

    onHoverZone ?: (z: string | null) => void;

};

const W = 120;
const H = 80;

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}


// Devuelve la zona más "pequeña" (más específica) que contiene (x,y)
function zoneAt(x: number, y: number): string | null {
  let bestId: string | null = null;
  let bestArea = Infinity;
  for (const [id, r] of Object.entries(ZONE_RECTS)) {
    const inside = x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h;
    if (!inside) continue;
    const area = r.w * r.h;
    if (area < bestArea) {
      bestArea = area;
      bestId = id;
    }
  }
  return bestId;
}

type ZoneDict = { x_min: number; x_max: number; y_min: number; y_max: number };

function isZoneDict(z: unknown): z is ZoneDict {
  return (
    typeof z === "object" &&
    z !== null &&
    "x_min" in z &&
    "x_max" in z &&
    "y_min" in z &&
    "y_max" in z
  );
}

function centerOfZone(s: EventFilter): {x:number;y:number}|null {
  if (typeof s.zone === "string") {
    const r = ZONE_RECTS[s.zone]; if (!r) return null;
    return { x: r.x + r.w/2, y: r.y + r.h/2 };
  }
  if (isZoneDict(s.zone)) {
    return {
      x: s.zone.x_min + (s.zone.x_max - s.zone.x_min)/2,
      y: s.zone.y_min + (s.zone.y_max - s.zone.y_min)/2,
    };
  }
  return null;
}

const EVENT_COLOR: Record<string, string> = {
  "Recovery": "#111827",
  "Pass": "#2563eb",
  "Shot": "#ef4444",
  "Dribble": "#8b5cf6",
  "Interception": "#f59e0b",
  "Duel": "#0ea5a4",
  "Ball Recovery": "#16a34a",
  "Ball Receipt": "#ca8a04",
  "Carry": "#6b7280",
  "Foul": "#7c3aed",
};

const GLYPH = {
    r: 8,
    thin: 1.6,
    thick: 2.4,
};

// Dibuja un “badge” de flag (success/goal/switch) junto al punto
function FlagBadge({
  x, y, label, fill, stroke,
}: { x: number; y: number; label: string; fill: string; stroke: string }) {
    const w = Math.max(18, 6 + label.length * 6);
    const h = 14;
    return (
        <g transform={`translate(${x},${y})`}>
        <rect
            x={-w / 2}
            y={-h / 2}
            width={w}
            height={h}
            rx={6}
            fill={fill}
            stroke={stroke}
            strokeWidth={0.8}
        />
        <text x={0} y={3} fontSize={9} textAnchor="middle" fill="#111">
            {label}
        </text>
        </g>
    );
}

function IconGlyph({
  url, x, y, size = 22, dx = 0, dy = 0,onMouseDown,
}: {url: string; x: number; y: number; size?: number; dx?: number; dy?: number;
  onMouseDown?: (e: React.MouseEvent<SVGImageElement>) => void;
}) {
  return (
    <image
      href={url}
      x={x - size / 2 + dx}
      y={y - size / 2 + dy}
      width={size}
      height={size}
      preserveAspectRatio="xMidYMid meet"
      style={{ cursor: "grab" }}
      onMouseDown={onMouseDown}
    />
  );
}


/// Icono por tipo de evento
function glyphForEvent(name: string, X: number, Y: number, color: string) {
  const r = GLYPH.r;
  const thin = GLYPH.thin;
  const thick = GLYPH.thick;

  switch (name) {
    case "Pass":
      // triángulo orientado “hacia arriba” como punta de flecha
      return (
        <polygon
          points={`${X},${Y - r} ${X + r},${Y + r*0.8} ${X - r},${Y + r*0.8}`}
          fill={color}
          stroke="#111827"
          strokeWidth={thin}
        />
      );

    case "Shot":
      // diana: círculo con un punto
      return (
        <g>
          <circle cx={X} cy={Y} r={r} fill="#fff" stroke={color} strokeWidth={thick}/>
          <circle cx={X} cy={Y} r={r*0.35} fill={color}/>
        </g>
      );

    case "Dribble":
      // zig-zag pequeño + punto
      return (
        <g>
          <path d={`M ${X - r},${Y + r*0.6} L ${X - r*0.3},${Y - r*0.4} L ${X + r*0.4},${Y + r*0.3} L ${X + r},${Y - r*0.8}`}
                fill="none" stroke={color} strokeWidth={thick}/>
          <circle cx={X} cy={Y} r={r*0.6} fill={color}/>
        </g>
      );

    case "Interception":
      // X
      return (
        <g stroke={color} strokeWidth={thick}>
          <line x1={X-r} y1={Y-r} x2={X+r} y2={Y+r}/>
          <line x1={X+r} y1={Y-r} x2={X-r} y2={Y+r}/>
        </g>
      );

    case "Duel":
      // dos puntos enfrentados
      return (
        <g>
          <circle cx={X - r*0.9} cy={Y} r={r*0.6} fill={color}/>
          <circle cx={X + r*0.9} cy={Y} r={r*0.6} fill={color}/>
        </g>
      );

    case "Ball Recovery":
    case "Recovery":
      // rombo
      return (
        <polygon
          points={`${X},${Y - r} ${X + r},${Y} ${X},${Y + r} ${X - r},${Y}`}
          fill={color}
          stroke="#111827"
          strokeWidth={thin}
        />
      );

    case "Ball Receipt":
      // anillo
      return (
        <g>
          <circle cx={X} cy={Y} r={r*0.9} fill="#fff" stroke={color} strokeWidth={thick}/>
          <circle cx={X} cy={Y} r={r*0.4} fill={color}/>
        </g>
      );

    case "Carry":
      // línea corta “de arrastre”
      return (
        <g>
          <line x1={X - r} y1={Y} x2={X + r} y2={Y} stroke={color} strokeWidth={thick}/>
          <circle cx={X} cy={Y} r={r*0.5} fill={color}/>
        </g>
      );

    case "Foul":
      // hexágono
      return (
        <polygon
          points={`${X - r},${Y - r/2} ${X},${Y - r} ${X + r},${Y - r/2} ${X + r},${Y + r/2} ${X},${Y + r} ${X - r},${Y + r/2}`}
          fill={color}
          stroke="#111827"
          strokeWidth={thin}
        />
      );

    default:
      // fallback: punto sólido (lo que ya tenías)
      return <circle cx={X} cy={Y} r={r*0.9} fill={color} stroke="#111827" strokeWidth={thin} />;
  }
}

export default function Campo({
    steps, selectedIndex, onSelect, onChange, mode ="coords", snapZones = true, showTolerance = true, width= 720, flip = false, onHoverZone,
}: Props) {

    const height = Math.round((width*H) / W);
    const sx = width / W;
    const sy = height / H;

    const fieldX = (x: number) => (flip ? (W - x) : x) * sx;
    const fieldY = (y: number) => y * sy;

    const pxToXY = (evt: React.MouseEvent<SVGSVGElement, MouseEvent>) => {
        const svg = evt.currentTarget;
        const pt = svg.createSVGPoint();
        pt.x = evt.clientX; pt.y = evt.clientY;
        const ctm = svg.getScreenCTM();
        if (!ctm) return { x: 0, y: 0 };
        const inv = ctm.inverse();
        const p = pt.matrixTransform(inv);
        const xf = clamp(p.x / sx, 0, W);
        const yf = clamp(p.y / sy, 0, H);
        // Deshago el flip al guardar
        const x = flip ? Number((W - xf).toFixed(1)) : Number(xf.toFixed(1));
        const y = Number(yf.toFixed(1));
        return { x, y };
  };

  function setStepCoords(i: number, x: number, y: number) {
    const next = steps.map((s, idx) => {
      if (idx !== i) return s;
      const updated: EventFilter = { ...s, start_x: x, start_y: y };
      if (snapZones) {
        const z = zoneAt(x, y);
        if (z) updated.zone = z;
      }
      return updated;
    });
    onChange(next);
  }
  function setStepEnd(i: number, x: number, y: number) {
    const next = steps.map((s, idx) => (idx === i ? { ...s, end_x: x, end_y: y } : s));
    onChange(next);
  }
  function setStepZone(i: number, zone: string) {
    const next = steps.map((s, idx) => (idx === i ? { ...s, zone, start_x: undefined, start_y: undefined } : s));
    onChange(next);
  }
  function clearStep(i: number) {
    const next = steps.map((s, idx) => (idx === i ? { ...s, start_x: undefined, start_y: undefined } : s));
    onChange(next);
  }

const [hoverZ, setHoverZ] = useState<string | null>(null);

const hoverHandler = (e: React.MouseEvent<SVGSVGElement>) => {
  const { x, y } = pxToXY(e);
  const z = zoneAt(x, y);
  setHoverZ(z);
  onHoverZone?.(z ?? null);
};

const clickHandler = (e: React.MouseEvent<SVGSVGElement>) => {
    if (selectedIndex == null) return;
    const { x, y } = pxToXY(e);
    if (mode === "coords") {
      setStepCoords(selectedIndex, x, y);
    } else if (mode === "zone") {
      const z = zoneAt(x, y); if (z) setStepZone(selectedIndex, z);
    } else { // "segmento": primer click fija inicio, segundo click fija fin
      const s = steps[selectedIndex];
      if (s.start_x == null || s.start_y == null) setStepCoords(selectedIndex, x, y);
      else setStepEnd(selectedIndex, x, y);
    }
};
  

const contextHandler = (e: React.MouseEvent<SVGSVGElement>) => {
    e.preventDefault();
    if (selectedIndex == null) return;
    clearStep(selectedIndex);
};

  // Estado de drag: qué punto estoy moviendo
const [drag, setDrag] = useState<null | { i: number; which: "start" | "end" }>(null);

const onMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    hoverHandler(e); // mantengo el hover de zona
    if (!drag) return;
    const { x, y } = pxToXY(e);
    const i = drag.i;
    if (drag.which === "start") {
        setStepCoords(i, x, y);
    } else {
        setStepEnd(i, x, y);
    }
    };

const onMouseUp = () => setDrag(null);
const onMouseLeave = () => setDrag(null);
  
const markers = (
    <defs>
      <marker id="arrowhead" orient="auto" markerWidth="8" markerHeight="8" refX="8" refY="4">
        <path d="M0,0 L8,4 L0,8 z" fill="#111827" />
      </marker>
      <marker id="arrowhead-pass" orient="auto" markerWidth="8" markerHeight="8" refX="8" refY="4">
        <path d="M0,0 L8,4 L0,8 z" fill="#2563eb" />
      </marker>
    </defs>
);

type Seg = { x1: number; y1: number; x2: number; y2: number; eventName: string; };
const segments: Seg[] = [];
for (let i = 0; i < steps.length; i++) {
    const s = steps[i];
    const name = (Array.isArray(s.event) ? s.event[0] : s.event) || "";
    const start = (s.start_x != null && s.start_y != null)
        ? { x: s.start_x as number, y: s.start_y as number }
        : centerOfZone(s);
    if (!start) continue;

    // 1) Si el paso tiene fin explícito, lo uso
    if (s.end_x != null && s.end_y != null) {
    segments.push({ x1: start.x, y1: start.y, x2: s.end_x, y2: s.end_y, eventName: name });
    continue;
    }

    // 2) Si no, conecto con el siguiente paso (coords o zona)
    const next = steps[i + 1];
    if (next) {
    const end = (next.start_x != null && next.start_y != null)
        ? { x: next.start_x as number, y: next.start_y as number }
        : centerOfZone(next);
    if (end) {
        segments.push({ x1: start.x, y1: start.y, x2: end.x, y2: end.y, eventName: name });
    }
    }
}
  // helper para estilo de línea
function lineProps(evName: string) {
    if (evName === "Pass") {
      return { stroke: "#2563eb", dash: null, marker: "url(#arrowhead-pass)" };
    }
    if (evName === "Dribble" || evName === "Carry") {
      return { stroke: "#8b5cf6", dash: "6 5", marker: "url(#arrowhead)" }; // punta neutra
    }
    return { stroke: "#111827", dash: null, marker: "url(#arrowhead)" };    
}

  /*const zoneRects = useMemo(() => {
    return {
      own_half:   { x: 0,   y: 0,  w: 60,  h: 80 },
      opponent_half: { x: 60,  y: 0,  w: 60,  h: 80 },
      final_third:   { x: 80,  y: 0,  w: 40,  h: 80 },
      box_left:   { x: 0,   y: 18, w: 18,  h: 44 },
      box_right:  { x: 102, y: 18, w: 18,  h: 44 },
    };
  }, []);
  */
return (
    <div className="bg-white rounded-xl shadow p-4 lg:p-6">
      <div className="flex items-center justify-between mb-2">
        <div className="font-medium">Campo (click fija; botón derecho limpia)</div>
        <div className="text-xs text-gray-500">Modo: {mode === "coords" ? "Coordenadas" : "Zona"}</div>
      </div>

       <svg
            width={width}
            height={height}
            onMouseMove={onMouseMove}
            onMouseUp={onMouseUp}
            onMouseLeave={onMouseLeave}
            onClick={clickHandler}
            onContextMenu={contextHandler}
            className="cursor-crosshair select-none bg-[#0b7a37] rounded-lg"
      >

    {/* Césped + perímetro */}

    <rect x={0} y={0} width={width} height={height} fill="#0b7a37" rx={8} />
    <rect x={1} y={1} width={width - 2} height={height - 2} fill="none" stroke="#e5e7eb" strokeWidth={2} />

    {/* Medio campo */}

    <line x1={fieldX(60)} y1={fieldY(0)} x2={fieldX(60)} y2={fieldY(80)} stroke="#e5e7eb" strokeWidth={2} />
    <circle cx={fieldX(60)} cy={fieldY(40)} r={9.15 * sx} fill="none" stroke="#e5e7eb" strokeWidth={2} />

    {/* Flecha de dirección de ataque */}
    <g transform={`translate(${fieldX(60)}, ${fieldY(78)})`}>
      <text
        x={0}
        y={0}
        textAnchor="middle"
        fontSize={14}
        fill="white"
        fontWeight="bold"
      >
        {flip ? "← Atacan hacia la izquierda" : "Atacan hacia la derecha →"}
      </text>
    </g>
    {/* Áreas */}

    {/* Izquierda */}

    <rect x={fieldX(0)} y={fieldY(18)} width={sx * 18} height={sy * 44} fill="none" stroke="#e5e7eb" strokeWidth={2} />
    <rect x={fieldX(0)} y={fieldY(30)} width={sx * 6}  height={sy * 20} fill="none" stroke="#e5e7eb" strokeWidth={2} />

    {/* Derecha */}

    <rect x={fieldX(120 - 18)} y={fieldY(18)} width={sx * 18} height={sy * 44} fill="none" stroke="#e5e7eb" strokeWidth={2} />
    <rect x={fieldX(120 - 6)}  y={fieldY(30)} width={sx * 6}  height={sy * 20} fill="none" stroke="#e5e7eb" strokeWidth={2} />

    {markers}
    {/* Overlay por HOVER */}
        {hoverZ && ZONE_RECTS[hoverZ] && (() => {
        const r = ZONE_RECTS[hoverZ];
        return (
            <rect
            x={fieldX(r.x)}
            y={fieldY(r.y)}
            width={r.w * sx}
            height={r.h * sy}
            fill="#ffffff18"
            stroke="#ffffff66"
            strokeWidth={2}
            pointerEvents="none"   // <- no roba el ratón
            />
        );
        })()}
    {/* Overlay de zona por hover usando zoneRects */}
    {/* Overlays de todas las zonas elegidas */}
        {steps.map((s, i) => {
        const name = Array.isArray(s.event) ? s.event[0] : s.event;
        const color = EVENT_COLOR[name] ?? "#111827";

        if (typeof s.zone === "string") {
            const r = ZONE_RECTS[s.zone]; if (!r) return null;
            return (
            <rect key={`zone-${i}`}
                x={fieldX(r.x)} y={fieldY(r.y)}
                width={r.w * sx} height={r.h * sy}
                fill="#ffffff22"
                stroke={color}
                strokeWidth={i === selectedIndex ? 3 : 2}
            />
            );
        }
        if (isZoneDict(s.zone)) {
            const z = s.zone;
            const r = { x: z.x_min, y: z.y_min, w: z.x_max - z.x_min, h: z.y_max - z.y_min };
            return (
            <rect key={`zone-${i}`}
                x={fieldX(r.x)} y={fieldY(r.y)}
                width={r.w * sx} height={r.h * sy}
                fill="#ffffff22"
                stroke={color}
                strokeWidth={i === selectedIndex ? 3 : 2}
            />
            );
        }
        return null;
        })}

    {/* Zona del paso seleccionado (string o rect dict) */}
        {selectedIndex != null && (() => {
        const s = steps[selectedIndex];
        // 1) si es string → buscamos en ZONE_RECTS
        let r = typeof s.zone === "string" ? ZONE_RECTS[s.zone] : undefined;
        // 2) si es dict → construimos el rect a partir de x_min..y_max
        if (!r && isZoneDict(s.zone)) {
            const z = s.zone
            r = { x: z.x_min, y: z.y_min, w: z.x_max - z.x_min, h: z.y_max - z.y_min };
        }
        if (!r) return null;
        return (
            <rect
            x={fieldX(r.x)} y={fieldY(r.y)}
            width={r.w * sx} height={r.h * sy}
            fill="#22c55e22" stroke="#22c55e" strokeWidth={3}
            />
        );
    })()}
    {/* Dibujo de segmentos */}
        {segments.map((g, i) => {
          const { stroke, dash, marker } = lineProps(g.eventName);
          
          return (
            <line
              key={`seg-${i}`}
              x1={fieldX(g.x1)} y1={fieldY(g.y1)}
              x2={fieldX(g.x2)} y2={fieldY(g.y2)}
              stroke={stroke}
              strokeWidth={3}
              markerEnd={marker}
              strokeDasharray={dash ?? undefined}
              opacity={0.95}
            />
          );
        })}


    {/* Marcadores de pasos */}
        {steps.map((s, i) => {
          const has = typeof s.start_x === "number" && typeof s.start_y === "number";
          if (!has) return null;
          const name = Array.isArray(s.event) ? s.event[0] : s.event;
          const color = EVENT_COLOR[name] ?? "#111827";
          const X = fieldX(s.start_x!);
          const Y = fieldY(s.start_y!);
          const selected = i === selectedIndex;

          // círculo de tolerancia si procede
          const Tol = showTolerance && s.tolerance ? (
            <circle
              cx={X}
              cy={Y}
              r={s.tolerance * sx}
              fill="#ffffff22"
              stroke="#ffffff55"
              strokeDasharray="4 4"
            />
          ) : null;

        const packIcon = EVENT_ICONS[name];

        return (
            <g key={i} onClick={(ev) => { ev.stopPropagation(); onSelect(i); }}>
              {Tol}

              {/* Icono por paso > icono de pack > glyph fallback */}
              {packIcon?.url ? (
                <IconGlyph
                    url={packIcon.url}
                    x={X}
                    y={Y}
                    size={packIcon.size ?? 22}
                    dx={packIcon.dx ?? 0}
                    dy={packIcon.dy ?? 0}
                    onMouseDown={(e) => {
                    e.stopPropagation();
                    setDrag({ i, which: "start" });
                    }}
                />
                ) : (
                // fallback a la forma SVG interna
                <>
                    {glyphForEvent(name, X, Y, color)}
                </>
                )}

              {/* Aro de selección */}
              {selected && (
                <circle cx={X} cy={Y} r={GLYPH.r + 6} fill="none" stroke="#fff" strokeWidth={2} />
              )}

              {/* Índice del paso */}
              <text x={X} y={Y - 12} textAnchor="middle" fontSize={12} fill="#fff">
                {i + 1}
              </text>

              {/* Badges de flags debajo del marcador */}
              <g transform={`translate(0, ${GLYPH.r + 16})`}>
                {s.success && (
                  <FlagBadge x={X - 26} y={Y} label="ok" fill="#d1fae5" stroke="#10b981" />
                )}
                {s.goal && (
                  <FlagBadge x={X} y={Y} label="goal" fill="#fef3c7" stroke="#f59e0b" />
                )}
                {s.switch_possession && (
                  <FlagBadge x={X + 28} y={Y} label="switch" fill="#e0f2fe" stroke="#38bdf8" />
                )}
              </g>

              {/* Punto final si existe (arrastrable) */}
              {typeof s.end_x === "number" && typeof s.end_y === "number" && (
                <circle
                  cx={fieldX(s.end_x)}
                  cy={fieldY(s.end_y)}
                  r={6}
                  fill="#fff"
                  stroke={color}
                  strokeWidth={2}
                  onMouseDown={(ev) => {
                    ev.stopPropagation();
                    setDrag({ i, which: "end" });
                  }}
                  style={{ cursor: "grab" }}
                />
              )}
            </g>
          );
        })}
      </svg>

      {/* Leyenda */}
      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs">
        <span className="text-gray-600">Leyenda:</span>
        {Object.entries(EVENT_COLOR).map(([k, v]) => (
          <span key={k} className="inline-flex items-center gap-1">
            <span style={{ background: v }} className="inline-block w-3 h-3 rounded-full border" />
            {k}
          </span>
        ))}
      </div>
    </div>
  );
}
