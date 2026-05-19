"""
Startup ingestion switcher: mock scenario vs live external APIs.
"""

from __future__ import annotations

import logging

from app.core.config import settings
from app.services.live_ingestion import seed_live_signals
from app.services.mock_engine import seed_hackathon_scenario, build_default_inventory
from app.store import store

logger = logging.getLogger("ciro.ingestion")
logger.setLevel(logging.INFO)


async def seed_startup_data() -> None:
    if settings.USE_LIVE_APIS:
        inventory = build_default_inventory()
        await store.set_inventory(inventory)
        count = await seed_live_signals()
        if count == 0:
            logger.warning("Live ingestion produced no signals; falling back to mock scenario data.")
            await seed_hackathon_scenario()
        return

    await seed_hackathon_scenario()
