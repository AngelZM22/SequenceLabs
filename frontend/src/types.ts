export type TeamRule = "same" | "opponent" | "any";
export type EventDTO = Record<string, unknown>;

export type ZoneDict = {
  x_min: number;
  x_max: number;
  y_min: number;
  y_max: number;
};

export type Option = { id: number; label: string };

export type EventKey =
  | 'Recovery'
  | 'Ball Recovery'
  | 'Pass'
  | 'Shot'
  | 'Dribble'
  | 'Interception'
  | 'Duel'
  | 'Ball Receipt'
  | 'Carry'
  | 'Foul'
  | 'Goalkeeper';

export interface EventFilter {
    event: string | string[];
    outcomes?: string[];
    start_x?: number;
    start_y?: number;
    end_x?: number;
    end_y?: number;
    tolerance?: number;
    zone?: string | ZoneDict;
    optional?: boolean;
    team?: TeamRule;
    switch_possession?: boolean;
    success?: boolean;
    goal?: boolean;
    play_pattern?: string | string[];
    player_id?: number;
}

export interface RepeatOccurrence {
  match_id?: number;
  minute?: number | null;
  label?: string | null;
  shot_outcome?: string | null; 
  preview?: string | null;        // URL a /render/play?...
  youtube_search?: string | null; // URL a búsqueda de YouTube
           
}

export interface RepeatStats {
  shots: number;
  on_target: number;
  goals: number;
  pct_on_target: number;
  pct_goals: number;
}
export interface RepeatGroup {
  key: string; 
  label: string;                  // legible (ej. "Pass(Messi→Suárez) > Shot(Suárez, Goal)")
  tokens: string[];                    
  count: number;                  // nº de veces que aparece el patrón
  stats: RepeatStats;
  occurrences: RepeatOccurrence[];
}

export interface SearchRequest {
    pattern: EventFilter[];
    match_id?: number;
    team_id?: number; 
    competition_id?: number; 
    season_id?: number;
    player_id?: number;
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
        repeats?: RepeatGroup[];
          
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