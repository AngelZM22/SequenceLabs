//Fallback minimo
// Fallback mínimo (nombres habituales en StatsBomb)
export const OUTCOMES_FALLBACK: Record<string, string[]> = {
  Pass: ["Incomplete", "Out", "Pass Offside", "Injury Clearance"],
  Shot: ["Goal", "Saved", "Blocked", "Off T", "Saved to Post", "Savedo Off Target", "Wayward"],
  Dribble: ["Complete", "Incomplete"],
  Duel: ["Won", "Lost In Play", "Lost Out", "Success in Play", "Success Out"],
  Interception: ["Won", "Lost In Play", "Lost Out", "Success in Play", "Success Out"],       
  Foul: [],   // o ["Conceded","Won"] según tu carga
  "Ball Recovery": [],          // normalmente sin outcome
  "Ball Receipt": ["Incomplete"], // si lo tienes tipado así
  Carry: [],                    // sin outcome
};
