import { useState, type ChangeEvent } from "react";
import type { EventFilter, TeamRule } from "../types";
export type EventDTO = Record<string, unknown>;

const TEAM_OPTIONS: TeamRule[] = ["any", "same", "opponent"];
// Lista que voy a enseñar en el selector de eventos
const EVENT_OPTIONS = [
    "Recovery",
    "Pass",
    "Shot",
    "Dribble",
    "Interception",
    "Duel",
    "Ball Recovery",
    "Ball Receipt",
    "Carry",
    "Foul",
];

const ZONES = ["", "final_third", "opponent_half", "own_half", "box_left", "box_right"];

function OutcomesInput({
    value,
    onOutcomesChange,
}:{
    value?: string[];
    onOutcomesChange: (v:string[]) => void;
}){

    const [txt, setTxt] = useState((value ?? [].join(","))); //Estado local del texto

    const handleChanges = (e: ChangeEvent<HTMLInputElement>) =>{
        setTxt(e.target.value);
        onOutcomesChange(e.target.value.split(",").map((s) => s.trim()).filter(Boolean));
    };
    return(
        <input
        className="mt-1 w-full border rounded px-2 py-2"
        placeholder="Complete,Won,Goal…"
        value={txt}
        onChange={handleChanges}
        />
    );
}

function PasoFila({
    paso,
    indice,
    seleccionado,
    onSelect,
    onChange,
    onRemove,
}: {
    paso: EventFilter;
    indice: number;
    seleccionado: boolean;
    onSelect: () => void;
    onChange: (s: EventFilter) => void;
    onRemove: () => void;

}){

    const onEvtChange = (e: ChangeEvent<HTMLSelectElement>) =>
    onChange({ ...paso, event: e.target.value });

  const onZoneChange = (e: ChangeEvent<HTMLSelectElement>) =>
    onChange({ ...paso, zone: e.target.value || undefined });

  const onTeamChange = (e: ChangeEvent<HTMLSelectElement>) =>
    onChange({ ...paso, team: e.target.value as TeamRule });

  const onSuccessChange = (e: ChangeEvent<HTMLInputElement>) =>
    onChange({ ...paso, success: e.target.checked });

  const onGoalChange = (e: ChangeEvent<HTMLInputElement>) =>
    onChange({ ...paso, goal: e.target.checked });

  const onSwitchChange = (e: ChangeEvent<HTMLInputElement>) =>
    onChange({ ...paso, switch_possession: e.target.checked });

  const onStartXChange = (e: ChangeEvent<HTMLInputElement>) =>
    onChange({
      ...paso,
      start_x: e.target.value ? Number(e.target.value) : undefined,
    });

  const onStartYChange = (e: ChangeEvent<HTMLInputElement>) =>
    onChange({
      ...paso,
      start_y: e.target.value ? Number(e.target.value) : undefined,
    });

  const onTolChange = (e: ChangeEvent<HTMLInputElement>) =>
    onChange({
      ...paso,
      tolerance: e.target.value ? Number(e.target.value) : undefined,
    });

    return(
        <div 
        onClick={onSelect}
        className={`grid md:grid-cols-6 gap-3 p-3 border rounded-lg bg-white cursor-pointer transition
        ${seleccionado ? "ring-2 ring-emerald-500 border-emerald-500" : "hover:border-gray-300"}`}
        title="Clic para seleccionar este paso"
        >

        {/* Evento */}
        <div className="md: col-span-2">
            <label className="text-xs text-gray-600">Paso #{indice +1} Evento</label>
            <select
                className="mt-1 w-full border rounded px-2 py-2"
                value={typeof paso.event === "string" ? paso.event: ""}
                onClick={(e) => e.stopPropagation()}
                onChange={onEvtChange}
            >
                {EVENT_OPTIONS.map((o)=> (
                    <option key = {o} value = {o}>
                        {o}
                    </option>
                ))}
            </select>
        </div>

        {/* Outcomes */}
        <div onClick={(e) => e.stopPropagation()}>
            <label className="text-xs text-gray-600">Outcomes (coma)</label>
            <OutcomesInput
                value={paso.outcomes}
                onOutcomesChange={(v) => onChange({ ...paso, outcomes: v })}
            />
        </div>

        {/* Zona */}
        <div onClick={(e) => e.stopPropagation()}>
            <label className="text-xs text-gray-600">Zona</label>
            <select
                className="mt-1 w-full border rounded px-2 py-2"
                value={typeof paso.zone === "string" ? paso.zone : ""}
                onChange={onZoneChange}
            >
            {ZONES.map((z) => (
                <option key={z} value={z}>
                {z || "—"}
                </option>
            ))}
            </select>
        </div>

        {/* Regla de equipo */}
        <div onClick={(e) => e.stopPropagation()}>
            <label className="text-xs text-gray-600">Team</label>
            <select
                className="mt-1 w-full border rounded px-2 py-2"
                value={(paso.team ?? "any") as TeamRule}
                onChange={onTeamChange}
            >
            {TEAM_OPTIONS.map(t => (
                <option key={t} value={t}>{t}</option>
            ))}
            </select>
        </div>

        {/* Flags */}
        <div className="flex items-end gap-3" onClick={(e) => e.stopPropagation()}>
            <label className="flex items-center gap-1 text-sm">
            <input
                type="checkbox"
                checked={!!paso.success}
                onChange={onSuccessChange}
            />
            success
            </label>
            <label className="flex items-center gap-1 text-sm">
            <input
                type="checkbox"
                checked={!!paso.goal}
                onChange={onGoalChange}
            />
            goal
            </label>
            <label className="flex items-center gap-1 text-sm">
            <input
                type="checkbox"
                checked={!!paso.switch_possession}
                onChange={onSwitchChange}
            />
            switch
            </label>

            {/* Botón quitar (paro propagación para no cambiar la selección al pulsar) */}
            <button
            type="button"
            onClick={(e) => {
                e.stopPropagation();
                onRemove();
            }}
            className="ml-auto text-red-600 text-sm"
            title="Quitar este paso"
            >
            Quitar
            </button>
        </div>

            {/* Coordenadas, fin opcional y tolerancia */}
            <div className="md:col-span-6 grid grid-cols-5 gap-3" onClick={(e) => e.stopPropagation()}>
                <div>
                    <label className="text-xs text-gray-600">start_x</label>
                    <input type="number" className="mt-1 w-full border rounded px-2 py-2"
                    value={paso.start_x ?? ""} onChange={onStartXChange}/>
                </div>
            <div>
                <label className="text-xs text-gray-600">start_y</label>
                <input type="number" className="mt-1 w-full border rounded px-2 py-2"
                value={paso.start_y ?? ""} onChange={onStartYChange}/>
            </div>
            <div>
                <label className="text-xs text-gray-600">end_x</label>
                <input
                type="number" className="mt-1 w-full border rounded px-2 py-2"
                value={paso.end_x ?? ""}
                onChange={(e) => onChange({ ...paso, end_x: e.target.value ? Number(e.target.value) : undefined })}
                />
            </div>
            <div>
                <label className="text-xs text-gray-600">end_y</label>
                <input
                type="number" className="mt-1 w-full border rounded px-2 py-2"
                value={paso.end_y ?? ""}
                onChange={(e) => onChange({ ...paso, end_y: e.target.value ? Number(e.target.value) : undefined })}
                />
            </div>
            <div>
                <label className="text-xs text-gray-600">tolerance</label>
                <input type="number" className="mt-1 w-full border rounded px-2 py-2"
                value={paso.tolerance ?? ""} onChange={onTolChange}/>
            </div>
        </div>
    </div>
    );
}

