/** Format seconds into "H時間M分" */
export function fmtTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0 && m > 0) return `${h}時間${m}分`;
  if (h > 0) return `${h}時間`;
  return `${m}分`;
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
