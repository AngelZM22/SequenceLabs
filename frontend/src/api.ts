import axios from "axios";
import type { SearchRequest, SearchResponse, PlayerInsightsResponse } from "./types";
import type { Option } from "./types";

const API = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export const api = axios.create(
    {
        baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
        headers: { "Content-Type": "application/json"},
    }
);

export async function apiStatus() {

    const r = await api.get("/status");
    return r.data as { ok : boolean};

}

export async function buscar(req: SearchRequest) {

    const r = await api.post<SearchResponse>("/buscar", req);
    return r.data
    
}

export async function getPlayerInsights(params: {
    role: string;
    player_id?: number;
    query_id?: string;
    limit_examples?: number;
}) {
    const r = await api.get<PlayerInsightsResponse>("/player-insights", {params});
    return r.data
}

export async function getOutcomes(event: string): Promise<string[]> {
  const r = await api.get <{ event: string; outcomes: string[] } > ("/outcomes", {
    params: {event},
  });
  return r.data?.outcomes ?? [];
}

export async function getCompetitions(): Promise<Option[]> {
  const r = await fetch(`${API}/options/competitions`);
  return r.json();
}
export async function getSeasons(competition_id?: number): Promise<Option[]> {
  const q = new URLSearchParams();
  if (competition_id != null) q.set("competition_id", String(competition_id));
  const r = await fetch(`${API}/options/seasons${q.toString() ? `?${q}` : ""}`)
  return r.json();
}
export async function getTeams(competition_id?: number, season_id?: number): Promise<Option[]> {
  const q = new URLSearchParams();
  if (competition_id != null) q.set("competition_id", String(competition_id));
  if (season_id != null) q.set("season_id", String(season_id));
  const r = await fetch(`${API}/options/teams${q.toString() ? `?${q}` : ""}`);
  return r.json();
}
export async function getPlayers(team_id?: number, season_id?: number): Promise<Option[]> {
  const q = new URLSearchParams();
  if (team_id != null) q.set("team_id", String(team_id));
  if (season_id != null) q.set("season_id", String(season_id));
  const r = await fetch(`${API}/options/players${q.toString() ? `?${q}` : ""}`);
  return r.json();
}