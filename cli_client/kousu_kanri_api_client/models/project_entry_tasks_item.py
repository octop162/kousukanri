from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProjectEntryTasksItem")


@_attrs_define
class ProjectEntryTasksItem:
    """
    Attributes:
        name (str | Unset):  Example: コーディング.
        seconds (float | Unset):  Example: 5400.
        formatted (str | Unset):  Example: 1:30:00.
    """

    name: str | Unset = UNSET
    seconds: float | Unset = UNSET
    formatted: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        seconds = self.seconds

        formatted = self.formatted

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if seconds is not UNSET:
            field_dict["seconds"] = seconds
        if formatted is not UNSET:
            field_dict["formatted"] = formatted

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        seconds = d.pop("seconds", UNSET)

        formatted = d.pop("formatted", UNSET)

        project_entry_tasks_item = cls(
            name=name,
            seconds=seconds,
            formatted=formatted,
        )

        project_entry_tasks_item.additional_properties = d
        return project_entry_tasks_item

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
