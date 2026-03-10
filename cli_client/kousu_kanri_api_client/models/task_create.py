from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="TaskCreate")


@_attrs_define
class TaskCreate:
    """
    Attributes:
        name (str):  Example: コーディング.
        start (str): HH:MM Example: 09:00.
        end (str): HH:MM Example: 10:30.
        date (datetime.date | Unset): 対象日 (デフォルト: 今日) Example: 2026-03-10.
        project (str | Unset): プロジェクト名 (存在するプロジェクトを指定) Example: 開発.
    """

    name: str
    start: str
    end: str
    date: datetime.date | Unset = UNSET
    project: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        start = self.start

        end = self.end

        date: str | Unset = UNSET
        if not isinstance(self.date, Unset):
            date = self.date.isoformat()

        project = self.project

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "start": start,
                "end": end,
            }
        )
        if date is not UNSET:
            field_dict["date"] = date
        if project is not UNSET:
            field_dict["project"] = project

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        start = d.pop("start")

        end = d.pop("end")

        _date = d.pop("date", UNSET)
        date: datetime.date | Unset
        if isinstance(_date, Unset):
            date = UNSET
        else:
            date = isoparse(_date).date()

        project = d.pop("project", UNSET)

        task_create = cls(
            name=name,
            start=start,
            end=end,
            date=date,
            project=project,
        )

        task_create.additional_properties = d
        return task_create

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
