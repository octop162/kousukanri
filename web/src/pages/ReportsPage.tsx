import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type Reports } from "../api";
import ReportList from "../components/ReportList";
import DateRangeForm from "../components/DateRangeForm";
import { today, thirtyDaysAgo } from "../utils";

export default function ReportsPage() {
  const [params] = useSearchParams();
  const from = params.get("from") || thirtyDaysAgo();
  const to = params.get("to") || today();
  const [reports, setReports] = useState<Reports | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    api
      .getReports({ from, to })
      .then(setReports)
      .catch((e: Error) => setError(e.message));
  }, [from, to]);

  return (
    <div>
      <h1 className="text-xl font-bold mb-3">期間集計</h1>
      <DateRangeForm />
      {error && <p className="text-error">{error}</p>}
      {reports && (
        <>
          <p className="text-sm opacity-60 mb-2">
            {reports.from} ～ {reports.to}（{reports.days_with_tasks} 日間）
          </p>
          <ReportList projects={reports.projects} grandTotal={reports.total_seconds} />
        </>
      )}
    </div>
  );
}
