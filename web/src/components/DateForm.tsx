import { useSearchParams } from "react-router-dom";
import { today } from "../utils";

interface Props {
  showDetail?: boolean;
}

function shiftDate(dateStr: string, days: number): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const dt = new Date(y, m - 1, d + days);
  const yy = dt.getFullYear();
  const mm = String(dt.getMonth() + 1).padStart(2, "0");
  const dd = String(dt.getDate()).padStart(2, "0");
  return `${yy}-${mm}-${dd}`;
}

export default function DateForm({ showDetail }: Props) {
  const [params, setParams] = useSearchParams();
  const date = params.get("date") || today();
  const detail = params.get("detail") === "1";

  function changeDate(d: string) {
    const next = new URLSearchParams(params);
    next.set("date", d);
    setParams(next);
  }

  function toggleDetail() {
    const next = new URLSearchParams(params);
    if (detail) next.delete("detail");
    else next.set("detail", "1");
    setParams(next);
  }

  return (
    <div className="flex flex-wrap gap-3 items-center mb-4">
      <button onClick={() => changeDate(shiftDate(date, -1))} className="px-2 py-1 border rounded hover:opacity-80">◀</button>
      <input
        type="date"
        value={date}
        onChange={(e) => changeDate(e.target.value)}
        className="border rounded px-2 py-1"
      />
      <button onClick={() => changeDate(shiftDate(date, 1))} className="px-2 py-1 border rounded hover:opacity-80">▶</button>
      {showDetail && (
        <label className="flex items-center gap-1">
          <input type="checkbox" checked={detail} onChange={toggleDetail} />
          内訳
        </label>
      )}
    </div>
  );
}
