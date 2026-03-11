import { useState, useEffect } from "react";
import { api, type Project } from "../api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getProjects().then(setProjects).catch((e: Error) => setError(e.message));
  }, []);

  const activeProjects = projects.filter((p) => !p.archived);
  const archivedProjects = projects.filter((p) => p.archived);

  const handleArchive = async (id: number) => {
    try {
      await api.archiveProject(id, true);
      setProjects((prev) =>
        prev.map((p) => (p.id === id ? { ...p, archived: true } : p))
      );
    } catch (e: unknown) {
      setError((e as Error).message);
    }
  };

  const handleRestore = async (id: number) => {
    try {
      await api.archiveProject(id, false);
      setProjects((prev) =>
        prev.map((p) => (p.id === id ? { ...p, archived: false } : p))
      );
    } catch (e: unknown) {
      setError((e as Error).message);
    }
  };

  return (
    <div>
      <h1 className="text-xl font-bold mb-3">プロジェクト一覧</h1>
      {error && <p className="text-error">{error}</p>}

      {activeProjects.length === 0 && !error && <p className="opacity-50">プロジェクトなし</p>}
      <ul className="text-sm space-y-0.5">
        {activeProjects.map((p) => (
          <li key={p.id} className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm shrink-0" style={{ backgroundColor: p.color }} />
            <span className="flex-1">{p.name}</span>
            <button
              className="text-xs opacity-40 hover:opacity-100 transition-opacity"
              onClick={() => handleArchive(p.id)}
              title="アーカイブ"
            >
              📦
            </button>
          </li>
        ))}
      </ul>

      {archivedProjects.length > 0 && (
        <>
          <h2 className="text-lg font-bold mt-6 mb-2 opacity-60">アーカイブ</h2>
          <ul className="text-sm space-y-0.5 opacity-60">
            {archivedProjects.map((p) => (
              <li key={p.id} className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-sm shrink-0" style={{ backgroundColor: p.color }} />
                <span className="flex-1">{p.name}</span>
                <button
                  className="text-xs opacity-60 hover:opacity-100 transition-opacity"
                  onClick={() => handleRestore(p.id)}
                  title="元に戻す"
                >
                  ↩
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
