import React, { useMemo, useState } from "react";
import type { EventFilter } from "../types";

type Mode = "coords" | "zone";

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

function zoneFromXY(x: number, y: number): string | null {
    const inRightBox = x >= 102 && x <= 120 && y >= 18 && y <= 62;
    const inLeftBox  = x >= 0   && x <= 18  && y >= 18 && y <= 62;
    if (inRightBox) return "box_right";
    if (inLeftBox)  return "box_left";
    if (x >= 80) return "final_third";
    if (x >= 60) return "opponent_half";
    return "own_half";

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
        const z = zoneFromXY(x, y);
        if (z) updated.zone = z;
      }
      return updated;
    });
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
  const z = zoneFromXY(x, y);
  setHoverZ(z);
  onHoverZone?.(z ?? null);
};

  const clickHandler = (e: React.MouseEvent<SVGSVGElement>) => {
    if (selectedIndex == null) return;
    const { x, y } = pxToXY(e);
    if (mode === "coords") setStepCoords(selectedIndex, x, y);
    else {
      const z = zoneFromXY(x, y);
      if (z) setStepZone(selectedIndex, z);
    }
  };

  const contextHandler = (e: React.MouseEvent<SVGSVGElement>) => {
    e.preventDefault();
    if (selectedIndex == null) return;
    clearStep(selectedIndex);
  };
  
  const zoneRects = useMemo(() => {
    return {
      own_half:   { x: 0,   y: 0,  w: 60,  h: 80 },
      opponent_half: { x: 60,  y: 0,  w: 60,  h: 80 },
      final_third:   { x: 80,  y: 0,  w: 40,  h: 80 },
      box_left:   { x: 0,   y: 18, w: 18,  h: 44 },
      box_right:  { x: 102, y: 18, w: 18,  h: 44 },
    };
  }, []);

  return (
    <div className="bg-white rounded-xl shadow p-3">
      <div className="flex items-center justify-between mb-2">
        <div className="font-medium">Campo (click fija; botón derecho limpia)</div>
        <div className="text-xs text-gray-500">Modo: {mode === "coords" ? "Coordenadas" : "Zona"}</div>
      </div>

       <svg
            width={width}
            height={height}
            onMouseMove={hoverHandler}
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

    {/* Áreas */}

    {/* Izquierda */}

    <rect x={fieldX(0)} y={fieldY(18)} width={sx * 18} height={sy * 44} fill="none" stroke="#e5e7eb" strokeWidth={2} />
    <rect x={fieldX(0)} y={fieldY(30)} width={sx * 6}  height={sy * 20} fill="none" stroke="#e5e7eb" strokeWidth={2} />

    {/* Derecha */}

    <rect x={fieldX(120 - 18)} y={fieldY(18)} width={sx * 18} height={sy * 44} fill="none" stroke="#e5e7eb" strokeWidth={2} />
    <rect x={fieldX(120 - 6)}  y={fieldY(30)} width={sx * 6}  height={sy * 20} fill="none" stroke="#e5e7eb" strokeWidth={2} />

    {/* Overlay de zona por hover usando zoneRects */}
    {hoverZ && zoneRects[hoverZ as keyof typeof zoneRects] && (() => {
    const r = zoneRects[hoverZ as keyof typeof zoneRects];
    return (
        <rect
        x={fieldX(r.x)}
        y={fieldY(r.y)}
        width={r.w * sx}
        height={r.h * sy}
        fill="#ffffff22"
        stroke="#ffffff55"
        />
    );
    })()}
    
    {/* Overlay de zona por hover (el padre me la pasa con onHoverZone) */}
    {/* Nota: el padre decide cuál está activa y me vuelve a renderizar con una prop; */}
    {/* en esta versión lo dibujo directamente en SearchPage para tener control, */}
    {/* pero si quisiese, podría almacenar estado interno. */}
    {/* (Dejo el sitio aquí por claridad del layout) */}

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

          return (
            <g key={i} onClick={(ev) => { ev.stopPropagation(); onSelect(i); }}>
              {Tol}
              <circle cx={X} cy={Y} r={8} fill={color} stroke={selected ? "#ffffff" : "#111827"} strokeWidth={selected ? 3 : 2} />
              <text x={X} y={Y - 12} textAnchor="middle" fontSize={12} fill="#fff">{i + 1}</text>
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
