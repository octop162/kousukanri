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
    </div>
  );
}
