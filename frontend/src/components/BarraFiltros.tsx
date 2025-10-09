import { useEffect, useState } from "react";
import type { Option } from "../types";
import { getCompetitions, getSeasons, getTeams, getPlayers } from "../api";

type Filtros = {
  competition_id?: number;
  season_id?: number;
  team_id?: number;
  player_id?: number;
};

function ensureValid<T extends number | undefined>(current: T, options: Option[]): T {
  if (current == null) return current;
  return options.some(o => o.id === current) ? current : undefined as T;
}

export default function BarraFiltros({
  value, onChange, className = "",
}: { value: Filtros; onChange: (f: Filtros) => void, className?: string}) {
  
    const { competition_id, season_id, team_id, player_id } = value;
    const [competitions, setCompetitions] = useState<Option[]>([]);
    const [seasons, setSeasons] = useState<Option[]>([]);
    const [teams, setTeams] = useState<Option[]>([]);
    const [players, setPlayers] = useState<Option[]>([]);

    const set = (patch: Partial<Filtros>) => onChange({ ...value, ...patch });


// Cargas iniciales: globales
    useEffect(() => {
    getCompetitions().then(setCompetitions);
    getSeasons().then(opts => {
      setSeasons(opts);
      // Validar selección actual
      const fixed = ensureValid(season_id, opts);
      if (fixed !== season_id) set({ season_id: fixed, team_id: undefined, player_id: undefined });
    });
    getTeams().then(opts => {
      setTeams(opts);
      const fixed = ensureValid(team_id, opts);
      if (fixed !== team_id) set({ team_id: fixed, player_id: undefined });
    });
    getPlayers().then(opts => {
      setPlayers(opts);
      const fixed = ensureValid(player_id, opts);
      if (fixed !== player_id) set({ player_id: fixed });
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

    // Cambia competition → seasons (por comp) y teams (por comp si quieres acotar), players según team/season
  useEffect(() => {
    getSeasons(competition_id).then(opts => {
      setSeasons(opts);
      const fixedSeason = ensureValid(season_id, opts);
      const seasonChanged = fixedSeason !== season_id;
      if (seasonChanged) set({ season_id: fixedSeason, team_id: undefined, player_id: undefined });
    });

    // Teams: si hay comp pero no season, acota por comp; si no, global
    const teamsFetcher = competition_id ? getTeams(competition_id) : getTeams();
    teamsFetcher.then(opts => {
      setTeams(opts);
      const fixedTeam = ensureValid(team_id, opts);
      if (fixedTeam !== team_id) set({ team_id: fixedTeam, player_id: undefined });
    });

    // Players: si hay team, ya se refrescarán en el efecto de team; si no, conservar global/season
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [competition_id]);

  // Cambia season → teams (por comp+season o por season), players (si no hay team)
  useEffect(() => {
    const teamsFetcher = season_id
      ? (competition_id ? getTeams(competition_id, season_id) : getTeams(undefined, season_id))
      : (competition_id ? getTeams(competition_id) : getTeams());

    teamsFetcher.then(opts => {
      setTeams(opts);
      const fixedTeam = ensureValid(team_id, opts);
      if (fixedTeam !== team_id) set({ team_id: fixedTeam, player_id: undefined });
    });

    if (!team_id) {
      const playersFetcher = season_id ? getPlayers(undefined, season_id) : getPlayers();
      playersFetcher.then(opts => {
        setPlayers(opts);
        const fixedPlayer = ensureValid(player_id, opts);
        if (fixedPlayer !== player_id) set({ player_id: fixedPlayer });
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [season_id]);

  // Cambia team → players (por team + season si está)
  useEffect(() => {
    const playersFetcher = team_id ? getPlayers(team_id, season_id) : (season_id ? getPlayers(undefined, season_id) : getPlayers());
    playersFetcher.then(opts => {
      setPlayers(opts);
      const fixedPlayer = ensureValid(player_id, opts);
      if (fixedPlayer !== player_id) set({ player_id: fixedPlayer });
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [team_id]);


  return (
    <div className={`grid grid-cols-1 md:grid-cols-4 gap-3 ${className}`}>
      {/* Competition */}
      <select
        className="border rounded px-3 py-2"
        value={competition_id ?? ""}
        onChange={(e) => set({ competition_id: e.target.value ? Number(e.target.value) : undefined })}
      >
        <option value="">Competition (any)</option>
        {competitions.map(o => <option key={o.id} value={o.id}>{o.label}</option>)}
      </select>

      {/* Season (independiente, pero se acota si hay competition) */}
      <select
        className="border rounded px-3 py-2"
        value={season_id ?? ""}
        onChange={(e) => set({ season_id: e.target.value ? Number(e.target.value) : undefined })}
      >
        <option value="">Season (any)</option>
        {seasons.map(o => <option key={o.id} value={o.id}>{o.label}</option>)}
      </select>

      {/* Team (independiente; se acota por comp/season si existen) */}
      <select
        className="border rounded px-3 py-2"
        value={team_id ?? ""}
        onChange={(e) => set({ team_id: e.target.value ? Number(e.target.value) : undefined })}
      >
        <option value="">Team (any)</option>
        {teams.map(o => <option key={o.id} value={o.id}>{o.label}</option>)}
      </select>

      {/* Player (independiente; se acota por team y/o season si existen) */}
      <select
        className="border rounded px-3 py-2"
        value={player_id ?? ""}
        onChange={(e) => set({ player_id: e.target.value ? Number(e.target.value) : undefined })}
      >
        <option value="">Player (any)</option>
        {players.map(o => <option key={o.id} value={o.id}>{o.label}</option>)}
      </select>
    </div>
  );
}
  