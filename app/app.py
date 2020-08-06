import asyncio
import logging
from types import AsyncGeneratorType
from typing import AsyncIterable

from aiohttp import PAYLOAD_REGISTRY
from aiohttp.web_app import Application

from app.handlers.prices import PricesView
from app.payloads import AsyncGenJSONListPayload
from app.price_updater import SkypickerProvider
from app.price_updater.periodical_price_update import PeriodicalPriceUpdateScheduler
from app.utils.client_session import setup_client_session
from app.utils.pg import setup_pg


log = logging.getLogger()

TOP_FLIGHT_DIRECTIONS = (
    ('ALA', 'TSE'),
    ('TSE', 'ALA'),
    ('ALA', 'MOW'),
    ('MOW', 'ALA'),
    ('ALA', 'CIT'),
    ('CIT', 'ALA'),
    ('TSE', 'MOW'),
    ('MOW', 'TSE'),
    ('TSE', 'LED'),
    ('LED', 'TSE'),
)

NUMBER_OF_DAYS = 30


async def update_prices_every_day(app):
    skypicker_provider = SkypickerProvider(app['client_session'])
    price_update_scheduler = PeriodicalPriceUpdateScheduler(
        pg=app['pg'],
        provider=skypicker_provider,
        directions=TOP_FLIGHT_DIRECTIONS,
        number_of_days=NUMBER_OF_DAYS
    )
    asyncio.create_task(price_update_scheduler.run())


def create_app():
    app = Application()
    app.cleanup_ctx.append(setup_pg)
    app.cleanup_ctx.append(setup_client_session)
    app.on_startup.append(update_prices_every_day)

    app.router.add_route('*', '/prices', PricesView)

    PAYLOAD_REGISTRY.register(AsyncGenJSONListPayload,
                              (AsyncGeneratorType, AsyncIterable))

    return app
