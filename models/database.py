"""SQLite DAL for tracker — WAL mode, ISO datetime strings."""

import sqlite3
from datetime import datetime
from pathlib import Path

from models.task import Task
from models.project import Project
from models.routine import Routine


class Database:
    def __init__(self, db_path: str | Path | None = None, check_same_thread: bool = True):
        if db_path is None:
            from utils.settings import DATA_DIR
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            db_path = DATA_DIR / "tracker.db"
        self._conn = sqlite3.connect(str(db_path), check_same_thread=check_same_thread)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    def _create_tables(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                color TEXT NOT NULL,
                "order" INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                color TEXT NOT NULL,
                project_id TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS routines (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                project_id TEXT,
                start_hour INTEGER NOT NULL,
                start_minute INTEGER NOT NULL,
                end_hour INTEGER NOT NULL,
                end_minute INTEGER NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_start_date
              ON tasks(substr(start_time, 1, 10));
        """)
        self._conn.commit()

    # ── Project CRUD ──

    def insert_project(self, project: Project):
        self._conn.execute(
            'INSERT OR REPLACE INTO projects (id, name, color, "order") VALUES (?, ?, ?, ?)',
            (project.id, project.name, project.color, project.order),
        )
        self._conn.commit()

    def update_project(self, project: Project):
        self._conn.execute(
            'UPDATE projects SET name=?, color=?, "order"=? WHERE id=?',
            (project.name, project.color, project.order, project.id),
        )
        self._conn.commit()

    def delete_project(self, project_id: str):
        self._conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        self._conn.commit()

    def get_all_projects(self) -> list[Project]:
        rows = self._conn.execute(
            'SELECT id, name, color, "order" FROM projects ORDER BY "order"'
        ).fetchall()
        return [
            Project(id=r[0], name=r[1], color=r[2], order=r[3])
            for r in rows
        ]

    # ── Task CRUD ──

    def insert_task(self, task: Task):
        self._conn.execute(
            "INSERT OR REPLACE INTO tasks (id, name, start_time, end_time, color, project_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (task.id, task.name,
             task.start_time.isoformat(), task.end_time.isoformat(),
             task.color, task.project_id),
        )
        self._conn.commit()

    def update_task(self, task: Task):
        self._conn.execute(
            "UPDATE tasks SET name=?, start_time=?, end_time=?, color=?, project_id=? WHERE id=?",
            (task.name,
             task.start_time.isoformat(), task.end_time.isoformat(),
             task.color, task.project_id, task.id),
        )
        self._conn.commit()

    def delete_task(self, task_id: str):
        self._conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self._conn.commit()

    def get_tasks_for_date(self, date_str: str) -> list[Task]:
        """Get tasks for a date. date_str should be 'YYYY-MM-DD'."""
        rows = self._conn.execute(
            "SELECT id, name, start_time, end_time, color, project_id "
            "FROM tasks WHERE substr(start_time, 1, 10) = ?",
            (date_str,),
        ).fetchall()
        return [
            Task(
                id=r[0], name=r[1],
                start_time=datetime.fromisoformat(r[2]),
                end_time=datetime.fromisoformat(r[3]),
                color=r[4], project_id=r[5],
            )
            for r in rows
        ]

    def get_tasks_by_name_and_project(self, name: str, project_id: str | None) -> list[Task]:
        """Get all tasks matching given name and project_id."""
        if project_id is None:
            rows = self._conn.execute(
                "SELECT id, name, start_time, end_time, color, project_id "
                "FROM tasks WHERE name = ? AND project_id IS NULL",
                (name,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id, name, start_time, end_time, color, project_id "
                "FROM tasks WHERE name = ? AND project_id = ?",
                (name, project_id),
            ).fetchall()
        return [
            Task(
                id=r[0], name=r[1],
                start_time=datetime.fromisoformat(r[2]),
                end_time=datetime.fromisoformat(r[3]),
                color=r[4], project_id=r[5],
            )
            for r in rows
        ]

    def get_recent_task_names(self, days: int = 30) -> list[tuple[str, str | None]]:
        """Get distinct (name, project_id) pairs from the last N days, most recent last."""
        since = (datetime.now() - __import__("datetime").timedelta(days=days)).strftime("%Y-%m-%d")
        rows = self._conn.execute(
            "SELECT name, project_id, MAX(start_time) as latest "
            "FROM tasks WHERE substr(start_time, 1, 10) >= ? "
            "GROUP BY name, project_id ORDER BY latest",
            (since,),
        ).fetchall()
        return [(r[0], r[1]) for r in rows]

    def bulk_update_tasks(self, tasks: list[Task]):
        """Update multiple tasks in a single transaction."""
        with self._conn:
            for task in tasks:
                self._conn.execute(
                    "UPDATE tasks SET name=?, start_time=?, end_time=?, color=?, project_id=? WHERE id=?",
                    (task.name,
                     task.start_time.isoformat(), task.end_time.isoformat(),
                     task.color, task.project_id, task.id),
                )

    # ── Routine CRUD ──

    def insert_routine(self, routine: Routine):
        self._conn.execute(
            "INSERT OR REPLACE INTO routines "
            "(id, name, project_id, start_hour, start_minute, end_hour, end_minute, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (routine.id, routine.name, routine.project_id,
             routine.start_hour, routine.start_minute,
             routine.end_hour, routine.end_minute, routine.order),
        )
        self._conn.commit()

    def delete_routine(self, routine_id: str):
        self._conn.execute("DELETE FROM routines WHERE id=?", (routine_id,))
        self._conn.commit()

    def get_all_routines(self) -> list[Routine]:
        rows = self._conn.execute(
            "SELECT id, name, project_id, start_hour, start_minute, end_hour, end_minute, sort_order "
            "FROM routines ORDER BY sort_order"
        ).fetchall()
        return [
            Routine(
                id=r[0], name=r[1], project_id=r[2],
                start_hour=r[3], start_minute=r[4],
                end_hour=r[5], end_minute=r[6], order=r[7],
            )
            for r in rows
        ]

    def update_routine(self, routine: Routine):
        self._conn.execute(
            "UPDATE routines SET name=?, project_id=?, start_hour=?, start_minute=?, "
            "end_hour=?, end_minute=?, sort_order=? WHERE id=?",
            (routine.name, routine.project_id, routine.start_hour, routine.start_minute,
             routine.end_hour, routine.end_minute, routine.order, routine.id),
        )
        self._conn.commit()

    def update_routine_orders(self, routines: list[Routine]):
        """Bulk-update sort_order for all routines."""
        self._conn.executemany(
            "UPDATE routines SET sort_order=? WHERE id=?",
            [(r.order, r.id) for r in routines],
        )
        self._conn.commit()

    # ── Utility ──

    def has_data(self) -> bool:
        """Return True if there is at least one project in the DB."""
        row = self._conn.execute("SELECT COUNT(*) FROM projects").fetchone()
        return row[0] > 0

    def close(self):
        self._conn.close()
