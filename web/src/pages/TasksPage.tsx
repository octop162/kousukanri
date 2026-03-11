import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type Task } from "../api";
import DateForm from "../components/DateForm";
import { today } from "../utils";

export default function TasksPage() {
  const [params, setParams] = useSearchParams();
  const date = params.get("date") || today();
  const simple = params.get("simple") === "1";
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    api
      .getTasks({ date, ...(simple ? { simple: "1" } : {}) })
      .then(setTasks)
      .catch((e: Error) => setError(e.message));
  }, [date, simple]);

  const toggleSimple = () => {
    setParams((prev) => {
      const next = new URLSearchParams(prev);
      if (simple) {
        next.delete("simple");
      } else {
        next.set("simple", "1");
      }
      return next;
    });
  };

  return (
    <div>
      <h1 className="text-xl font-bold mb-3">タスク一覧</h1>
      <DateForm />
      {error && <p className="text-error">{error}</p>}
      <label className="label cursor-pointer justify-start gap-1.5 text-sm mb-1">
        <input
          type="checkbox"
          checked={simple}
          onChange={toggleSimple}
          className="checkbox checkbox-sm"
        />
        <span>プロジェクトを非表示</span>
      </label>
      {tasks.length === 0 && !error && <p className="opacity-50">タスクなし</p>}
      <ul className="text-sm space-y-0.5">
        {tasks.map((t) => (
          <li key={t.id}>
            {t.start}–{t.end}　{t.name}
            {t.project && `　[${t.project}]`}
          </li>
        ))}
      </ul>
    </div>
  );
}
