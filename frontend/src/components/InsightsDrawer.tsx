import { useEffect, useState } from "react";
import { getPlayerInsights } from "../api";
import type { PlayerInsightsResponse } from "../types";

// Panel lateral simple, vale para validar rapidamente el drilldown

type Props = {
    open: boolean;
    onClose: () => void;
    role: string;
    playerId ?: number;
    queryId ?: string;
};

export default function InsightsDrawer({
    open,
    onClose,
    role,
    playerId,
    queryId,
}: Props) {
    // Me guardo respuesta, estado de carga y error/es
    const [data, setData] = useState<PlayerInsightsResponse | null> (null);
    const [cargando, setCargando] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Cada vez que se abre el panel o se cambian los parametros, se vuelven a pedir los datos
    useEffect(()=> {
        if (!open) return;
        setError(null);
        setCargando(true);
        getPlayerInsights({
            role,
            player_id: playerId,
            query_id: queryId,
            limit_examples: 5,
        }).then(setData).catch((e: unknown) => setError(e instanceof Error ? e.message : "Error desconocido")).finally(() => setCargando(false));
    }, [open, role, playerId, queryId]);
    

    return (
        <div className={`fixed inset-0 ${open ? "" : "pointer-events-none"}`}>
        {/* Fondo semitransparente */}
        <div
            className={`absolute inset-0 bg-black/30 transition-opacity ${
            open ? "opacity-100" : "opacity-0"
            }`}
            onClick={onClose}
        />
        {/* El propio panel */}
        <div
            className={`absolute right-0 top-0 h-full w-full sm:w-[480px] bg-white shadow-xl transition-transform ${
            open ? "translate-x-0" : "translate-x-full"
            }`}
        >
            <div className="p-4 border-b flex items-center justify-between">
          <div className="font-semibold">Player Insights</div>
          <button onClick={onClose} className="text-sm">
            Cerrar
          </button>
        </div>

        <div className="p-4 space-y-3 overflow-auto h-[calc(100%-56px)]">
          {cargando && <div>Cargando…</div>}
          {error && <div className="text-red-600 text-sm">{error}</div>}

          {data && (
            <>
              <div className="font-medium">{data.player ?? "—"}</div>

              {data.totals && (
                <pre className="text-xs bg-gray-50 p-3 rounded">
                  {JSON.stringify(data.totals, null, 2)}
                </pre>
              )}

              <div className="space-y-2">
                <div className="font-medium">Ejemplos</div>
                <ul className="text-sm space-y-2">
                  {data.examples?.map((ex, i) => (
                    <li key={i} className="border rounded p-2">
                      <div>
                        {ex.events.join(" → ")} | {ex.result}
                      </div>
                      <div className="text-xs">
                        {ex.preview && (
                          <a
                            className="underline mr-2"
                            href={ex.preview}
                            target="_blank"
                          >
                            Preview
                          </a>
                        )}
                        {ex.youtube_search && (
                          <a
                            className="underline"
                            href={ex.youtube_search}
                            target="_blank"
                          >
                            YouTube
                          </a>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
