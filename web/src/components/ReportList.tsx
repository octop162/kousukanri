import type { ReportProject } from "../api";
import { fmtTime } from "../utils";

interface Props {
  projects: ReportProject[];
  grandTotal: number;
}

export default function ReportList({ projects, grandTotal }: Props) {
  return (
    <div className="text-sm">
      <table className="border-collapse">
        <tbody>
          {projects.map((proj) => (
            <tr key={proj.name}>
              <td className="py-0.5 pr-2 align-top whitespace-nowrap">
                {proj.name}
              </td>
              <td className="py-0.5 align-top whitespace-nowrap text-right tabular-nums">
                {fmtTime(proj.seconds)}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="border-t border-base-300 font-semibold">
            <td className="pt-1.5">合計</td>
            <td className="pt-1.5 text-right tabular-nums">{fmtTime(grandTotal)}</td>
          </tr>
        </tfoot>
      </table>

      {projects.some((p) => p.tasks && p.tasks.length > 0) && (
        <div className="mt-3 space-y-2">
          {projects
            .filter((p) => p.tasks && p.tasks.length > 0)
            .map((proj) => (
              <div key={proj.name}>
                <p className="font-medium text-xs opacity-60 mb-0.5">{proj.name}</p>
                <table className="border-collapse ml-3">
                  <tbody>
                    {proj.tasks!.map((t) => (
                      <tr key={t.name}>
                        <td className="py-px pr-2 whitespace-nowrap">{t.name}</td>
                        <td className="py-px whitespace-nowrap text-right tabular-nums">
                          {fmtTime(t.seconds)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
