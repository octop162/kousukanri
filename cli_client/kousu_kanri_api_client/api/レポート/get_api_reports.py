import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_api_reports_detail import GetApiReportsDetail
from ...models.period_report import PeriodReport
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    from_: datetime.date | Unset = UNSET,
    to: datetime.date | Unset = UNSET,
    since: str | Unset = UNSET,
    detail: GetApiReportsDetail | Unset = GetApiReportsDetail.VALUE_0,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_from_: str | Unset = UNSET
    if not isinstance(from_, Unset):
        json_from_ = from_.isoformat()
    params["from"] = json_from_

    json_to: str | Unset = UNSET
    if not isinstance(to, Unset):
        json_to = to.isoformat()
    params["to"] = json_to

    params["since"] = since

    json_detail: str | Unset = UNSET
    if not isinstance(detail, Unset):
        json_detail = detail.value

    params["detail"] = json_detail

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/reports",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> PeriodReport | None:
    if response.status_code == 200:
        response_200 = PeriodReport.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[PeriodReport]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    from_: datetime.date | Unset = UNSET,
    to: datetime.date | Unset = UNSET,
    since: str | Unset = UNSET,
    detail: GetApiReportsDetail | Unset = GetApiReportsDetail.VALUE_0,
) -> Response[PeriodReport]:
    """期間集計レポート

    Args:
        from_ (datetime.date | Unset):
        to (datetime.date | Unset):
        since (str | Unset):  Example: 30d.
        detail (GetApiReportsDetail | Unset):  Default: GetApiReportsDetail.VALUE_0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PeriodReport]
    """

    kwargs = _get_kwargs(
        from_=from_,
        to=to,
        since=since,
        detail=detail,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    from_: datetime.date | Unset = UNSET,
    to: datetime.date | Unset = UNSET,
    since: str | Unset = UNSET,
    detail: GetApiReportsDetail | Unset = GetApiReportsDetail.VALUE_0,
) -> PeriodReport | None:
    """期間集計レポート

    Args:
        from_ (datetime.date | Unset):
        to (datetime.date | Unset):
        since (str | Unset):  Example: 30d.
        detail (GetApiReportsDetail | Unset):  Default: GetApiReportsDetail.VALUE_0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PeriodReport
    """

    return sync_detailed(
        client=client,
        from_=from_,
        to=to,
        since=since,
        detail=detail,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    from_: datetime.date | Unset = UNSET,
    to: datetime.date | Unset = UNSET,
    since: str | Unset = UNSET,
    detail: GetApiReportsDetail | Unset = GetApiReportsDetail.VALUE_0,
) -> Response[PeriodReport]:
    """期間集計レポート

    Args:
        from_ (datetime.date | Unset):
        to (datetime.date | Unset):
        since (str | Unset):  Example: 30d.
        detail (GetApiReportsDetail | Unset):  Default: GetApiReportsDetail.VALUE_0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PeriodReport]
    """

    kwargs = _get_kwargs(
        from_=from_,
        to=to,
        since=since,
        detail=detail,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    from_: datetime.date | Unset = UNSET,
    to: datetime.date | Unset = UNSET,
    since: str | Unset = UNSET,
    detail: GetApiReportsDetail | Unset = GetApiReportsDetail.VALUE_0,
) -> PeriodReport | None:
    """期間集計レポート

    Args:
        from_ (datetime.date | Unset):
        to (datetime.date | Unset):
        since (str | Unset):  Example: 30d.
        detail (GetApiReportsDetail | Unset):  Default: GetApiReportsDetail.VALUE_0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PeriodReport
    """

    return (
        await asyncio_detailed(
            client=client,
            from_=from_,
            to=to,
            since=since,
            detail=detail,
        )
    ).parsed
