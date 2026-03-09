"""CLI entry point for tracker — add/list tasks without GUI."""

import argparse
import io
import json
import sys
from datetime import datetime, date, timedelta

# Windows cp932 環境での文字化け対策: stdout/stderr を UTF-8 に強制
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from models.database import Database
from models.task import Task
from models.project import Project
from utils.constants import DEFAULT_BLOCK_COLOR

_SERVER_NAME = "kousu-kanri-single-instance"


def _notify_gui():
    """Send 'reload' message to running GUI via QLocalSocket."""
    try:
        from PySide6.QtNetwork import QLocalSocket
        from PySide6.QtWidgets import QApplication
        # QLocalSocket requires a QCoreApplication
        app = QApplication.instance()
        owns_app = False
        if app is None:
            from PySide6.QtCore import QCoreApplication
            app = QCoreApplication([])
            owns_app = True
        sock = QLocalSocket()
        sock.connectToServer(_SERVER_NAME)
        if sock.waitForConnected(500):
            sock.write(b"reload")
            sock.flush()
            sock.waitForBytesWritten(500)
            sock.close()
    except Exception:
        pass  # GUI が起動していなければ何もしない


def cmd_add(args, db: Database):
    # Parse start/end times
    try:
        start = datetime.strptime(args.start, "%H:%M")
        end = datetime.strptime(args.end, "%H:%M")
    except ValueError:
        print("エラー: 時刻は HH:MM 形式で指定してください", file=sys.stderr)
        sys.exit(1)

    target_date = date.fromisoformat(args.date) if args.date else date.today()
    start_dt = datetime(target_date.year, target_date.month, target_date.day,
                        start.hour, start.minute)
    end_dt = datetime(target_date.year, target_date.month, target_date.day,
                      end.hour, end.minute)

    color = DEFAULT_BLOCK_COLOR
    project_id = None

    if args.project:
        projects = db.get_all_projects()
        matched = [p for p in projects if p.name == args.project]
        if not matched:
            print(f'エラー: プロジェクト「{args.project}」が見つかりません', file=sys.stderr)
            sys.exit(1)
        project_id = matched[0].id
        color = matched[0].color

    task = Task(
        name=args.name,
        start_time=start_dt,
        end_time=end_dt,
        color=color,
        project_id=project_id,
    )
    db.insert_task(task)
    proj_str = f"  [{args.project}]" if args.project else ""
    print(f"追加: {args.start} - {args.end}  {args.name}{proj_str}")
    _notify_gui()


def cmd_list(args, db: Database):
    if args.yesterday:
        target_date = (date.today() - timedelta(days=1)).isoformat()
    elif args.date:
        target_date = args.date
    else:
        target_date = date.today().isoformat()
    tasks = db.get_tasks_for_date(target_date)

    if not tasks:
        print("タスクはありません")
        return

    # Build project id -> name map
    projects = db.get_all_projects()
    proj_map = {p.id: p.name for p in projects}

    simple = getattr(args, "simple", False)
    tasks.sort(key=lambda t: t.start_time)
    for t in tasks:
        start_str = t.start_time.strftime("%H:%M")
        end_str = t.end_time.strftime("%H:%M")
        proj_str = "" if simple else (f"  [{proj_map[t.project_id]}]" if t.project_id and t.project_id in proj_map else "")
        print(f"{start_str} - {end_str}  {t.name}{proj_str}")


def cmd_add_project(args, db: Database):
    projects = db.get_all_projects()
    if any(p.name == args.name for p in projects):
        print(f'エラー: プロジェクト「{args.name}」は既に存在します', file=sys.stderr)
        sys.exit(1)
    order = max((p.order for p in projects), default=-1) + 1
    project = Project(name=args.name, order=order)
    if args.color:
        project.color = args.color
    db.insert_project(project)
    print(f"プロジェクト追加: {args.name}  ({project.color})")
    _notify_gui()


