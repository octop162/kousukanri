"""CLI entry point for tracker — add/list tasks without GUI."""

import argparse
import sys
from datetime import datetime, date, timedelta

from models.database import Database
from models.task import Task
from models.project import Project
from utils.constants import DEFAULT_BLOCK_COLOR


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


def cmd_list(args, db: Database):
    target_date = args.date if args.date else date.today().isoformat()
    tasks = db.get_tasks_for_date(target_date)

    if not tasks:
        print("タスクはありません")
        return

    # Build project id -> name map
    projects = db.get_all_projects()
    proj_map = {p.id: p.name for p in projects}

    tasks.sort(key=lambda t: t.start_time)
    for t in tasks:
        start_str = t.start_time.strftime("%H:%M")
        end_str = t.end_time.strftime("%H:%M")
        proj_str = f"  [{proj_map[t.project_id]}]" if t.project_id and t.project_id in proj_map else ""
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


def _aggregate_by_project(tasks, proj_map):
    """Aggregate task durations by project name. Returns dict {name: seconds}."""
    totals = {}
    for t in tasks:
        name = proj_map.get(t.project_id, "(なし)") if t.project_id else "(なし)"
        secs = (t.end_time - t.start_time).total_seconds()
        totals[name] = totals.get(name, 0) + secs
    return totals


def _print_report_table(totals):
    """Print a formatted report table from totals dict."""
    # Sort: named projects alphabetically, "(なし)" last
    sorted_names = sorted(n for n in totals if n != "(なし)")
    if "(なし)" in totals:
        sorted_names.append("(なし)")

    max_dw = max(_display_width(n) for n in sorted_names)
    line_width = max(max_dw + 2 + 10, 30)

    print("─" * line_width)
    grand_total = 0
    for name in sorted_names:
        secs = totals[name]
        grand_total += secs
        pad = " " * (max_dw - _display_width(name) + 2)
        print(f"{name}{pad}{_fmt_time(secs)}")
    print("─" * line_width)
    pad = " " * (max_dw - _display_width("合計") + 2)
    print(f"合計{pad}{_fmt_time(grand_total)}")


def cmd_report(args, db: Database):
    if args.yesterday:
        target_date = (date.today() - timedelta(days=1)).isoformat()
    elif args.date:
        target_date = args.date
    else:
        target_date = date.today().isoformat()
    tasks = db.get_tasks_for_date(target_date)

    print(f"{target_date} レポート")
    if not tasks:
        print("タスクはありません")
        return

    proj_map = {p.id: p.name for p in db.get_all_projects()}
    totals = _aggregate_by_project(tasks, proj_map)
    _print_report_table(totals)


def cmd_report_30d(args, db: Database):
    end_date = date.fromisoformat(args.date) if args.date else date.today()
    start_date = end_date - timedelta(days=29)

    proj_map = {p.id: p.name for p in db.get_all_projects()}
    grand_total = 0
    days_with_tasks = 0

    print(f"{start_date.isoformat()} 〜 {end_date.isoformat()} レポート（30日間）")
    print()

    for i in range(30):
        d = start_date + timedelta(days=i)
        tasks = db.get_tasks_for_date(d.isoformat())
        if not tasks:
            continue
        days_with_tasks += 1
        totals = _aggregate_by_project(tasks, proj_map)
        day_total = sum(totals.values())
        grand_total += day_total
        print(f"■ {d.isoformat()}  ({_fmt_time(day_total)})")
        _print_report_table(totals)
        print()

    if days_with_tasks == 0:
        print("タスクはありません")
        return

    print(f"記録日数: {days_with_tasks}日 / 合計: {_fmt_time(grand_total)}")


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

    # report-30d
    p_r30 = sub.add_parser("report-30d", help="過去30日のプロジェクト別レポート")
    p_r30.add_argument("--date", help="終了日 (YYYY-MM-DD, デフォルト: 今日)")

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
        elif args.command == "report-30d":
            cmd_report_30d(args, db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
