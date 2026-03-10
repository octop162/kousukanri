import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type Task } from "../api";
import DateForm from "../components/DateForm";
import { today } from "../utils";

export default function TasksPage() {
  const [params] = useSearchParams();
  const date = params.get("date") || today();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    api.getTasks({ date }).then(setTasks).catch((e: Error) => setError(e.message));
  }, [date]);

  return (
    <div>
      <h1 className="text-xl font-bold mb-3">タスク一覧</h1>
      <DateForm />
      {error && <p className="text-red-600">{error}</p>}
      {tasks.length === 0 && !error && <p className="text-gray-500">タスクなし</p>}
      <ul className="text-sm space-y-0.5">
        {tasks.map((t) => (
          <li key={t.id}>
            {t.start}–{t.end}　{t.name}{t.project && `　[${t.project}]`}
          </li>
        ))}
      </ul>
    </div>
  );
}
