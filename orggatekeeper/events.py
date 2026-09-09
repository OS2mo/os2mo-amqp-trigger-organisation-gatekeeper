# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0

from uuid import UUID

import structlog
from fastapi import APIRouter
from fastramqpi.events import Event
from fastramqpi.ramqp.depends import Context

from . import calculate

events_router = APIRouter()

logger = structlog.stdlib.get_logger()


async def org_unit_handler(context: Context, org_unit_uuid: UUID) -> None:
    """Callback to check org_unit_hierarchy.

    Listens to changes on org_units and it-accounts on org_units.
    """

    logger.info("Changes to org_unit or its it-accounts", org_unit=org_unit_uuid)
    await calculate.update_line_management(**context, uuid=org_unit_uuid)


async def ituser_handler(context: Context, ituser_uuid: UUID) -> None:
    """Callback to check org_unit_hierarchy on changes to it-users."""
    try:
        org_units = await calculate.get_orgunit_from_ituser(
            context["legacy_graphql_session"], ituser_uuid
        )
    except ValueError:
        logger.debug("ITUser not found", ituser=ituser_uuid)
        return
    logger.info("Changes to it-user. Checking org_units", org_unit=org_units)
    await calculate.update(context, org_units)


async def association_handler(context: Context, association_uuid: UUID) -> None:
    """Callback to check org_unit_hierarchy on changes to associations."""
    try:
        org_units = await calculate.get_orgunit_from_association(
            context["legacy_graphql_session"], association_uuid
        )
    except ValueError:
        logger.debug("Association not found", association=association_uuid)
        return
    logger.info("Changes to association. Checking org_units", org_unit=org_units)
    await calculate.update(context, org_units)


async def engagement_handler(context: Context, engagement_uuid: UUID) -> None:
    """Callback to check org_unit_hierarchy on changes to engagements."""
    try:
        org_units = await calculate.get_orgunit_from_engagement(
            context["legacy_graphql_session"], engagement_uuid
        )
    except ValueError:
        logger.debug("Engagement not found", engagement=engagement_uuid)
        return
    logger.info("Changes to engagement. Checking org_units", org_unit=org_units)
    await calculate.update(context, org_units)


@events_router.post("/events/mo/org_unit")
async def _org_unit_event(context: Context, event: Event[UUID]) -> None:
    logger.info("Received org_unit event", org_unit_event=event.dict())
    await org_unit_handler(context, event.subject)


@events_router.post("/events/mo/ituser")
async def _ituser_event(context: Context, event: Event[UUID]) -> None:
    logger.info("Received ituser event", ituser_event=event.dict())
    await ituser_handler(context, event.subject)


@events_router.post("/events/mo/association")
async def _association_event(context: Context, event: Event[UUID]) -> None:
    logger.info("Received association event", association_event=event.dict())
    await association_handler(context, event.subject)


@events_router.post("/events/mo/engagement")
async def _engagement_event(context: Context, event: Event[UUID]) -> None:
    logger.info("Received engagement event", engagement_event=event.dict())
    await engagement_handler(context, event.subject)
