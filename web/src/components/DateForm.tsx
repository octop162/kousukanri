import { useSearchParams } from "react-router-dom";
import { today } from "../utils";

function shiftDate(dateStr: string, days: number): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const dt = new Date(y, m - 1, d + days);
  const yy = dt.getFullYear();
  const mm = String(dt.getMonth() + 1).padStart(2, "0");
  const dd = String(dt.getDate()).padStart(2, "0");
  return `${yy}-${mm}-${dd}`;
}

export default function DateForm() {
  const [params, setParams] = useSearchParams();
  const date = params.get("date") || today();

  function changeDate(d: string) {
    const next = new URLSearchParams(params);
    next.set("date", d);
    setParams(next);
  }

  return (
    <div className="flex flex-wrap gap-2 items-center mb-4">
      <button onClick={() => changeDate(shiftDate(date, -1))} className="btn btn-sm btn-ghost">◀</button>
      <input
        type="date"
        value={date}
        onChange={(e) => changeDate(e.target.value)}
        className="input input-sm input-bordered"
      />
      <button onClick={() => changeDate(shiftDate(date, 1))} className="btn btn-sm btn-ghost">▶</button>
    </div>
  );
}
