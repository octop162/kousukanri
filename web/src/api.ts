export interface Task {
  id: number;
  name: string;
  start: string;
  end: string;
  date: string;
  color: string;
  project_id?: number | null;
  project?: string | null;
}

export interface Project {
  id: number;
  name: string;
  color: string;
  order: number;
  archived: boolean;
}

export interface ReportEntry {
  name: string;
  seconds: number;
  formatted: string;
}

export interface DayReport {
  date: string;
  total_seconds: number;
  total_formatted: string;
  projects: ReportEntry[];
}

export interface ReportDaily {
  from: string;
  to: string;
  days: number;
  days_with_tasks: number;
  total_seconds: number;
  total_formatted: string;
  daily: DayReport[];
}

export interface ReportTasks {
  from: string;
  to: string;
  days: number;
  days_with_tasks: number;
  total_seconds: number;
  total_formatted: string;
  tasks: ReportEntry[];
}

const BASE = "";

async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(BASE + path, location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => v && url.searchParams.set(k, v));
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

async function patch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(BASE + path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const api = {
  getTasks: (params?: { date?: string; simple?: string }) =>
    get<Task[]>("/api/tasks", params as Record<string, string>),

  postTask: (body: { name: string; start: string; end: string; date?: string; project?: string }) =>
    post<Task>("/api/tasks", body),

  getProjects: () => get<Project[]>("/api/projects"),

  postProject: (body: { name: string; color?: string }) =>
    post<Project>("/api/projects", body),

  archiveProject: (id: number, archived: boolean) =>
    patch<{ id: number; archived: boolean }>(`/api/projects/${id}/archive`, { archived }),

  getReportDaily: (params?: { from?: string; to?: string; since?: string }) =>
    get<ReportDaily>("/api/report/daily", params as Record<string, string>),

  getReportTasks: (params?: { from?: string; to?: string; since?: string }) =>
    get<ReportTasks>("/api/report/tasks", params as Record<string, string>),
};