def _display_width(s):
    """Calculate display width accounting for fullwidth characters."""
    w = 0
    for c in s:
        if ord(c) > 0x7F:
            w += 2
        else:
            w += 1
    return w


def _fmt_time(seconds):
    h = int(seconds) // 3600
    m = int(seconds) % 3600 // 60
    return f"{h}h {m:02d}m"


def _aggregate_by_project(tasks, proj_map, detail=False):
    """Aggregate task durations by project name.

    Returns (totals, details):
      totals: {project_name: seconds}
      details: {project_name: {task_name: seconds}} (only if detail=True, else {})
    """
    totals = {}
    details = {}
    for t in tasks:
        proj_name = proj_map.get(t.project_id, "(なし)") if t.project_id else "(なし)"
        secs = (t.end_time - t.start_time).total_seconds()
        totals[proj_name] = totals.get(proj_name, 0) + secs
        if detail:
            details.setdefault(proj_name, {})
            details[proj_name][t.name] = details[proj_name].get(t.name, 0) + secs
    return totals, details


def _merge_aggregates(dst_totals, dst_details, src_totals, src_details):
    """Merge src aggregates into dst (in-place)."""
    for name, secs in src_totals.items():
        dst_totals[name] = dst_totals.get(name, 0) + secs
    for proj, tasks in src_details.items():
        dst_details.setdefault(proj, {})
        for task_name, secs in tasks.items():
            dst_details[proj][task_name] = dst_details[proj].get(task_name, 0) + secs


def _format_report_table(totals, details=None) -> str:
    """Format a report table from totals dict and return as string."""
    # Sort: named projects alphabetically, "(なし)" last
    sorted_names = sorted(n for n in totals if n != "(なし)")
    if "(なし)" in totals:
        sorted_names.append("(なし)")

    # Calculate max width considering detail lines
    all_labels = list(sorted_names) + ["合計"]
    if details:
        for proj in sorted_names:
            if proj in details:
                for task_name in details[proj]:
                    all_labels.append("  " + task_name)
    max_dw = max(_display_width(l) for l in all_labels)
    line_width = max(max_dw + 2 + 10, 30)

    lines = []
    lines.append("─" * line_width)
    grand_total = 0
    for name in sorted_names:
        secs = totals[name]
        grand_total += secs
        pad = " " * (max_dw - _display_width(name) + 2)
        lines.append(f"{name}{pad}{_fmt_time(secs)}")
        if details and name in details:
            for task_name in sorted(details[name]):
                label = "  " + task_name
                tsecs = details[name][task_name]
                tpad = " " * (max_dw - _display_width(label) + 2)
                lines.append(f"{label}{tpad}{_fmt_time(tsecs)}")
    lines.append("─" * line_width)
    pad = " " * (max_dw - _display_width("合計") + 2)
    lines.append(f"合計{pad}{_fmt_time(grand_total)}")
    return "\n".join(lines)


def _totals_to_json_list(totals, details=None):
    """Convert totals/details dicts to a JSON-serializable list of project entries."""
    sorted_names = sorted(n for n in totals if n != "(なし)")
    if "(なし)" in totals:
        sorted_names.append("(なし)")

    entries = []
    for name in sorted_names:
        secs = totals[name]
        entry = {"project": name, "seconds": int(secs), "formatted": _fmt_time(secs)}
        if details and name in details:
            entry["tasks"] = [
                {"name": tn, "seconds": int(ts), "formatted": _fmt_time(ts)}
                for tn, ts in sorted(details[name].items())
            ]
        entries.append(entry)
    return entries


def _print_report_table(totals, details=None):
    """Print a formatted report table from totals dict."""
    print(_format_report_table(totals, details))


