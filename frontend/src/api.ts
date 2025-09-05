import axios from "axios";
import type { SearchRequest, SearchResponse, PlayerInsightsResponse } from "./types";

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