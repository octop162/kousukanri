/** Format seconds into "HH:MM" */
export function fmtTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

/** Today's date in YYYY-MM-DD */
export function today(): string {
  return new Date().toISOString().slice(0, 10);
}

/** 30 days ago in YYYY-MM-DD */
export function thirtyDaysAgo(): string {
  const d = new Date();
  d.setDate(d.getDate() - 29);
  return d.toISOString().slice(0, 10);
}
