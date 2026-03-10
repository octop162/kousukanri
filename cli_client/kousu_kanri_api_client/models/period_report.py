from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.project_entry import ProjectEntry


T = TypeVar("T", bound="PeriodReport")


@_attrs_define
class PeriodReport:
    """
    Attributes:
        from_ (datetime.date | Unset):
        to (datetime.date | Unset):
        days (int | Unset): 期間の日数
        days_with_tasks (int | Unset): タスクが存在する日数
        total_seconds (int | Unset):
        total_formatted (str | Unset):
        projects (list[ProjectEntry] | Unset):
    """

    from_: datetime.date | Unset = UNSET
    to: datetime.date | Unset = UNSET
    days: int | Unset = UNSET
    days_with_tasks: int | Unset = UNSET
    total_seconds: int | Unset = UNSET
    total_formatted: str | Unset = UNSET
    projects: list[ProjectEntry] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from_: str | Unset = UNSET
        if not isinstance(self.from_, Unset):
            from_ = self.from_.isoformat()

        to: str | Unset = UNSET
        if not isinstance(self.to, Unset):
            to = self.to.isoformat()

        days = self.days

        days_with_tasks = self.days_with_tasks

        total_seconds = self.total_seconds

        total_formatted = self.total_formatted

        projects: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.projects, Unset):
            projects = []
            for projects_item_data in self.projects:
                projects_item = projects_item_data.to_dict()
                projects.append(projects_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if from_ is not UNSET:
            field_dict["from"] = from_
        if to is not UNSET:
            field_dict["to"] = to
        if days is not UNSET:
            field_dict["days"] = days
        if days_with_tasks is not UNSET:
            field_dict["days_with_tasks"] = days_with_tasks
        if total_seconds is not UNSET:
            field_dict["total_seconds"] = total_seconds
        if total_formatted is not UNSET:
            field_dict["total_formatted"] = total_formatted
        if projects is not UNSET:
            field_dict["projects"] = projects

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.project_entry import ProjectEntry

        d = dict(src_dict)
        _from_ = d.pop("from", UNSET)
        from_: datetime.date | Unset
        if isinstance(_from_, Unset):
            from_ = UNSET
        else:
            from_ = isoparse(_from_).date()

        _to = d.pop("to", UNSET)
        to: datetime.date | Unset
        if isinstance(_to, Unset):
            to = UNSET
        else:
            to = isoparse(_to).date()

        days = d.pop("days", UNSET)

        days_with_tasks = d.pop("days_with_tasks", UNSET)

        total_seconds = d.pop("total_seconds", UNSET)

        total_formatted = d.pop("total_formatted", UNSET)

        _projects = d.pop("projects", UNSET)
        projects: list[ProjectEntry] | Unset = UNSET
        if _projects is not UNSET:
            projects = []
            for projects_item_data in _projects:
                projects_item = ProjectEntry.from_dict(projects_item_data)

                projects.append(projects_item)

        period_report = cls(
            from_=from_,
            to=to,
            days=days,
            days_with_tasks=days_with_tasks,
            total_seconds=total_seconds,
            total_formatted=total_formatted,
            projects=projects,
        )

        period_report.additional_properties = d
        return period_report

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
