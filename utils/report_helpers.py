"""Report helper functions — aggregation, formatting, JSON conversion."""

from datetime import timedelta


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


def _aggregate_by_task(tasks):
    """Aggregate durations by task name (no project grouping)."""
    totals = {}
    for t in tasks:
        secs = (t.end_time - t.start_time).total_seconds()
        totals[t.name] = totals.get(t.name, 0) + secs
    return totals


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


def _iter_date_range(start_date, end_date):
    d = start_date
    while d <= end_date:
        yield d
        d += timedelta(days=1)
