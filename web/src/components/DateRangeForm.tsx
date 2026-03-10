import { useSearchParams } from "react-router-dom";
import { today, thirtyDaysAgo } from "../utils";

export default function DateRangeForm() {
  const [params, setParams] = useSearchParams();

  const from = params.get("from") || thirtyDaysAgo();
  const to = params.get("to") || today();
  const detail = params.get("detail") === "1";

  function apply(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const next = new URLSearchParams();
    const f = fd.get("from") as string;
    const t = fd.get("to") as string;
    if (f) next.set("from", f);
    if (t) next.set("to", t);
    if (fd.get("detail")) next.set("detail", "1");
    setParams(next);
  }

  return (
    <form onSubmit={apply} className="flex flex-wrap gap-3 items-center mb-4 text-sm">
      <input type="date" name="from" defaultValue={from} className="border rounded px-2 py-1" />
      <span>～</span>
      <input type="date" name="to" defaultValue={to} className="border rounded px-2 py-1" />
      <label className="flex items-center gap-1">
        <input type="checkbox" name="detail" defaultChecked={detail} />
        内訳
      </label>
      <button type="submit" className="bg-gray-700 text-white px-3 py-1 rounded hover:bg-gray-600">
        表示
      </button>
    </form>
  );
}