/**
 * Builder del patrón.
 * Aquí gestiono la lista de pasos y quién está seleccionado.
 * Ojo: dejo el API del componente preparado para integrarlo con mi "Pitch"
 * (campo táctico) más adelante: selectedIndex + onSelect.
 */

export default function PatternBuilder({
    value,
    onChange,
    selectedIndex,
    onSelect,
}: {
    value: EventFilter[];
    onChange: (v: EventFilter[]) => void;
    selectedIndex: number | null;
    onSelect: (i: number) => void;
}) {
    // Añadir un paso nuevo: por defecto metemos recovery (útil)
    const anadirPaso = () => onChange([...value, {event:"Recovery"}]);

    //Actualizar un paso en concreto
    const actualizarPaso = (i:number, s: EventFilter) =>
        onChange(value.map((v, idx) =>(idx === i ? s : v)));

    //Quitar un paso (filtro por indice)
    const quitarPaso = (i:number) => onChange(value.filter ((_, idx) => idx !== i));

    return(
        <div className="space-y-3">
      {/* Header del builder */}
      <div className="flex items-center justify-between">
        <h3 className="font-medium">Patrón</h3>
        <button
          type="button"
          onClick={anadirPaso}
          className="px-3 py-1.5 rounded bg-black text-white text-sm"
        >
          + Añadir paso
        </button>
      </div>

      {/* Mensaje si no hay pasos */}
      {value.length === 0 && (
        <div className="text-sm text-gray-500">Añade el primer paso.</div>
      )}

      {/* Lista de pasos */}
      <div className="space-y-3">
        {value.map((p, i) => (
          <PasoFila
            key={i}
            paso={p}
            indice={i}
            seleccionado={i === selectedIndex}
            onSelect={() => onSelect(i)}
            onChange={(ns) => actualizarPaso(i, ns)}
            onRemove={() => quitarPaso(i)}
          />
        ))}
      </div>
    </div>
  );
    
}


