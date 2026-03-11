import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type ReportDaily } from "../api";
import ReportList from "../components/ReportList";
import DateRangeForm from "../components/DateRangeForm";
import { today, thirtyDaysAgo, fmtTime } from "../utils";

export default function ReportDailyPage() {
  const [params] = useSearchParams();
  const from = params.get("from") || thirtyDaysAgo();
  const to = params.get("to") || today();
  const [data, setData] = useState<ReportDaily | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    api
      .getReportDaily({ from, to })
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, [from, to]);

  return (
    <div>
      <h1 className="text-xl font-bold mb-3">日別レポート</h1>
      <DateRangeForm />
      {error && <p className="text-error">{error}</p>}
      {data && (
        <div className="space-y-5">
          {data.daily.map((day) => (
            <section key={day.date}>
              <div className="flex items-baseline gap-2 mb-1.5 border-b border-base-300 pb-1">
                <p className="font-semibold">{day.date}</p>
                <span className="text-sm opacity-60">{fmtTime(day.total_seconds)}</span>
              </div>
              <ReportList items={day.projects} grandTotal={day.total_seconds} />
            </section>
          ))}
          <p className="font-bold text-base border-t-2 border-base-300 pt-2">
            総合計　{fmtTime(data.total_seconds)}
          </p>
        </div>
      )}
    </div>
  );
}
