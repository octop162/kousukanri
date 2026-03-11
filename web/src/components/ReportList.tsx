import type { ReportEntry } from "../api";
import { fmtTime } from "../utils";

interface Props {
  items: ReportEntry[];
  grandTotal: number;
}

export default function ReportList({ items, grandTotal }: Props) {
  return (
    <div className="text-sm">
      <table className="border-collapse w-full max-w-md">
        <tbody>
          {items.map((item) => (
            <tr key={item.name}>
              <td className="py-0.5 pr-2 align-top whitespace-nowrap">
                {item.name}
              </td>
              <td className="py-0.5 align-top whitespace-nowrap text-right tabular-nums w-24">
                {fmtTime(item.seconds)}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="border-t border-base-300 font-semibold">
            <td className="pt-1.5">合計</td>
            <td className="pt-1.5 text-right tabular-nums w-24">{fmtTime(grandTotal)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
