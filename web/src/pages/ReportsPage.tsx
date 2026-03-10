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
  const detail = params.get("detail") === "1";
  const [reports, setReports] = useState<Reports | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    api
      .getReports({ from, to, detail: detail ? "1" : undefined })
      .then(setReports)
      .catch((e: Error) => setError(e.message));
  }, [from, to, detail]);

  return (
    <div>
      <h1 className="text-xl font-bold mb-3">期間集計</h1>
      <DateRangeForm />
      {error && <p className="text-red-600">{error}</p>}
      {reports && (
        <>
          <p className="text-sm text-gray-600 mb-2">
            {reports.from} ～ {reports.to}（{reports.days_with_tasks} 日間）
          </p>
          <ReportList projects={reports.projects} grandTotal={reports.total_seconds} />
        </>
      )}
    </div>
  );
}
