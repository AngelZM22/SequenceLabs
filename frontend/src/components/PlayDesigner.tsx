import { useState, useEffect} from "react";
import type { EventFilter, TeamRule } from "../types";
import Campo from "./Campo";
import { OUTCOMES_FALLBACK } from "../OutcomesFallback";
import { getOutcomes, getPlayers } from "../api";
import { zoneLabel, zoneLabelFromSpec } from "../Zonas";
import type {Option} from "../types";



const EVENT_OPTIONS = [
    "Recovery", "Pass", "Shot", "Dribble", "Interception",
  "Duel", "Ball Recovery", "Ball Receipt", "Carry", "Foul", "Goal Keeper"
];

const TEAM_OPTIONS: TeamRule[] = ["any", "same", "opponent"];
//const ZONE_OPTIONS = ["", "final_third", "opponent_half", "own_half", "box_left", "box_right"] as const;


type Props = {
  value: EventFilter[];
  onChange: (v: EventFilter[]) => void;
  teamId?: number;
  seasonId?: number;
};

export default function PlayDesigner({ value, onChange, teamId, seasonId }: Props){

    const [sel, setSel] = useState<number | null>(value.length ? 0 : null);

    // ajustes para la interacción del campo
    const [mode, setMode] = useState<"coords" | "zone">("coords");
    const [snapZones, setSnapZones] = useState(true);
    const [showTol, setShowTol] = useState(true);
    const [flip, setFlip] = useState(false);

    // Resaltar zona 
    const [hoverZone, setHoverZone] = useState<string | null>(null);
    // Para añadir pasos nuevos
    const [toolEvent, setToolEvent] = useState<string>("Recovery");
    const [toolOutcomes, setToolOutcomes] = useState<string[]>([]);
    const [availableOutcomes, setAvailableOutcomes] = useState<string[]>([]);

    const [toolPlayerId, setToolPlayerId] = useState<number | undefined>(undefined);
    const [playerOptions, setPlayerOptions] = useState<Option[]>([]);

    const editing = sel != null;
    const current = editing ? value[sel!] : undefined;

    const evForOutcomes =
        editing
            ? (Array.isArray(current?.event) ? current?.event[0] : (current?.event as string) || "")
            : toolEvent;

        useEffect(() => {
        let cancel = false;
        async function load() {
            const fromApi = await getOutcomes(evForOutcomes);
            const list = (fromApi && fromApi.length ? fromApi : (OUTCOMES_FALLBACK[evForOutcomes] || []))
            .sort((a, b) => a.localeCompare(b));

            if (!cancel) {
            setAvailableOutcomes(list);
            // Si cambia el catálogo, limpia seleccionados que ya no existan
            setToolOutcomes(prev => prev.filter(o => list.includes(o)));
            }
        }
        load();
        return () => { cancel = true; };
        }, [evForOutcomes]);

    useEffect(() => {
        let cancel = false;

        async function loadPlayers() {
            // Filtra por team si hay team; si no, por season; si no, vacío
            const opts = await (
            teamId ? getPlayers(teamId, seasonId)
                    : (seasonId ? getPlayers(undefined, seasonId) : Promise.resolve([]))
            );
            if (!cancel) setPlayerOptions(opts || []);
        }

        loadPlayers();
        return () => { cancel = true; };
        }, [teamId, seasonId]);

    

    const [toolTeam, setToolTeam] = useState<TeamRule>("any");
    const [toolSuccess, setToolSuccess] = useState(false);
    const [toolGoal, setToolGoal] = useState(false);
    const [toolSwitch, setToolSwitch] = useState(false);
    const [toolOptional, setToolOptional] = useState(false);
    const [toolTol, setToolTol] = useState<number>(10);
    
    useEffect(() => {
        if (sel == null) return;
        const s = value[sel];
        const ev = Array.isArray(s.event) ? s.event[0] : (s.event as string) || "";
        setToolEvent(ev);
        setToolOutcomes(s.outcomes ?? []);
        setToolTeam((s.team as TeamRule) ?? "any");
        setToolSuccess(!!s.success);
        setToolGoal(!!s.goal);
        setToolSwitch(!!s.switch_possession);
        setToolOptional(!!s.optional);
        setToolTol(s.tolerance ?? 10);
        setToolPlayerId(s.player_id ?? undefined);
        }, [sel, value]);

/*    const outcomesArr = useMemo(
    () => toolOutcomes.split(",").map(s => s.trim()).filter(Boolean),
    [toolOutcomes]
  );*/

    const addStep = () => {
        const nuevo: EventFilter = {
            event: toolEvent,
            outcomes: toolOutcomes.length ? toolOutcomes : undefined,
            team: toolTeam || undefined,
            success: toolSuccess || undefined,
            goal: toolGoal || undefined,
            switch_possession: toolSwitch || undefined,
            optional: toolOptional || undefined,
            tolerance: toolTol || undefined,
            //zone: toolZone || undefined,
            player_id: toolPlayerId ?? undefined,
        };

        const next = [...value, nuevo];
        onChange(next);
        setSel(next.length - 1);

    };

    const updateStep = (i: number, patch: Partial<EventFilter>) =>
        onChange(value.map((s, idx) => (idx === i ? { ...s, ...patch } : s)));

    const removeStep = (i: number) => {
        const next = value.filter((_, idx) => idx !== i);
        onChange(next);
        setSel(next.length ? Math.min(i, next.length - 1) : null);
    };

    const onToggleGoal = (v: boolean) => {
    if (editing) updateStep(sel!, { goal: v || undefined });
    else setToolGoal(v);
    };

    const onToggleSuccess = (v: boolean) => {
    if (editing) updateStep(sel!, { success: v || undefined });
    else setToolSuccess(v);
    };

    const onToggleSwitch = (v: boolean) => {
    if (editing) updateStep(sel!, { switch_possession: v || undefined });
    else setToolSwitch(v);
    };

    const onToggleOptional = (v: boolean) => {
    if (editing) updateStep(sel!, { optional: v || undefined });
    else setToolOptional(v);
    };


    

    const handleReset = () => {
    // Vaciar pasos
    onChange([]);

    // Quitar selección y hover
    setSel(null);
    setHoverZone(null);

    // Resetear herramienta (ajústalo a tus defaults)
    setToolEvent("");
    setToolOutcomes([]);
    setToolTeam("any");
    setToolSuccess(false);
    setToolGoal(false);
    setToolSwitch(false);
    setToolOptional(false);
    setToolTol(10);

    // Resetear ajustes del campo si quieres
    setMode("coords");
    setSnapZones(true);
    setShowTol(true);
    setFlip(false);
    };
    

    const Flag = ({ children }: { children: React.ReactNode }) => (
    <span className="inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] text-gray-700 bg-gray-50">
      {children}
    </span>
);

    return(
         <div className="space-y-6">

            {/* Panel de controles */}
            <div className="space-y-4 bg-white rounded-xl shadow p-4">
                <div className="font-semibold">Diseñar jugada</div>

                {/* Herramienta para crear pasos */}
                <div className="grid md:grid-cols-2 gap-3">
                <label className="text-sm">
                    Evento
                    <select className="mt-1 w-full border rounded px-2 py-2" value={toolEvent} onChange={(e)=>setToolEvent(e.target.value)}>
                    {EVENT_OPTIONS.map(e => <option key={e} value={e}>{e}</option>)}
                    </select>
                </label>
                <label className="text-sm">
                Outcomes
                <div className="mt-1 grid grid-cols-2 gap-2 border rounded p-2 max-h-32 overflow-auto">
                    {availableOutcomes.length === 0 && (
                    <div className="text-xs text-gray-500">— Sin outcomes para este evento —</div>
                    )}
                    {availableOutcomes.map((o) => {
                    const checked = editing
                        ? (current?.outcomes?.includes(o) ?? false)
                        : toolOutcomes.includes(o);
                    return (
                        <label key={o} className="flex items-center gap-2 text-sm">
                        <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                            const checked = e.currentTarget.checked;
                            if (editing) {
                                const prev = current?.outcomes ?? [];
                                const next = checked ? [...prev, o] : prev.filter(x => x !== o);
                                updateStep(sel!, { outcomes: next.length ? next : undefined });
                            } else {
                                setToolOutcomes(prev => checked ? [...prev, o] : prev.filter(x => x !== o));
                            }
                            }}
                        />
                        {o}
                        </label>
                    );
                    })}
                </div>
                </label>
                <label className="text-sm">
                    Team
                    <select
                        className="mt-1 w-full border rounded px-2 py-2"
                        value={editing ? (current?.team ?? "any") : toolTeam}
                        onChange={(e)=>{
                            const v = e.target.value as TeamRule;
                            if (editing) updateStep(sel!, { team: v === "any" ? undefined : v });
                            else setToolTeam(v);
                        }}
                        >
                        {TEAM_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                </label>
                <label className="text-sm">
                    Tolerancia
                    <input
                        type="number"
                        className="mt-1 w-full border rounded px-2 py-2"
                        value={editing ? (current?.tolerance ?? toolTol) : toolTol}
                        onChange={(e)=> {
                            const n = Number(e.target.value) || 0;
                            if (editing) updateStep(sel!, { tolerance: n || undefined });
                            else setToolTol(n);
                        }}
                        />
                </label>
                <div className="flex items-end gap-4">
                    <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={editing ? !!current?.success : toolSuccess} onChange={(e)=>onToggleSuccess(e.target.checked)} /> success
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={editing ? !!current?.goal : toolGoal} onChange={(e)=>onToggleGoal(e.target.checked)} /> goal
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={editing ? !!current?.switch_possession : toolSwitch} onChange={(e)=>onToggleSwitch(e.target.checked)} /> switch
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={editing ? !!current?.optional: toolOptional} onChange={(e)=>onToggleOptional(e.target.checked)} /> optional
                    </label>
                </div>

                <div className="space-y-2">
                    <label className="block text-sm font-medium">Jugador (opcional para este paso)</label>
                    <select
                        className="border rounded px-3 py-2 w-full"
                        value={editing ? (current?.player_id ?? "") : (toolPlayerId ?? "")}
                        onChange={e => {
                        const v = e.target.value ? Number(e.target.value) : undefined;
                        if (editing) updateStep(sel!, { player_id: v });
                        else setToolPlayerId(v);
                        }}
                        >
                        <option value="">(cualquiera)</option>
                        {playerOptions.map(o => (
                        <option key={o.id} value={o.id}>{o.label}</option>
                        ))}
                    </select>
                </div>
                
                </div>

                <div className="flex gap-2">
                <button type="button" onClick={addStep} className="px-3 py-2 rounded bg-black text-white text-sm">+ Añadir paso</button>
                <button type="button" onClick={handleReset} className="px-3 py-2 rounded border text-sm"> Reset </button>
                </div>

                {/* Lista rápida de pasos para seleccionar/eliminar */}
                <div className="space-y-2">
                    <div className="text-sm font-medium">Pasos del patrón</div>
                    {value.length === 0 && <div className="text-sm text-gray-500">No hay pasos todavía.</div>}
                    <ul className="space-y-1">
                        {value.map((s, i) => (
                        <li
                        key={i}
                        className={`rounded border px-2 py-1 ${i===sel ? "border-emerald-500 ring-1 ring-emerald-500" : ""}`}
                        >
                        <div className="flex items-center justify-between">
                            <button type="button" className="text-left flex-1" onClick={()=>setSel(i)}>
                            #{i + 1} · {Array.isArray(s.event) ? s.event[0] : s.event}
                            {s.start_x != null && s.start_y != null ? (
                                <span className="text-gray-600"> ({s.start_x},{s.start_y})</span>
                            ) : zoneLabelFromSpec(s.zone) ? (
                                <span className="text-gray-600"> · [{zoneLabelFromSpec(s.zone)}]</span>
                            ) : null}
                            </button>
                            <button type="button" className="text-red-600 text-sm" onClick={()=>removeStep(i)}>Quitar</button>
                        </div>
                        
                        {/* Badges de paso */}
                        <div className="mt-1 flex flex-wrap gap-1">
                            {s.team && <Flag>team: {s.team}</Flag>}
                            {s.success && <Flag>success</Flag>}
                            {s.goal && <Flag>goal</Flag>}
                            {s.switch_possession && <Flag>switch</Flag>}
                            {s.optional && <Flag>optional</Flag>}
                            {s.tolerance != null && <Flag>tol: {s.tolerance}</Flag>}
                            {(s.outcomes ?? []).map(o => <Flag key={o}>{o}</Flag>)} 
                        </div>
                        </li>
                        ))}
                    </ul>
                </div>

                {/* Ajustes del campo */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <label className="flex items-center gap-2 text-sm">
                        <input type="radio" name="mode" checked={mode==="coords"} onChange={()=>setMode("coords")} /> coords
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                        <input type="radio" name="mode" checked={mode==="zone"} onChange={()=>setMode("zone")} /> zona
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" checked={snapZones} onChange={(e)=>setSnapZones(e.target.checked)} /> snap zona
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" checked={showTol} onChange={(e)=>setShowTol(e.target.checked)} /> ver tolerancia
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" checked={flip} onChange={(e)=>setFlip(e.target.checked)} /> flip
                    </label>
                </div>

                <div className="text-xs text-gray-500">
                    Consejo: selecciona un paso y haz <b>click</b> en el campo para fijar su posición (modo coords).  
                    En modo zona, el click asigna la zona bajo el cursor. Botón derecho limpia las coords del paso seleccionado.
                    </div>
                </div>

                {/* Campo */}
                <div className="space-y-8 mt-3">
                    <Campo
                    steps={value}
                    selectedIndex={sel}
                    onSelect={setSel}
                    onChange={onChange}
                    mode={mode}
                    snapZones={snapZones}
                    showTolerance={showTol}
                    width={720}
                    flip={flip}
                    onHoverZone={setHoverZone}
                    />

                    {/* Aviso de hover */}
                    <div className="text-xs text-gray-600">
                    Zona bajo el cursor: {hoverZone ? zoneLabel(hoverZone) : '—'}
                    </div>
                </div>
                </div>
            );
        }