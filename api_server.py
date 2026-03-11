"""HTTP API server for tracker — Flask-based, runs in a daemon thread."""

import atexit
import sys
import threading
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from PySide6.QtCore import QObject, Signal

from models.database import Database
from models.task import Task
from models.project import Project
from utils.constants import DEFAULT_BLOCK_COLOR
from utils.report_helpers import (
    _aggregate_by_project, _aggregate_by_task, _merge_aggregates,
    _totals_to_json_list, _fmt_time,
)


def _get_static_dir() -> str:
    if "__compiled__" in globals():
        return str(Path(sys.executable).parent / "static")
    return str(Path(__file__).parent / "static")


class ApiNotifier(QObject):
    """Emits data_changed from API thread; Qt auto-queues to main thread."""
    data_changed = Signal()


def create_app(db: Database, notifier: ApiNotifier) -> Flask:
    """Create and configure the Flask application."""
    static_dir = _get_static_dir()
    app = Flask(__name__, static_folder=static_dir, static_url_path="")
    app.json.ensure_ascii = False

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    # ── API docs ──

    @app.route("/api/docs")
    def api_docs():
        return """<!DOCTYPE html>
<html><head>
<title>KousuKanri API Docs</title>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>body{margin:0;padding:0}</style>
</head><body>
<redoc spec-url="/openapi.yaml"></redoc>
<script src="/redoc.standalone.js"></script>
</body></html>"""

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
            {"id": p.id, "name": p.name, "color": p.color, "order": p.order, "archived": p.archived}
            for p in projects
        ]
        return jsonify(result)

    @app.route("/api/report/daily")
    def report_daily():
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
                day_totals = _aggregate_by_project(tasks, proj_map)
                day_total = sum(day_totals.values())
                grand_total += day_total
                json_days.append({
                    "date": d.isoformat(),
                    "total_seconds": int(day_total),
                    "total_formatted": _fmt_time(day_total),
                    "projects": _totals_to_json_list(day_totals),
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

    @app.route("/api/report/tasks")
    def report_tasks():
        start_date, end_date = _resolve_date_range()
        totals = {}
        days_with_tasks = 0
        d = start_date
        while d <= end_date:
            tasks = db.get_tasks_for_date(d.isoformat())
            if tasks:
                days_with_tasks += 1
                day_totals = _aggregate_by_task(tasks)
                _merge_aggregates(totals, day_totals)
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
            "tasks": _totals_to_json_list(totals),
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

    @app.route("/api/projects/<project_id>/archive", methods=["PATCH"])
    def patch_project_archive(project_id):
        body = request.get_json(force=True)
        archived = body.get("archived", True)
        projects = db.get_all_projects()
        if not any(p.id == project_id for p in projects):
            return jsonify({"error": "project not found"}), 404
        db.archive_project(project_id, archived)
        notifier.data_changed.emit()
        return jsonify({"id": project_id, "archived": archived})

    # ── SPA catch-all (must be last) ──

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api"):
            return jsonify({"error": "Not found"}), 404
        return send_from_directory(static_dir, "index.html")

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
