"""CLI for KousuKanri — powered by auto-generated API client."""

from __future__ import annotations

import sys
from datetime import date, timedelta

import click

from kousu_kanri_api_client.client import Client
from kousu_kanri_api_client.api.タスク import get_api_tasks, post_api_tasks
from kousu_kanri_api_client.api.プロジェクト import get_api_projects, post_api_projects
from kousu_kanri_api_client.api.レポート import get_api_report, get_api_reports, get_api_reports_by_day
from kousu_kanri_api_client.models.get_api_tasks_simple import GetApiTasksSimple
from kousu_kanri_api_client.models.get_api_report_detail import GetApiReportDetail
from kousu_kanri_api_client.models.get_api_reports_detail import GetApiReportsDetail
from kousu_kanri_api_client.models.get_api_reports_by_day_detail import GetApiReportsByDayDetail
from kousu_kanri_api_client.models.task_create import TaskCreate
from kousu_kanri_api_client.models.project_create import ProjectCreate
from kousu_kanri_api_client.types import UNSET


def _client(ctx: click.Context) -> Client:
    return ctx.obj["client"]


def _fmt_projects(projects, detail: bool = False):
    """Format project entries for display."""
    for p in projects:
        name = p.name if not isinstance(p.name, type(UNSET)) else "(未分類)"
        formatted = p.formatted if not isinstance(p.formatted, type(UNSET)) else ""
        click.echo(f"  {name}: {formatted}")
        if detail and not isinstance(getattr(p, "tasks", UNSET), type(UNSET)):
            for t in p.tasks:
                t_name = t.name if not isinstance(t.name, type(UNSET)) else ""
                t_fmt = t.formatted if not isinstance(t.formatted, type(UNSET)) else ""
                click.echo(f"    - {t_name}: {t_fmt}")


@click.group()
@click.option("--port", default=8321, envvar="KOUSU_PORT", help="API server port")
@click.pass_context
def cli(ctx, port: int):
    """工数管理 CLI"""
    ctx.ensure_object(dict)
    ctx.obj["client"] = Client(base_url=f"http://127.0.0.1:{port}")


# ── tasks ──


@cli.command()
@click.option("--date", "-d", "date_str", default=None, help="日付 (YYYY-MM-DD, default: today)")
@click.option("--simple", "-s", is_flag=True, help="プロジェクト情報を省略")
@click.pass_context
def tasks(ctx, date_str: str | None, simple: bool):
    """タスク一覧を表示"""
    client = _client(ctx)
    kwargs = {}
    if date_str:
        kwargs["date"] = date.fromisoformat(date_str)
    if simple:
        kwargs["simple"] = GetApiTasksSimple.VALUE_1
    result = get_api_tasks.sync(client=client, **kwargs)
    if result is None:
        click.echo("Error: API に接続できません", err=True)
        sys.exit(1)
    if not result:
        click.echo("(タスクなし)")
        return
    for t in result:
        proj = f" [{t.project}]" if not isinstance(t.project, type(UNSET)) and t.project else ""
        click.echo(f"{t.start}-{t.end}  {t.name}{proj}")


@cli.command("add")
@click.argument("name")
@click.argument("start")
@click.argument("end")
@click.option("--date", "-d", "date_str", default=None, help="日付 (YYYY-MM-DD)")
@click.option("--project", "-p", default=None, help="プロジェクト名")
@click.pass_context
def add_task(ctx, name: str, start: str, end: str, date_str: str | None, project: str | None):
    """タスクを追加  (例: kousu add コーディング 09:00 10:30 -p 開発)"""
    client = _client(ctx)
    body = TaskCreate(name=name, start=start, end=end)
    if date_str:
        body.date = date.fromisoformat(date_str)
    if project:
        body.project = project
    resp = post_api_tasks.sync_detailed(client=client, body=body)
    if resp.status_code.value == 201:
        click.echo(f"追加: {name} {start}-{end}")
    else:
        click.echo(f"Error ({resp.status_code.value}): {resp.content.decode()}", err=True)
        sys.exit(1)


# ── projects ──


@cli.command()
@click.pass_context
def projects(ctx):
    """プロジェクト一覧を表示"""
    client = _client(ctx)
    result = get_api_projects.sync(client=client)
    if result is None:
        click.echo("Error: API に接続できません", err=True)
        sys.exit(1)
    if not result:
        click.echo("(プロジェクトなし)")
        return
    for p in result:
        click.echo(f"  {p.name}  {p.color}")


