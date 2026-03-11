import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type Report } from "../api";
import ReportList from "../components/ReportList";
import DateForm from "../components/DateForm";
import { today } from "../utils";

export default function ReportPage() {
  const [params] = useSearchParams();
  const date = params.get("date") || today();
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    api
      .getReport({ date })
      .then(setReport)
      .catch((e: Error) => setError(e.message));
  }, [date]);

  return (
    <div>
      <h1 className="text-xl font-bold mb-3">日次レポート</h1>
      <DateForm />
      {error && <p className="text-error">{error}</p>}
      {report && (
        <ReportList projects={report.projects} grandTotal={report.total_seconds} />
      )}
    </div>
  );
}
