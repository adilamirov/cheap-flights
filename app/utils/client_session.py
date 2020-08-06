import logging

from aiohttp import ClientSession
from aiohttp.abc import Application


log = logging.getLogger(__name__)


async def setup_client_session(app: Application):
    log.info('Creating aiohttp.ClientSession')

    app['client_session'] = ClientSession(
        headers={'Accept': 'application/json'}
    )

    try:
        yield
    finally:
        log.info('Closing ClientSession')
        await app['client_session'].close()
        log.info('ClientSession closed')