def cmd_report(args, db: Database):
    if args.yesterday:
        target_date = (date.today() - timedelta(days=1)).isoformat()
    elif args.date:
        target_date = args.date
    else:
        target_date = date.today().isoformat()
    tasks = db.get_tasks_for_date(target_date)

    detail = getattr(args, "detail", False)
    use_json = getattr(args, "json", False)

    if not tasks:
        if use_json:
            print(json.dumps({"date": target_date, "projects": []}, ensure_ascii=False, indent=2))
        else:
            print(f"{target_date} レポート")
            print("タスクはありません")
        return

    proj_map = {p.id: p.name for p in db.get_all_projects()}
    totals, details = _aggregate_by_project(tasks, proj_map, detail=detail)

    if use_json:
        grand_total = sum(totals.values())
        data = {
            "date": target_date,
            "total_seconds": int(grand_total),
            "total_formatted": _fmt_time(grand_total),
            "projects": _totals_to_json_list(totals, details if detail else None),
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"{target_date} レポート")
        _print_report_table(totals, details if detail else None)


def _resolve_date_range(args) -> tuple[date, date]:
    """Resolve --from/--to/--since into (start_date, end_date)."""
    end_date = date.fromisoformat(args.to) if args.to else date.today()
    if args.since:
        try:
            days = int(args.since.rstrip("d"))
        except ValueError:
            print("エラー: --since は数値または '30d' 形式で指定してください", file=sys.stderr)
            sys.exit(1)
        start_date = end_date - timedelta(days=days - 1)
    elif getattr(args, "from"):
        start_date = date.fromisoformat(getattr(args, "from"))
    else:
        start_date = end_date - timedelta(days=29)
    return start_date, end_date


def _iter_date_range(start_date: date, end_date: date):
    d = start_date
    while d <= end_date:
        yield d
        d += timedelta(days=1)


