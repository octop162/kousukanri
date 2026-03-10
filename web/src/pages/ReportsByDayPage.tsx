import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type ReportsByDay } from "../api";
import ReportList from "../components/ReportList";
import DateRangeForm from "../components/DateRangeForm";
import { today, thirtyDaysAgo, fmtTime } from "../utils";

export default function ReportsByDayPage() {
  const [params] = useSearchParams();
  const from = params.get("from") || thirtyDaysAgo();
  const to = params.get("to") || today();
  const detail = params.get("detail") === "1";
  const [data, setData] = useState<ReportsByDay | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    api
      .getReportsByDay({ from, to, detail: detail ? "1" : undefined })
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, [from, to, detail]);

  return (
    <div>
      <h1 className="text-xl font-bold mb-3">日別レポート</h1>
      <DateRangeForm />
      {error && <p className="text-red-600">{error}</p>}
      {data && (
        <div className="space-y-4">
          {data.daily.map((day) => (
            <section key={day.date}>
              <p className="font-semibold mb-1">{day.date}（{fmtTime(day.total_seconds)}）</p>
              <ReportList projects={day.projects} grandTotal={day.total_seconds} />
            </section>
          ))}
          <p className="font-bold">総合計　{fmtTime(data.total_seconds)}</p>
        </div>
      )}
    </div>
  );
}