@cli.command("add-project")
@click.argument("name")
@click.option("--color", "-c", default=None, help="色コード (例: #ff9800)")
@click.pass_context
def add_project(ctx, name: str, color: str | None):
    """プロジェクトを追加"""
    client = _client(ctx)
    body = ProjectCreate(name=name)
    if color:
        body.color = color
    resp = post_api_projects.sync_detailed(client=client, body=body)
    if resp.status_code.value == 201:
        click.echo(f"追加: {name}")
    else:
        click.echo(f"Error ({resp.status_code.value}): {resp.content.decode()}", err=True)
        sys.exit(1)


# ── reports ──


@cli.command()
@click.option("--date", "-d", "date_str", default=None, help="日付 (YYYY-MM-DD, default: today)")
@click.option("--detail", is_flag=True, help="タスク内訳を表示")
@click.pass_context
def report(ctx, date_str: str | None, detail: bool):
    """日次レポート"""
    client = _client(ctx)
    kwargs = {}
    if date_str:
        kwargs["date"] = date.fromisoformat(date_str)
    if detail:
        kwargs["detail"] = GetApiReportDetail.VALUE_1
    result = get_api_report.sync(client=client, **kwargs)
    if result is None:
        click.echo("Error: API に接続できません", err=True)
        sys.exit(1)
    click.echo(f"日付: {result.date}  合計: {result.total_formatted}")
    if not isinstance(result.projects, type(UNSET)):
        _fmt_projects(result.projects, detail)


@cli.command()
@click.option("--from", "-f", "from_str", default=None, help="開始日 (YYYY-MM-DD)")
@click.option("--to", "-t", "to_str", default=None, help="終了日 (YYYY-MM-DD)")
@click.option("--since", "-s", default=None, help="直近N日 (例: 30d)")
@click.option("--detail", is_flag=True, help="タスク内訳を表示")
@click.pass_context
def reports(ctx, from_str: str | None, to_str: str | None, since: str | None, detail: bool):
    """期間集計レポート"""
    client = _client(ctx)
    kwargs = {}
    if from_str:
        kwargs["from_"] = date.fromisoformat(from_str)
    if to_str:
        kwargs["to"] = date.fromisoformat(to_str)
    if since:
        kwargs["since"] = since
    if detail:
        kwargs["detail"] = GetApiReportsDetail.VALUE_1
    result = get_api_reports.sync(client=client, **kwargs)
    if result is None:
        click.echo("Error: API に接続できません", err=True)
        sys.exit(1)
    click.echo(f"期間: {result.from_} ~ {result.to}  ({result.days_with_tasks}/{result.days}日)")
    click.echo(f"合計: {result.total_formatted}")
    if not isinstance(result.projects, type(UNSET)):
        _fmt_projects(result.projects, detail)


@cli.command("reports-by-day")
@click.option("--from", "-f", "from_str", default=None, help="開始日 (YYYY-MM-DD)")
@click.option("--to", "-t", "to_str", default=None, help="終了日 (YYYY-MM-DD)")
@click.option("--since", "-s", default=None, help="直近N日 (例: 30d)")
@click.option("--detail", is_flag=True, help="タスク内訳を表示")
@click.pass_context
def reports_by_day(ctx, from_str: str | None, to_str: str | None, since: str | None, detail: bool):
    """日別レポート"""
    client = _client(ctx)
    kwargs = {}
    if from_str:
        kwargs["from_"] = date.fromisoformat(from_str)
    if to_str:
        kwargs["to"] = date.fromisoformat(to_str)
    if since:
        kwargs["since"] = since
    if detail:
        kwargs["detail"] = GetApiReportsByDayDetail.VALUE_1
    result = get_api_reports_by_day.sync(client=client, **kwargs)
    if result is None:
        click.echo("Error: API に接続できません", err=True)
        sys.exit(1)
    click.echo(f"期間: {result.from_} ~ {result.to}  ({result.days_with_tasks}/{result.days}日)")
    click.echo(f"合計: {result.total_formatted}")
    if not isinstance(result.daily, type(UNSET)):
        for day in result.daily:
            click.echo(f"\n  {day.date}  {day.total_formatted}")
            if not isinstance(getattr(day, "projects", UNSET), type(UNSET)):
                _fmt_projects(day.projects, detail)


if __name__ == "__main__":
    cli()
