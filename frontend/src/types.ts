export type TeamRule = "same" | "opponent" | "any";
export type EventDTO = Record<string, unknown>;
export interface EventFilter {
    event: string | string[];
    outcomes?: string[];
    start_x?: number;
    start_y?: number;
    tolerance?: number;
    zone?: string | Record<string,number>;
    optional?: boolean;
    team?: TeamRule;
    switch_possession?: boolean;
    success?: boolean;
    goal?: boolean;
    play_pattern?: string | string[];

}

export interface SearchRequest {
    pattern: EventFilter[];
    match_id?: number;
    team_id?: number; 
    competition?: string; 
    tolerancia?: number; 
    margen_tiempo?: number; 
}

export interface SearchResponse {
    
    summary?:{
        total: number;
        avg_time_between_events_sec: number;
        teams_covered: number;
        matches_covered: number;
    }
    ranking: 
        Record< string, {
            player_id: number;
            player_name: string;
            count?: number;
            score?: number;
            drilldown?: number
        
        }[]
        >;
        examples?: EventDTO[][];
        query_id?: string;
          
}

export interface PlayerInsightsResponse {
    role: string;
    player_id?: number;
    player?: string;
    totals?: Record<string, number>;
    context?: EventDTO;
    examples: {
        match_id?: number;
        minute?: number;
        events: string[];
        result: string;
        preview?: string | null;
        youtube_search?: string | null;
    } [] ;

}