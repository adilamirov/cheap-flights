import logging
import os
from collections import AsyncIterable
from pathlib import Path
from types import SimpleNamespace
from typing import Union

from aiohttp.web_app import Application
from alembic.config import Config
from asyncpgsa import PG
from asyncpgsa.transactionmanager import ConnectionTransactionContextManager
from sqlalchemy.sql import Select

CENSORED = '***'
DEFAULT_PG_URL = 'postgresql://postgres:postgres@localhost:5432/flights'

PROJECT_PATH = Path(__file__).parent.parent.resolve()

log = logging.getLogger(__name__)


async def setup_pg(app: Application) -> PG:
    db_info = DEFAULT_PG_URL
    log.info('Connecting to database: %s', db_info)

    app['pg'] = PG()
    await app['pg'].init(os.getenv('DATABASE_URI', DEFAULT_PG_URL))
    await app['pg'].fetchval('SELECT 1')
    log.info('Connected to database %s', db_info)

    try:
        yield
    finally:
        log.info('Disconnecting from database %s', db_info)
        await app['pg'].pool.close()
        log.info('Disconnected from database %s', db_info)


def make_alembic_config(cmd_opts: SimpleNamespace,
                        base_path: str = PROJECT_PATH) -> Config:
    if not os.path.isabs(cmd_opts.config):
        cmd_opts.config = os.path.join(base_path, cmd_opts.config)

    config = Config(file_=cmd_opts.config, ini_section=cmd_opts.name,
                    cmd_opts=cmd_opts)

    alembic_location = config.get_main_option('script_location')
    if not os.path.isabs(alembic_location):
        config.set_main_option('script_location',
                               os.path.join(base_path, alembic_location))
    if cmd_opts.pg_url:
        config.set_main_option('sqlalchemy.url', cmd_opts.pg_url)

    return config


class SelectQuery(AsyncIterable):
    __slots__ = (
        'query', 'transaction_ctx', 'timeout'
    )

    def __init__(self, query: Select,
                 transaction_ctx: ConnectionTransactionContextManager,
                 timeout: float = None):
        self.query = query
        self.transaction_ctx = transaction_ctx
        self.timeout = timeout

    async def __aiter__(self):
        async with self.transaction_ctx as conn:
            cursor = conn.cursor(self.query, timeout=self.timeout)
            async for row in cursor:
                yield row
