import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.daily_report import DailyReport
from ...models.get_api_report_detail import GetApiReportDetail
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    date: datetime.date | Unset = UNSET,
    detail: GetApiReportDetail | Unset = GetApiReportDetail.VALUE_0,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_date: str | Unset = UNSET
    if not isinstance(date, Unset):
        json_date = date.isoformat()
    params["date"] = json_date

    json_detail: str | Unset = UNSET
    if not isinstance(detail, Unset):
        json_detail = detail.value

    params["detail"] = json_detail

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/report",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> DailyReport | None:
    if response.status_code == 200:
        response_200 = DailyReport.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[DailyReport]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    date: datetime.date | Unset = UNSET,
    detail: GetApiReportDetail | Unset = GetApiReportDetail.VALUE_0,
) -> Response[DailyReport]:
    """日次レポート

    Args:
        date (datetime.date | Unset):  Example: 2026-03-10.
        detail (GetApiReportDetail | Unset):  Default: GetApiReportDetail.VALUE_0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DailyReport]
    """

    kwargs = _get_kwargs(
        date=date,
        detail=detail,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    date: datetime.date | Unset = UNSET,
    detail: GetApiReportDetail | Unset = GetApiReportDetail.VALUE_0,
) -> DailyReport | None:
    """日次レポート

    Args:
        date (datetime.date | Unset):  Example: 2026-03-10.
        detail (GetApiReportDetail | Unset):  Default: GetApiReportDetail.VALUE_0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DailyReport
    """

    return sync_detailed(
        client=client,
        date=date,
        detail=detail,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    date: datetime.date | Unset = UNSET,
    detail: GetApiReportDetail | Unset = GetApiReportDetail.VALUE_0,
) -> Response[DailyReport]:
    """日次レポート

    Args:
        date (datetime.date | Unset):  Example: 2026-03-10.
        detail (GetApiReportDetail | Unset):  Default: GetApiReportDetail.VALUE_0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DailyReport]
    """

    kwargs = _get_kwargs(
        date=date,
        detail=detail,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    date: datetime.date | Unset = UNSET,
    detail: GetApiReportDetail | Unset = GetApiReportDetail.VALUE_0,
) -> DailyReport | None:
    """日次レポート

    Args:
        date (datetime.date | Unset):  Example: 2026-03-10.
        detail (GetApiReportDetail | Unset):  Default: GetApiReportDetail.VALUE_0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DailyReport
    """

    return (
        await asyncio_detailed(
            client=client,
            date=date,
            detail=detail,
        )
    ).parsed
