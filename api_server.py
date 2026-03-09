"""HTTP API server for tracker — Flask-based, runs in a daemon thread."""

import atexit
import threading
from datetime import date, datetime, timedelta

from html import escape

from flask import Flask, jsonify, request
from PySide6.QtCore import QObject, Signal

from models.database import Database
from models.task import Task
from models.project import Project
from utils.constants import DEFAULT_BLOCK_COLOR
from cli import _aggregate_by_project, _merge_aggregates, _totals_to_json_list, _fmt_time


class ApiNotifier(QObject):
    """Emits data_changed from API thread; Qt auto-queues to main thread."""
    data_changed = Signal()


def create_app(db: Database, notifier: ApiNotifier) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.json.ensure_ascii = False

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    _CSS = """
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body { font-family: -apple-system, 'Segoe UI', sans-serif; max-width: 720px;
             margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; line-height: 1.6; }
      h1 { font-size: 1.4rem; margin-bottom: 1rem; padding-bottom: .5rem;
           border-bottom: 2px solid #e0e0e0; }
      h2 { font-size: 1.1rem; margin: 1.2rem 0 .4rem; color: #444; }
      ul { list-style: none; margin: .5rem 0; }
      li { padding: .35rem .5rem; border-radius: 4px; }
      li:nth-child(odd) { background: #f7f7f7; }
      li ul { margin: .2rem 0 .2rem 1.2rem; }
      li li { padding: .15rem .5rem; font-size: .9rem; color: #555; }
      a { color: #2563eb; text-decoration: none; }
      a:hover { text-decoration: underline; }
      p { margin: .5rem 0; }
      b { color: #222; }
      small { color: #888; }
      nav { margin-bottom: 1rem; }
      nav a { margin-right: 1rem; }
      form { display: inline-flex; gap: .5rem; align-items: center; flex-wrap: wrap; }
      input[type=date] { padding: .3rem .4rem; border: 1px solid #ccc; border-radius: 4px; font-size: .9rem; }
      button { padding: .3rem .8rem; background: #2563eb; color: #fff; border: none;
               border-radius: 4px; font-size: .9rem; cursor: pointer; }
      button:hover { background: #1d4ed8; }
      label { font-size: .9rem; color: #555; }
      .form-row { margin: .5rem 0; }
    """

    def _nav():
        return ("<nav><a href='/'>トップ</a><a href='/tasks'>タスク</a>"
                "<a href='/projects'>プロジェクト</a><a href='/report'>レポート</a>"
                "<a href='/reports'>期間集計</a><a href='/reports-by-day'>日別</a></nav>")

    def _html(title, body):
        return (f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
                f"<title>{title} - 工数管理</title>"
                f"<style>{_CSS}</style></head>"
                f"<body>{_nav()}<h1>{title}</h1>{body}</body></html>",
                200, {"Content-Type": "text/html; charset=utf-8"})

    @app.route("/")
    def index():
        today = date.today().isoformat()
        body = (
            "<h2>タスク</h2>"
            "<div class='form-row'><form action='/tasks' method='get'>"
            f"<input type='date' name='date' value='{today}'>"
            "<label><input type='checkbox' name='simple' value='1'> シンプル</label>"
            "<button>表示</button></form></div>"

            "<h2>プロジェクト</h2>"
            "<div class='form-row'><a href='/projects'>一覧を表示</a></div>"

            "<h2>レポート（1日）</h2>"
            "<div class='form-row'><form action='/report' method='get'>"
            f"<input type='date' name='date' value='{today}'>"
            "<label><input type='checkbox' name='detail' value='1'> 内訳</label>"
            "<button>表示</button></form></div>"

            "<h2>期間集計</h2>"
            "<div class='form-row'><form action='/reports' method='get'>"
            f"<label>from</label><input type='date' name='from' value='{today}'>"
            f"<label>to</label><input type='date' name='to' value='{today}'>"
            "<label><input type='checkbox' name='detail' value='1'> 内訳</label>"
            "<button>表示</button></form></div>"

            "<h2>日別レポート</h2>"
            "<div class='form-row'><form action='/reports-by-day' method='get'>"
            f"<label>from</label><input type='date' name='from' value='{today}'>"
            f"<label>to</label><input type='date' name='to' value='{today}'>"
            "<label><input type='checkbox' name='detail' value='1'> 内訳</label>"
            "<button>表示</button></form></div>"
        )
        return _html("工数管理", body)

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api"):
            return jsonify({"error": "Not found"}), 404
        return e.get_response()

    # ── HTML endpoints ──

    @app.route("/tasks")
    def html_tasks():
        date_str = request.args.get("date", date.today().isoformat())
        simple = request.args.get("simple", "0") == "1"
        tasks = db.get_tasks_for_date(date_str)
        tasks.sort(key=lambda t: t.start_time)
        proj_map = {p.id: p.name for p in db.get_all_projects()}
        items = []
        for t in tasks:
            proj_tag = ""
            if not simple:
                proj = proj_map.get(t.project_id, "") if t.project_id else ""
                proj_tag = f" <small>[{escape(proj)}]</small>" if proj else ""
            items.append(f"<li>{escape(t.start_time.strftime('%H:%M'))} - "
                         f"{escape(t.end_time.strftime('%H:%M'))}  "
                         f"{escape(t.name)}{proj_tag}</li>")
        toggle = (f"<a href='/tasks?date={escape(date_str)}'>プロジェクトあり</a>" if simple
                  else f"<a href='/tasks?date={escape(date_str)}&simple=1'>プロジェクトなし</a>")
        body = f"<p>{escape(date_str)} ({toggle})</p><ul>{''.join(items)}</ul>" if items else "<p>タスクはありません</p>"
        return _html("タスク", body)

    @app.route("/projects")
    def html_projects():
        projects = db.get_all_projects()
        items = [f"<li><span style='color:{escape(p.color)}'>&#9632;</span> {escape(p.name)}</li>"
                 for p in projects]
        body = f"<ul>{''.join(items)}</ul>" if items else "<p>プロジェクトはありません</p>"
        return _html("プロジェクト", body)

    @app.route("/report")
    def html_report():
        date_str = request.args.get("date", date.today().isoformat())
        detail = request.args.get("detail", "0") == "1"
        simple = request.args.get("simple", "0") == "1"
        tasks = db.get_tasks_for_date(date_str)
        proj_map = {p.id: p.name for p in db.get_all_projects()}
        if simple:
            totals = _aggregate_by_task(tasks)
            items = [_report_li(n, s) for n, s in sorted(totals.items())]
        else:
            totals, details = _aggregate_by_project(tasks, proj_map, detail=detail)
            items = []
            for name in sorted(n for n in totals if n != "(なし)"):
                items.append(_report_li(name, totals[name], details.get(name) if detail else None))
            if "(なし)" in totals:
                items.append(_report_li("(なし)", totals["(なし)"], details.get("(なし)") if detail else None))
        grand = sum(totals.values())
        links = _toggle_links("/report", date_str=date_str, detail=detail, simple=simple)
        body = (f"<p>{escape(date_str)} ({' / '.join(links)})</p>"
                f"<ul>{''.join(items)}</ul><p><b>合計: {_fmt_time(grand)}</b></p>" if items
                else "<p>タスクはありません</p>")
        return _html("レポート", body)

    @app.route("/reports")
    def html_reports():
        detail = request.args.get("detail", "0") == "1"
        simple = request.args.get("simple", "0") == "1"
        start_date, end_date = _resolve_date_range()
        proj_map = {p.id: p.name for p in db.get_all_projects()}
        totals = {}
        all_details = {}
        d = start_date
        while d <= end_date:
            tasks = db.get_tasks_for_date(d.isoformat())
            if tasks:
                if simple:
                    day_totals = _aggregate_by_task(tasks)
                    for n, s in day_totals.items():
                        totals[n] = totals.get(n, 0) + s
                else:
                    day_totals, day_details = _aggregate_by_project(tasks, proj_map, detail=detail)
                    _merge_aggregates(totals, all_details, day_totals, day_details)
            d += timedelta(days=1)
        if simple:
            items = [_report_li(n, s) for n, s in sorted(totals.items())]
        else:
            items = []
            for name in sorted(n for n in totals if n != "(なし)"):
                items.append(_report_li(name, totals[name], all_details.get(name) if detail else None))
            if "(なし)" in totals:
                items.append(_report_li("(なし)", totals["(なし)"], all_details.get("(なし)") if detail else None))
        grand = sum(totals.values())
        links = _toggle_links("/reports", start_date=start_date, end_date=end_date, detail=detail, simple=simple)
        body = (f"<p>{start_date.isoformat()} 〜 {end_date.isoformat()} ({' / '.join(links)})</p>"
                f"<ul>{''.join(items)}</ul><p><b>合計: {_fmt_time(grand)}</b></p>" if items
                else "<p>タスクはありません</p>")
        return _html("期間集計", body)

    @app.route("/reports-by-day")
    def html_reports_by_day():
        detail = request.args.get("detail", "0") == "1"
        simple = request.args.get("simple", "0") == "1"
        start_date, end_date = _resolve_date_range()
        proj_map = {p.id: p.name for p in db.get_all_projects()}
        sections = []
        grand_total = 0
        d = start_date
        while d <= end_date:
            tasks = db.get_tasks_for_date(d.isoformat())
            if tasks:
                if simple:
                    day_totals = _aggregate_by_task(tasks)
                    day_total = sum(day_totals.values())
                    items = [_report_li(n, s) for n, s in sorted(day_totals.items())]
                else:
                    day_totals, day_details = _aggregate_by_project(tasks, proj_map, detail=detail)
                    day_total = sum(day_totals.values())
                    items = []
                    for name in sorted(n for n in day_totals if n != "(なし)"):
                        items.append(_report_li(name, day_totals[name], day_details.get(name) if detail else None))
                    if "(なし)" in day_totals:
                        items.append(_report_li("(なし)", day_totals["(なし)"], day_details.get("(なし)") if detail else None))
                grand_total += day_total
                sections.append(f"<h2>{d.isoformat()} ({_fmt_time(day_total)})</h2><ul>{''.join(items)}</ul>")
            d += timedelta(days=1)
        links = _toggle_links("/reports-by-day", start_date=start_date, end_date=end_date, detail=detail, simple=simple)
        body = (f"<p>{start_date.isoformat()} 〜 {end_date.isoformat()} ({' / '.join(links)})</p>"
                f"{''.join(sections)}<p><b>合計: {_fmt_time(grand_total)}</b></p>" if sections
                else "<p>タスクはありません</p>")
        return _html("日別レポート", body)

    def _aggregate_by_task(tasks):
        """Aggregate durations by task name (no project grouping)."""
        totals = {}
        for t in tasks:
            secs = (t.end_time - t.start_time).total_seconds()
            totals[t.name] = totals.get(t.name, 0) + secs
        return totals

    def _toggle_links(path, date_str=None, start_date=None, end_date=None, detail=False, simple=False):
        """Build toggle links for detail/simple switching."""
        base_params = []
        if date_str:
            base_params.append(f"date={date_str}")
        if start_date:
            base_params.append(f"from={start_date.isoformat()}")
        if end_date:
            base_params.append(f"to={end_date.isoformat()}")
        links = []
        # detail toggle
        if not simple:
            d_params = list(base_params) + ([] if detail else ["detail=1"])
            d_label = "内訳なし" if detail else "内訳"
            links.append(f"<a href='{path}?{'&'.join(d_params)}'>{d_label}</a>")
        # simple toggle
        s_params = list(base_params)
        if detail and not simple:
            s_params.append("detail=1")
        if simple:
            links.append(f"<a href='{path}?{'&'.join(s_params)}'>プロジェクトあり</a>")
        else:
            s_params.append("simple=1")
            links.append(f"<a href='{path}?{'&'.join(s_params)}'>プロジェクトなし</a>")
        return links

    def _report_li(name, secs, task_details=None):
        line = f"<li>{escape(name)} — {_fmt_time(secs)}"
        if task_details:
            sub = "".join(f"<li>{escape(tn)} — {_fmt_time(ts)}</li>"
                          for tn, ts in sorted(task_details.items()))
            line += f"<ul>{sub}</ul>"
        return line + "</li>"

    # ── JSON API endpoints ──

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/api/tasks")
    def get_tasks():
        date_str = request.args.get("date", date.today().isoformat())
        simple = request.args.get("simple", "0") == "1"
        tasks = db.get_tasks_for_date(date_str)
        tasks.sort(key=lambda t: t.start_time)
        proj_map = {p.id: p.name for p in db.get_all_projects()}
        result = []
        for t in tasks:
            entry = {
                "id": t.id,
                "name": t.name,
                "start": t.start_time.strftime("%H:%M"),
                "end": t.end_time.strftime("%H:%M"),
                "date": t.start_time.strftime("%Y-%m-%d"),
                "color": t.color,
            }
            if not simple:
                entry["project_id"] = t.project_id
                entry["project"] = proj_map.get(t.project_id) if t.project_id else None
            result.append(entry)
        return jsonify(result)

    @app.route("/api/projects")
    def get_projects():
        projects = db.get_all_projects()
        result = [
            {"id": p.id, "name": p.name, "color": p.color, "order": p.order}
            for p in projects
        ]
        return jsonify(result)

    @app.route("/api/report")
    def report():
        date_str = request.args.get("date", date.today().isoformat())
        detail = request.args.get("detail", "0") == "1"
        tasks = db.get_tasks_for_date(date_str)
        proj_map = {p.id: p.name for p in db.get_all_projects()}
        totals, details = _aggregate_by_project(tasks, proj_map, detail=detail)
        grand_total = sum(totals.values())
        return jsonify({
            "date": date_str,
            "total_seconds": int(grand_total),
            "total_formatted": _fmt_time(grand_total),
            "projects": _totals_to_json_list(totals, details if detail else None),
        })

    @app.route("/api/reports")
    def reports():
        detail = request.args.get("detail", "0") == "1"
        start_date, end_date = _resolve_date_range()
        proj_map = {p.id: p.name for p in db.get_all_projects()}
        totals = {}
        all_details = {}
        days_with_tasks = 0
        d = start_date
        while d <= end_date:
            tasks = db.get_tasks_for_date(d.isoformat())
            if tasks:
                days_with_tasks += 1
                day_totals, day_details = _aggregate_by_project(tasks, proj_map, detail=detail)
                _merge_aggregates(totals, all_details, day_totals, day_details)
            d += timedelta(days=1)
        days = (end_date - start_date).days + 1
        grand_total = sum(totals.values())
        return jsonify({
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
            "days": days,
            "days_with_tasks": days_with_tasks,
            "total_seconds": int(grand_total),
            "total_formatted": _fmt_time(grand_total),
            "projects": _totals_to_json_list(totals, all_details if detail else None),
        })

    @app.route("/api/reports-by-day")
    def reports_by_day():
        detail = request.args.get("detail", "0") == "1"
        start_date, end_date = _resolve_date_range()
        proj_map = {p.id: p.name for p in db.get_all_projects()}
        days_with_tasks = 0
        grand_total = 0
        json_days = []
        d = start_date
        while d <= end_date:
            tasks = db.get_tasks_for_date(d.isoformat())
            if tasks:
                days_with_tasks += 1
                day_totals, day_details = _aggregate_by_project(tasks, proj_map, detail=detail)
                day_total = sum(day_totals.values())
                grand_total += day_total
                json_days.append({
                    "date": d.isoformat(),
                    "total_seconds": int(day_total),
                    "total_formatted": _fmt_time(day_total),
                    "projects": _totals_to_json_list(day_totals, day_details if detail else None),
                })
            d += timedelta(days=1)
        days = (end_date - start_date).days + 1
        return jsonify({
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
            "days": days,
            "days_with_tasks": days_with_tasks,
            "total_seconds": int(grand_total),
            "total_formatted": _fmt_time(grand_total),
            "daily": json_days,
        })

    # ── POST endpoints ──

    @app.route("/api/tasks", methods=["POST"])
    def post_task():
        body = request.get_json(force=True)
        name = body.get("name")
        start_str = body.get("start")
        end_str = body.get("end")
        if not name or not start_str or not end_str:
            return jsonify({"error": "name, start, end are required"}), 400
        try:
            start = datetime.strptime(start_str, "%H:%M")
            end = datetime.strptime(end_str, "%H:%M")
        except ValueError:
            return jsonify({"error": "start/end must be HH:MM format"}), 400
        date_str = body.get("date")
        target_date = date.fromisoformat(date_str) if date_str else date.today()
        start_dt = datetime(target_date.year, target_date.month, target_date.day,
                            start.hour, start.minute)
        end_dt = datetime(target_date.year, target_date.month, target_date.day,
                          end.hour, end.minute)
        color = DEFAULT_BLOCK_COLOR
        project_id = None
        project_name = body.get("project")
        if project_name:
            projects = db.get_all_projects()
            matched = [p for p in projects if p.name == project_name]
            if not matched:
                return jsonify({"error": f"project '{project_name}' not found"}), 400
            project_id = matched[0].id
            color = matched[0].color
        task = Task(name=name, start_time=start_dt, end_time=end_dt,
                    color=color, project_id=project_id)
        db.insert_task(task)
        notifier.data_changed.emit()
        return jsonify({
            "id": task.id,
            "name": task.name,
            "start": start_str,
            "end": end_str,
            "date": target_date.isoformat(),
            "project": project_name,
        }), 201

    @app.route("/api/projects", methods=["POST"])
    def post_project():
        body = request.get_json(force=True)
        name = body.get("name")
        if not name:
            return jsonify({"error": "name is required"}), 400
        projects = db.get_all_projects()
        if any(p.name == name for p in projects):
            return jsonify({"error": f"project '{name}' already exists"}), 409
        order = max((p.order for p in projects), default=-1) + 1
        project = Project(name=name, order=order)
        if body.get("color"):
            project.color = body["color"]
        db.insert_project(project)
        notifier.data_changed.emit()
        return jsonify({
            "id": project.id,
            "name": project.name,
            "color": project.color,
            "order": project.order,
        }), 201

    # ── Helpers ──

    def _resolve_date_range():
        to_str = request.args.get("to")
        end_date = date.fromisoformat(to_str) if to_str else date.today()
        since_str = request.args.get("since")
        from_str = request.args.get("from")
        if since_str:
            days = int(since_str.rstrip("d"))
            start_date = end_date - timedelta(days=days - 1)
        elif from_str:
            start_date = date.fromisoformat(from_str)
        else:
            start_date = end_date - timedelta(days=29)
        return start_date, end_date

    return app


class ApiServer:
    """Flask API server running in a daemon thread."""

    def __init__(self, port: int, notifier: ApiNotifier):
        self._port = port
        self._notifier = notifier
        self._db = Database(check_same_thread=False)
        self._app = create_app(self._db, notifier)
        self._server = None
        self._thread = None

    def start(self):
        from werkzeug.serving import make_server
        self._server = make_server("127.0.0.1", self._port, self._app, threaded=True)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        atexit.register(self.stop)

    def stop(self):
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._db is not None:
            self._db.close()
            self._db = None