def cmd_reports_by_day(args, db: Database):
    start_date, end_date = _resolve_date_range(args)
    detail = getattr(args, "detail", False)
    use_json = getattr(args, "json", False)

    proj_map = {p.id: p.name for p in db.get_all_projects()}
    grand_total = 0
    days_with_tasks = 0

    days = (end_date - start_date).days + 1
    json_days = []

    if not use_json:
        print(f"{start_date.isoformat()} 〜 {end_date.isoformat()} 日別レポート（{days}日間）")
        print()

    for d in _iter_date_range(start_date, end_date):
        tasks = db.get_tasks_for_date(d.isoformat())
        if not tasks:
            continue
        days_with_tasks += 1
        totals, details = _aggregate_by_project(tasks, proj_map, detail=detail)
        day_total = sum(totals.values())
        grand_total += day_total

        if use_json:
            json_days.append({
                "date": d.isoformat(),
                "total_seconds": int(day_total),
                "total_formatted": _fmt_time(day_total),
                "projects": _totals_to_json_list(totals, details if detail else None),
            })
        else:
            print(f"■ {d.isoformat()}  ({_fmt_time(day_total)})")
            _print_report_table(totals, details if detail else None)
            print()

    if use_json:
        data = {
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
            "days": days,
            "days_with_tasks": days_with_tasks,
            "total_seconds": int(grand_total),
            "total_formatted": _fmt_time(grand_total),
            "daily": json_days,
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        if days_with_tasks == 0:
            print("タスクはありません")
            return
        print(f"記録日数: {days_with_tasks}日 / 合計: {_fmt_time(grand_total)}")


def cmd_reports(args, db: Database):
    start_date, end_date = _resolve_date_range(args)
    detail = getattr(args, "detail", False)
    use_json = getattr(args, "json", False)

    proj_map = {p.id: p.name for p in db.get_all_projects()}
    totals = {}
    all_details = {}
    days_with_tasks = 0

    for d in _iter_date_range(start_date, end_date):
        tasks = db.get_tasks_for_date(d.isoformat())
        if not tasks:
            continue
        days_with_tasks += 1
        day_totals, day_details = _aggregate_by_project(tasks, proj_map, detail=detail)
        _merge_aggregates(totals, all_details, day_totals, day_details)

    days = (end_date - start_date).days + 1

    if use_json:
        grand_total = sum(totals.values())
        data = {
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
            "days": days,
            "days_with_tasks": days_with_tasks,
            "total_seconds": int(grand_total),
            "total_formatted": _fmt_time(grand_total),
            "projects": _totals_to_json_list(totals, all_details if detail else None),
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"{start_date.isoformat()} 〜 {end_date.isoformat()} 集計レポート（{days}日間）")
        if not totals:
            print("タスクはありません")
            return
        _print_report_table(totals, all_details if detail else None)
        print(f"\n記録日数: {days_with_tasks}日")


def cmd_list_projects(args, db: Database):
    projects = db.get_all_projects()
    if not projects:
        print("プロジェクトはありません")
        return
    for p in projects:
        print(f"{p.name}  ({p.color})")


def main():
    parser = argparse.ArgumentParser(description="KousuKanri CLI")
    sub = parser.add_subparsers(dest="command")

    # add
    p_add = sub.add_parser("add", help="タスクを追加")
    p_add.add_argument("name", help="タスク名")
    p_add.add_argument("start", help="開始時刻 (HH:MM)")
    p_add.add_argument("end", help="終了時刻 (HH:MM)")
    p_add.add_argument("--project", help="プロジェクト名")
    p_add.add_argument("--date", help="日付 (YYYY-MM-DD, デフォルト: 今日)")

    # list
    p_list = sub.add_parser("list", help="タスク一覧")
    p_list.add_argument("--date", help="日付 (YYYY-MM-DD, デフォルト: 今日)")
    p_list.add_argument("--yesterday", action="store_true", help="昨日のタスク一覧")
    p_list.add_argument("--simple", action="store_true", help="プロジェクト表示を省略")

    # add-project
    p_ap = sub.add_parser("add-project", help="プロジェクトを追加")
    p_ap.add_argument("name", help="プロジェクト名")
    p_ap.add_argument("--color", help="色 (例: #FF5722)")

    # list-projects
    sub.add_parser("list-projects", help="プロジェクト一覧")

    # report
    p_report = sub.add_parser("report", help="プロジェクト別レポート")
    p_report.add_argument("--date", help="日付 (YYYY-MM-DD, デフォルト: 今日)")
    p_report.add_argument("--yesterday", action="store_true", help="昨日のレポート")
    p_report.add_argument("--detail", action="store_true", help="タスク別の内訳を表示")
    p_report.add_argument("--json", action="store_true", help="JSON形式で出力")

    # reports-by-day
    p_rbd = sub.add_parser("reports-by-day", help="期間内の日別レポート")
    p_rbd.add_argument("--from", dest="from", help="開始日 (YYYY-MM-DD)")
    p_rbd.add_argument("--to", help="終了日 (YYYY-MM-DD, デフォルト: 今日)")
    p_rbd.add_argument("--since", help="過去N日 (例: 30, 7d)")
    p_rbd.add_argument("--detail", action="store_true", help="タスク別の内訳を表示")
    p_rbd.add_argument("--json", action="store_true", help="JSON形式で出力")

    # reports
    p_rs = sub.add_parser("reports", help="期間内のプロジェクト別集計")
    p_rs.add_argument("--from", dest="from", help="開始日 (YYYY-MM-DD)")
    p_rs.add_argument("--to", help="終了日 (YYYY-MM-DD, デフォルト: 今日)")
    p_rs.add_argument("--since", help="過去N日 (例: 30, 7d)")
    p_rs.add_argument("--detail", action="store_true", help="タスク別の内訳を表示")
    p_rs.add_argument("--json", action="store_true", help="JSON形式で出力")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    db = Database()
    try:
        if args.command == "add":
            cmd_add(args, db)
        elif args.command == "list":
            cmd_list(args, db)
        elif args.command == "add-project":
            cmd_add_project(args, db)
        elif args.command == "list-projects":
            cmd_list_projects(args, db)
        elif args.command == "report":
            cmd_report(args, db)
        elif args.command == "reports-by-day":
            cmd_reports_by_day(args, db)
        elif args.command == "reports":
            cmd_reports(args, db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
