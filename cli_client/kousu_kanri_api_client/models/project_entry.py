from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.project_entry_tasks_item import ProjectEntryTasksItem


T = TypeVar("T", bound="ProjectEntry")


@_attrs_define
class ProjectEntry:
    """
    Attributes:
        name (str | Unset):  Example: 開発.
        seconds (float | Unset):  Example: 5400.
        formatted (str | Unset):  Example: 1:30:00.
        tasks (list[ProjectEntryTasksItem] | Unset): detail=1 の場合のみ
    """

    name: str | Unset = UNSET
    seconds: float | Unset = UNSET
    formatted: str | Unset = UNSET
    tasks: list[ProjectEntryTasksItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        seconds = self.seconds

        formatted = self.formatted

        tasks: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.tasks, Unset):
            tasks = []
            for tasks_item_data in self.tasks:
                tasks_item = tasks_item_data.to_dict()
                tasks.append(tasks_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if seconds is not UNSET:
            field_dict["seconds"] = seconds
        if formatted is not UNSET:
            field_dict["formatted"] = formatted
        if tasks is not UNSET:
            field_dict["tasks"] = tasks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.project_entry_tasks_item import ProjectEntryTasksItem

        d = dict(src_dict)
        name = d.pop("name", UNSET)

        seconds = d.pop("seconds", UNSET)

        formatted = d.pop("formatted", UNSET)

        _tasks = d.pop("tasks", UNSET)
        tasks: list[ProjectEntryTasksItem] | Unset = UNSET
        if _tasks is not UNSET:
            tasks = []
            for tasks_item_data in _tasks:
                tasks_item = ProjectEntryTasksItem.from_dict(tasks_item_data)

                tasks.append(tasks_item)

        project_entry = cls(
            name=name,
            seconds=seconds,
            formatted=formatted,
            tasks=tasks,
        )

        project_entry.additional_properties = d
        return project_entry

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
