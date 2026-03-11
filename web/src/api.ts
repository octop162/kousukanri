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

export interface ReportProject {
  name: string;
  seconds: number;
  formatted: string;
}

export interface Report {
  date: string;
  total_seconds: number;
  total_formatted: string;
  projects: ReportProject[];
}

export interface Reports {
  from: string;
  to: string;
  days: number;
  days_with_tasks: number;
  total_seconds: number;
  total_formatted: string;
  projects: ReportProject[];
}

export interface DayReport {
  date: string;
  total_seconds: number;
  total_formatted: string;
  projects: ReportProject[];
}

export interface ReportsByDay {
  from: string;
  to: string;
  days: number;
  days_with_tasks: number;
  total_seconds: number;
  total_formatted: string;
  daily: DayReport[];
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

  getReport: (params?: { date?: string }) =>
    get<Report>("/api/report", params as Record<string, string>),

  getReports: (params?: { from?: string; to?: string; since?: string }) =>
    get<Reports>("/api/reports", params as Record<string, string>),

  getReportsByDay: (params?: { from?: string; to?: string; since?: string }) =>
    get<ReportsByDay>("/api/reports-by-day", params as Record<string, string>),
};
