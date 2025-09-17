// src/eventIcons.ts
export type EventIcon = { url: string; size?: number; dx?: number; dy?: number };

export const EVENT_ICONS: Record<string, EventIcon> = {
  Recovery:        { url: "/icons/events/Recovery.png",     size: 22 },
  "Ball Recovery": { url: "/icons/events/Recovery.png",     size: 22 },
  Pass:            { url: "/icons/events/pase.png",         size: 22 },
  Shot:            { url: "/icons/events/disparo.png",         size: 22 },
  Dribble:         { url: "/icons/events/dribble.png",      size: 22 },
  Interception:    { url: "/icons/events/Recovery.png", size: 22 },
  Duel:            { url: "/icons/events/Recovery.png",         size: 22 },
  "Ball Receipt":  { url: "/icons/events/receipt.png",      size: 22 },
  Carry:           { url: "/icons/events/carrera.png",        size: 22 },
  Foul:            { url: "/icons/events/falta.png",         size: 22 },
  // cohíbe diferencias de escritura:
  "Goal Keeper":   { url: "/icons/events/GoalKeeper.png",   size: 22 },
  Goalkeeper:      { url: "/icons/events/GoalKeeper.png",   size: 22 },
};