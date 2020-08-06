import asyncio
import datetime
import logging
from typing import Tuple, List, Collection

from asyncpgsa import PG
from sqlalchemy import desc

from app.db.schema import price_updates_table, Status
from app.price_updater import PriceMonitor, AsyncAirlineTicketProvider, Flight
from app.price_updater.flight import bulk_insert_flights
from app.utils.loop import get_loop_time

log = logging.getLogger(__name__)


class PeriodicalPriceUpdateScheduler:
    """
    Class that updates flight prices and schedules updates
    """

    def __init__(self,
                 pg: PG,
                 provider: AsyncAirlineTicketProvider,
                 directions: Collection[Tuple[str, str]],
                 number_of_days: int):
        self._directions = directions
        self._number_of_days = number_of_days
        self._pg = pg
        self._updater = PriceMonitor(
            provider=provider,
            directions=directions,
            number_of_days=number_of_days,
        )

    async def run(self):
        """
        The entry method. If no price updates today was made run first update,
        otherwise just schedule next update for midnight.
        :return:
        """
        last_update = await self._get_last_update()
        if not last_update or last_update['created_at'].date() != datetime.datetime.utcnow().date():
            await self._update_prices()
        else:
            self._schedule_next_update()

    async def _update_prices(self):
        """
        Update prices and schedule new update for the midnight
        :return:
        """
        async with self._pg.transaction() as db_conn:
            price_update_id = await self._create_price_update_record(db_conn)
            flights = await self._updater.get_cheapest_flights()
            flights_saved = await self._save_flights(db_conn, flights, price_update_id)
            if flights_saved > 0:
                await self._confirm_successful_update(db_conn, price_update_id)
            else:
                await self._mark_update_failed(db_conn, price_update_id)

        # Schedule next update soon if retrieved less than 2/3 of expected number of flights
        next_update_soon = flights_saved < len(self._directions) * self._number_of_days * 2 / 3
        self._schedule_next_update(soon=next_update_soon)

    def _schedule_next_update(self, soon: bool = False):
        loop = asyncio.get_event_loop()
        if not soon:
            next_day_midnight = datetime.datetime.combine(
                date=datetime.datetime.utcnow().date() + datetime.timedelta(days=1),
                time=datetime.time(hour=0, minute=0)
            )
            call_time = get_loop_time(loop, next_day_midnight)
        else:
            call_time = loop.time() + datetime.timedelta(minutes=20).total_seconds()
        loop.call_at(call_time, asyncio.create_task, self._update_prices())
        log.info(f'Next prices update scheduled on {call_time}')

    async def _get_last_update(self):
        last_update_query = price_updates_table.select() \
            .where(price_updates_table.c.status == Status.completed.value) \
            .order_by(desc(price_updates_table.c.created_at))
        return await self._pg.fetchrow(last_update_query)

    @classmethod
    async def _create_price_update_record(cls, db_conn):
        query = price_updates_table.insert().returning(price_updates_table.c.id)
        return await db_conn.fetchval(query)

    @classmethod
    async def _save_flights(cls, db_conn, flights: List[Flight], price_update_id: int):
        log.info(f'Inserting {len(flights)} flights')
        return await bulk_insert_flights(flights, price_update_id, db_conn)

    @classmethod
    async def _confirm_successful_update(cls, db_conn, price_update_id):
        await cls._update_status(db_conn, price_update_id, Status.completed.value)

    @classmethod
    async def _mark_update_failed(cls, db_conn, price_update_id):
        await cls._update_status(db_conn, price_update_id, Status.failed.value)

    @classmethod
    async def _update_status(cls, db_conn, price_update_id, status):
        update_status = price_updates_table \
            .update() \
            .where(price_updates_table.c.id == price_update_id) \
            .values(status=status)
        await db_conn.execute(update_status)
