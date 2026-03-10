from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.daily_report_by_day_daily_item import DailyReportByDayDailyItem


T = TypeVar("T", bound="DailyReportByDay")


@_attrs_define
class DailyReportByDay:
    """
    Attributes:
        from_ (datetime.date | Unset):
        to (datetime.date | Unset):
        days (int | Unset):
        days_with_tasks (int | Unset):
        total_seconds (int | Unset):
        total_formatted (str | Unset):
        daily (list[DailyReportByDayDailyItem] | Unset):
    """

    from_: datetime.date | Unset = UNSET
    to: datetime.date | Unset = UNSET
    days: int | Unset = UNSET
    days_with_tasks: int | Unset = UNSET
    total_seconds: int | Unset = UNSET
    total_formatted: str | Unset = UNSET
    daily: list[DailyReportByDayDailyItem] | Unset = UNSET
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

        daily: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.daily, Unset):
            daily = []
            for daily_item_data in self.daily:
                daily_item = daily_item_data.to_dict()
                daily.append(daily_item)

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
        if daily is not UNSET:
            field_dict["daily"] = daily

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.daily_report_by_day_daily_item import DailyReportByDayDailyItem

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

        _daily = d.pop("daily", UNSET)
        daily: list[DailyReportByDayDailyItem] | Unset = UNSET
        if _daily is not UNSET:
            daily = []
            for daily_item_data in _daily:
                daily_item = DailyReportByDayDailyItem.from_dict(daily_item_data)

                daily.append(daily_item)

        daily_report_by_day = cls(
            from_=from_,
            to=to,
            days=days,
            days_with_tasks=days_with_tasks,
            total_seconds=total_seconds,
            total_formatted=total_formatted,
            daily=daily,
        )

        daily_report_by_day.additional_properties = d
        return daily_report_by_day

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
