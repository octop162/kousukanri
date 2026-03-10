from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="Task")


@_attrs_define
class Task:
    """
    Attributes:
        id (int | Unset):  Example: 1.
        name (str | Unset):  Example: コーディング.
        start (str | Unset): HH:MM Example: 09:00.
        end (str | Unset): HH:MM Example: 10:30.
        date (datetime.date | Unset):  Example: 2026-03-10.
        color (str | Unset):  Example: #4fc3f7.
        project_id (int | None | Unset):  Example: 1.
        project (None | str | Unset):  Example: 開発.
    """

    id: int | Unset = UNSET
    name: str | Unset = UNSET
    start: str | Unset = UNSET
    end: str | Unset = UNSET
    date: datetime.date | Unset = UNSET
    color: str | Unset = UNSET
    project_id: int | None | Unset = UNSET
    project: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        start = self.start

        end = self.end

        date: str | Unset = UNSET
        if not isinstance(self.date, Unset):
            date = self.date.isoformat()

        color = self.color

        project_id: int | None | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

        project: None | str | Unset
        if isinstance(self.project, Unset):
            project = UNSET
        else:
            project = self.project

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if start is not UNSET:
            field_dict["start"] = start
        if end is not UNSET:
            field_dict["end"] = end
        if date is not UNSET:
            field_dict["date"] = date
        if color is not UNSET:
            field_dict["color"] = color
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if project is not UNSET:
            field_dict["project"] = project

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        start = d.pop("start", UNSET)

        end = d.pop("end", UNSET)

        _date = d.pop("date", UNSET)
        date: datetime.date | Unset
        if isinstance(_date, Unset):
            date = UNSET
        else:
            date = isoparse(_date).date()

        color = d.pop("color", UNSET)

        def _parse_project_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        def _parse_project(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project = _parse_project(d.pop("project", UNSET))

        task = cls(
            id=id,
            name=name,
            start=start,
            end=end,
            date=date,
            color=color,
            project_id=project_id,
            project=project,
        )

        task.additional_properties = d
        return task

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
