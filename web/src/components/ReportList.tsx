import type { ReportProject } from "../api";
import { fmtTime } from "../utils";

interface Props {
  projects: ReportProject[];
  grandTotal: number;
}

export default function ReportList({ projects, grandTotal }: Props) {
  return (
    <div className="text-sm">
      <ul className="space-y-0.5">
        {projects.map((proj) => (
          <li key={proj.name}>
            {proj.name}　{fmtTime(proj.seconds)}
            {proj.tasks && proj.tasks.length > 0 && (
              <ul className="ml-4 space-y-0.5 text-gray-600">
                {proj.tasks.map((t) => (
                  <li key={t.name}>{t.name}　{fmtTime(t.seconds)}</li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
      <p className="mt-2">合計　{fmtTime(grandTotal)}</p>
    </div>
  );
}
