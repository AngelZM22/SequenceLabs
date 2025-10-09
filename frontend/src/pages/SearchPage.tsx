import { useEffect, useState, type FormEvent } from "react";
import { apiStatus, buscar } from "../api";
import type { EventFilter, SearchRequest, SearchResponse } from "../types";

//import PatternBuilder from "../components/PatternBuilder";
import InsightsDrawer from "../components/InsightsDrawer";
import PlayDesigner from "../components/PlayDesigner";

import BarraFiltros from "../components/BarraFiltros";
// Como any da problemas
type RankItem = { player_id: number; player_name: string; count?: number; score?: number; drilldown?: string };
type Ranking = Record<string, RankItem[]>;
type EventDTO = { type_name?: string; [k: string]: unknown };

export default function SearchPage(){

    //Estados que quiero guardar

    const [statusOk, setStatusOk] = useState<boolean | null> (null);

    //Patron
    const [pattern, setPattern] = useState<EventFilter[]>([{event: "Recovery"}]);

    //Parametros de busqueda
    const [margen, setMargen] = useState<number>(25);
    const [tol, setTol] = useState<number>(10);

    const [loading, setLoading] = useState(false);
    const [res, setRes] = useState<SearchResponse | null> (null);
    const [err, setErr] = useState<string | null> (null);

    //Metricas de playerInsights
    const [drawerOpen, setDrawerOpen] = useState(false);
    const [drawerRole, setDrawerRole] = useState<string>("tiradores");
    const [drawerPlayerId, setDrawerPlayerId]= useState<number | undefined> (undefined);  
    
    //Filtros
    const [filters, setFilters] = useState<{competition_id?:number; season_id?:number; team_id?:number; player_id?:number}>({});


    useEffect(() => {
        apiStatus().then(s => setStatusOk(!!s.ok)).catch(()=> setStatusOk(false));
    }, []);

    //Envio de la búsqueda
    async function submit(e?: FormEvent) {
        e?.preventDefault();
        setErr(null);
        setLoading(true);

        try{
            const body: SearchRequest ={ pattern, 
                margen_tiempo: margen, 
                tolerancia: tol, 
                competition_id:filters.competition_id,
                season_id: filters.season_id,
                team_id: filters.team_id,
                player_id: filters.player_id,
            };
            const data= await buscar(body);
            setRes(data);

            localStorage.setItem("last_query_id", data.query_id ?? "");
            localStorage.setItem("last_request", JSON.stringify(body));

        }catch(ex){
            const msg = ex instanceof Error ? ex.message : "Error";
            setErr(msg);
            setRes(null);
        }finally {
            setLoading(false);
        }
    }

     function openInsights(role: string, player_id?: number) {
        setDrawerRole(role);
        setDrawerPlayerId(player_id);
        setDrawerOpen(true);
  }
    const query_Id = res?.query_id || localStorage.getItem("last_query_id") || undefined;

    //function presetRecovery() {setPattern([{event: "Recovery"}]); setMargen(25); setTol(10);}
    //function presetPassShot() { setPattern([{ event: "Pass" }, { event: "Shot" }]); setMargen(25); setTol(10); }
    //function presetDribbleComplete() { setPattern([{ event: "Dribble", outcomes: ["Complete"] }]); setMargen(0); setTol(0); }

    // Convierto el ranking a un tipo seguro para el .map de TS
    const ranking: Ranking = (res?.ranking ?? {}) as Ranking;
    // Ejemplos como "array de arrays" con al menos type_name
    const examples: EventDTO[][] = (res?.examples ?? []) as unknown as EventDTO[][];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-xl font-semibold">Búsqueda de patrones</h1>
                <span className={`text-sm ${statusOk ? "text-emerald-600" : "text-red-600"}`}>
                API: {statusOk === null ? "…" : statusOk ? "OK" : "OFF"}
                </span>
            </div>

            {/* NUEVO: barra de filtros en cascada */}
            <BarraFiltros value={filters} onChange={setFilters} />

            {/* Tu diseñador en campo se queda como está */}
            <PlayDesigner value={pattern} onChange={setPattern} /> {/* :contentReference[oaicite:3]{index=3} */}

            {/* Botón de búsqueda y parámetros globales (si los quieres mantener) */}
            <form onSubmit={submit} className="bg-white p-4 rounded-xl shadow space-y-4">
                <div className="grid sm:grid-cols-3 gap-3">
                <label className="text-sm">
                    margen_tiempo (s)
                    <input type="number" className="mt-1 w-full border rounded px-2 py-2"
                        value={margen} onChange={(e)=>setMargen(Number(e.target.value)||0)} />
                </label>
                <label className="text-sm">
                    tolerancia
                    <input type="number" className="mt-1 w-full border rounded px-2 py-2"
                        value={tol} onChange={(e)=>setTol(Number(e.target.value)||0)} />
                </label>
                </div>

                <button type="submit" disabled={loading} className="px-4 py-2 rounded bg-black text-white">
                {loading ? "Buscando..." : "Buscar"}
                </button>

                {err && <div className="text-red-600">{err}</div>}
            </form>

            {/* Resumen */}
            {res?.summary && (
                <section className="bg-white p-4 rounded-xl shadow">
                <h2 className="font-medium mb-2">Resumen</h2>
                <ul className="text-sm grid sm:grid-cols-2 gap-2">
                    <li>Total secuencias: {res.summary.total}</li>
                    <li>Δt medio: {res.summary.avg_time_between_events_sec}s</li>
                    <li>Equipos: {res.summary.teams_covered}</li>
                    <li>Partidos: {res.summary.matches_covered}</li>
                </ul>
                </section>
            )}

            {/* Ranking */}
            {Object.keys(ranking).length > 0 && (
                <section className="bg-white p-4 rounded-xl shadow">
                <h2 className="font-medium mb-3">Ranking (clic para ver insights)</h2>
                <div className="grid md:grid-cols-3 gap-4">
                    {Object.entries(ranking).map(([role, items]) => (
                    <div key={role} className="border rounded-lg p-3">
                        <div className="font-semibold mb-2 capitalize">{role.replace("_", " ")}</div>
                        <ul className="text-sm space-y-1">
                        {items.map((it, i) => (
                            <li key={`${it.player_id}-${i}`} className="flex justify-between">
                            <button
                                className="text-left hover:underline"
                                onClick={() => openInsights(role, it.player_id)}
                            >
                                {it.player_name}
                            </button>
                            <span className="text-gray-500">{it.count ?? it.score ?? ""}</span>
                            </li>
                        ))}
                        </ul>
                    </div>
                    ))}
                </div>
                </section>
            )}
            {/* Ejemplos */}
            {examples.length > 0 && (
                <section className="bg-white p-4 rounded-xl shadow">
                <h2 className="font-medium mb-2">Ejemplos</h2>
                <ol className="list-decimal pl-6 space-y-2 text-sm">
                    {examples.slice(0, 25).map((jugada, idx) => (
                    <li key={idx}>{jugada.map((e) => e.type_name ?? "—").join(" → ")}</li>
                    ))}
                </ol>
                </section>
            )}

            <InsightsDrawer
                open={drawerOpen}
                onClose={() => setDrawerOpen(false)}
                role={drawerRole}
                playerId={drawerPlayerId}
                queryId={query_Id}
            />
        </div>
    );
}

