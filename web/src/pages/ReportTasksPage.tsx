import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type ReportTasks } from "../api";
import ReportList from "../components/ReportList";
import DateRangeForm from "../components/DateRangeForm";
import { today, thirtyDaysAgo } from "../utils";

export default function ReportTasksPage() {
  const [params] = useSearchParams();
  const from = params.get("from") || thirtyDaysAgo();
  const to = params.get("to") || today();
  const [data, setData] = useState<ReportTasks | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    api
      .getReportTasks({ from, to })
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, [from, to]);

  return (
    <div>
      <h1 className="text-xl font-bold mb-3">タスク別レポート</h1>
      <DateRangeForm />
      {error && <p className="text-error">{error}</p>}
      {data && (
        <>
          <p className="text-sm opacity-60 mb-2">
            {data.from} ～ {data.to}（{data.days_with_tasks} 日間）
          </p>
          <ReportList items={data.tasks} grandTotal={data.total_seconds} />
        </>
      )}
    </div>
  );
}
