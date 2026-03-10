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


T = TypeVar("T", bound="DailyReport")


@_attrs_define
class DailyReport:
    """
    Attributes:
        date (datetime.date | Unset):  Example: 2026-03-10.
        total_seconds (int | Unset):  Example: 28800.
        total_formatted (str | Unset):  Example: 8:00:00.
        projects (list[ProjectEntry] | Unset):
    """

    date: datetime.date | Unset = UNSET
    total_seconds: int | Unset = UNSET
    total_formatted: str | Unset = UNSET
    projects: list[ProjectEntry] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        date: str | Unset = UNSET
        if not isinstance(self.date, Unset):
            date = self.date.isoformat()

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
        if date is not UNSET:
            field_dict["date"] = date
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
        _date = d.pop("date", UNSET)
        date: datetime.date | Unset
        if isinstance(_date, Unset):
            date = UNSET
        else:
            date = isoparse(_date).date()

        total_seconds = d.pop("total_seconds", UNSET)

        total_formatted = d.pop("total_formatted", UNSET)

        _projects = d.pop("projects", UNSET)
        projects: list[ProjectEntry] | Unset = UNSET
        if _projects is not UNSET:
            projects = []
            for projects_item_data in _projects:
                projects_item = ProjectEntry.from_dict(projects_item_data)

                projects.append(projects_item)

        daily_report = cls(
            date=date,
            total_seconds=total_seconds,
            total_formatted=total_formatted,
            projects=projects,
        )

        daily_report.additional_properties = d
        return daily_report

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
