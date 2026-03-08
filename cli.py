"""CLI entry point for tracker — add/list tasks without GUI."""

import argparse
import sys
from datetime import datetime, date

from models.database import Database
from models.task import Task
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
    finally:
        db.close()


if __name__ == "__main__":
    main()
