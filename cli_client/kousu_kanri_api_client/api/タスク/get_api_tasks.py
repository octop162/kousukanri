import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_api_tasks_simple import GetApiTasksSimple
from ...models.task import Task
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    date: datetime.date | Unset = UNSET,
    simple: GetApiTasksSimple | Unset = GetApiTasksSimple.VALUE_0,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_date: str | Unset = UNSET
    if not isinstance(date, Unset):
        json_date = date.isoformat()
    params["date"] = json_date

    json_simple: str | Unset = UNSET
    if not isinstance(simple, Unset):
        json_simple = simple.value

    params["simple"] = json_simple

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/tasks",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> list[Task] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = Task.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[list[Task]]:
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
    simple: GetApiTasksSimple | Unset = GetApiTasksSimple.VALUE_0,
) -> Response[list[Task]]:
    """タスク一覧

    Args:
        date (datetime.date | Unset):  Example: 2026-03-10.
        simple (GetApiTasksSimple | Unset):  Default: GetApiTasksSimple.VALUE_0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[Task]]
    """

    kwargs = _get_kwargs(
        date=date,
        simple=simple,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    date: datetime.date | Unset = UNSET,
    simple: GetApiTasksSimple | Unset = GetApiTasksSimple.VALUE_0,
) -> list[Task] | None:
    """タスク一覧

    Args:
        date (datetime.date | Unset):  Example: 2026-03-10.
        simple (GetApiTasksSimple | Unset):  Default: GetApiTasksSimple.VALUE_0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[Task]
    """

    return sync_detailed(
        client=client,
        date=date,
        simple=simple,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    date: datetime.date | Unset = UNSET,
    simple: GetApiTasksSimple | Unset = GetApiTasksSimple.VALUE_0,
) -> Response[list[Task]]:
    """タスク一覧

    Args:
        date (datetime.date | Unset):  Example: 2026-03-10.
        simple (GetApiTasksSimple | Unset):  Default: GetApiTasksSimple.VALUE_0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[Task]]
    """

    kwargs = _get_kwargs(
        date=date,
        simple=simple,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    date: datetime.date | Unset = UNSET,
    simple: GetApiTasksSimple | Unset = GetApiTasksSimple.VALUE_0,
) -> list[Task] | None:
    """タスク一覧

    Args:
        date (datetime.date | Unset):  Example: 2026-03-10.
        simple (GetApiTasksSimple | Unset):  Default: GetApiTasksSimple.VALUE_0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[Task]
    """

    return (
        await asyncio_detailed(
            client=client,
            date=date,
            simple=simple,
        )
    ).parsed
