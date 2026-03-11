import { useSearchParams } from "react-router-dom";
import { today, thirtyDaysAgo } from "../utils";

export default function DateRangeForm() {
  const [params, setParams] = useSearchParams();

  const from = params.get("from") || thirtyDaysAgo();
  const to = params.get("to") || today();

  function apply(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const next = new URLSearchParams();
    const f = fd.get("from") as string;
    const t = fd.get("to") as string;
    if (f) next.set("from", f);
    if (t) next.set("to", t);
    setParams(next);
  }

  return (
    <form onSubmit={apply} className="flex flex-wrap gap-2 items-center mb-4">
      <input type="date" name="from" defaultValue={from} className="input input-sm input-bordered" />
      <span>～</span>
      <input type="date" name="to" defaultValue={to} className="input input-sm input-bordered" />
      <button type="submit" className="btn btn-sm btn-neutral">表示</button>
    </form>
  );
}
