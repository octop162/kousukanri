import { useState, useEffect } from "react";
import { api, type Project } from "../api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getProjects().then(setProjects).catch((e: Error) => setError(e.message));
  }, []);

  return (
    <div>
      <h1 className="text-xl font-bold mb-3">プロジェクト一覧</h1>
      {error && <p className="text-red-600">{error}</p>}
      {projects.length === 0 && !error && <p className="text-gray-500">プロジェクトなし</p>}
      <ul className="text-sm space-y-0.5">
        {projects.map((p) => (
          <li key={p.id} className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm shrink-0" style={{ backgroundColor: p.color }} />
            {p.name}
          </li>
        ))}
      </ul>
    </div>
  );
}
