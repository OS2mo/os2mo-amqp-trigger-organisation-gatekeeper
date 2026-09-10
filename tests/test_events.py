# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0

from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from fastramqpi.ramqp.depends import get_context

from orggatekeeper.events import association_handler
from orggatekeeper.events import engagement_handler
from orggatekeeper.events import ituser_handler
from orggatekeeper.events import org_unit_handler
from orggatekeeper.main import create_app


@patch("orggatekeeper.calculate.update_line_management")
async def test_handle_engagement(
    update_line_management_mock: MagicMock, context: dict[str, Any]
) -> None:
    """Test that changes to engagements results in calls to update_line_management
    with the org_unit_uuid of an engagement.
    """
    org_unit_uuid = uuid4()
    with patch(
        "orggatekeeper.calculate.get_orgunit_from_engagement",
        return_value={org_unit_uuid},
    ):
        await engagement_handler(context, uuid4())
    update_line_management_mock.assert_called_once_with(**context, uuid=org_unit_uuid)


@patch("orggatekeeper.calculate.update_line_management")
async def test_handle_engagement_missing_uuid(
    update_line_management_mock: MagicMock, context: dict[str, Any]
) -> None:
    """Test that engagements without a matching org unit do not result in calls
    to update_line_management.
    """
    with patch(
        "orggatekeeper.calculate.get_orgunit_from_engagement",
        side_effect=ValueError,
    ):
        await engagement_handler(context, uuid4())
    update_line_management_mock.assert_not_called()


@patch("orggatekeeper.calculate.update_line_management")
async def test_handle_association(
    update_line_management_mock: MagicMock, context: dict[str, Any]
) -> None:
    """Test that changes to associations results in calls to update_line_management
    with the org_unit_uuid of an association.
    """
    with patch(
        "orggatekeeper.calculate.get_orgunit_from_association", return_value={uuid4()}
    ):
        await association_handler(context, uuid4())
    update_line_management_mock.assert_called_once()


@patch("orggatekeeper.calculate.update_line_management")
async def test_handle_association_missing_uuid(
    update_line_management_mock: MagicMock, context: dict[str, Any]
) -> None:
    """Test that associations without a matching org unit do not result in calls
    to update_line_management.
    """
    with patch(
        "orggatekeeper.calculate.get_orgunit_from_association", side_effect=ValueError
    ):
        await association_handler(context, uuid4())
    update_line_management_mock.assert_not_called()


@patch("orggatekeeper.calculate.update_line_management")
async def test_handle_ituser(
    update_line_management_mock: MagicMock, context: dict[str, Any]
) -> None:
    """Test that changes to itusers results in calls to update_line_management
    with the org_unit_uuid of an ituser.
    """
    with patch(
        "orggatekeeper.calculate.get_orgunit_from_ituser", return_value={uuid4()}
    ):
        await ituser_handler(context, uuid4())
    update_line_management_mock.assert_called_once()


@patch("orggatekeeper.calculate.update_line_management")
async def test_handle_ituser_missing_uuid(
    update_line_management_mock: MagicMock, context: dict[str, Any]
) -> None:
    """Test that itusers without a matching org unit do not result in calls
    to update_line_management.
    """
    with patch(
        "orggatekeeper.calculate.get_orgunit_from_ituser", side_effect=ValueError
    ):
        await ituser_handler(context, uuid4())
    update_line_management_mock.assert_not_called()


@patch("orggatekeeper.calculate.update_line_management")
async def test_handle_org_unit(
    update_line_management_mock: MagicMock,
    context: dict[str, Any],
) -> None:
    """Test that changes calls update line management with an org_units uuid"""
    uuid = uuid4()
    await org_unit_handler(context, uuid)
    update_line_management_mock.assert_called_once_with(**context, uuid=uuid)


@pytest.mark.parametrize(
    "path,handler_name",
    [
        ("/events/mo/org_unit", "org_unit_handler"),
        ("/events/mo/ituser", "ituser_handler"),
        ("/events/mo/association", "association_handler"),
        ("/events/mo/engagement", "engagement_handler"),
    ],
)
def test_event_endpoint_calls_handler(
    path: str,
    handler_name: str,
    context: dict[str, Any],
) -> None:
    """Test that each event endpoint hands the event subject to its handler."""
    app = create_app(
        fastramqpi={
            "client_id": "orggatekeeper",
            "client_secret": "hunter2",
            "enable_metrics": False,
        },
    )
    # The context is normally populated during the ASGI lifespan, which the
    # test client does not run.
    app.dependency_overrides[get_context] = lambda: context

    subject = uuid4()
    with patch(f"orggatekeeper.events.{handler_name}", new=AsyncMock()) as handler_mock:
        response = TestClient(app).post(
            path, json={"subject": str(subject), "priority": 10000}
        )

    assert response.status_code == 200
    handler_mock.assert_awaited_once_with(context, subject)
