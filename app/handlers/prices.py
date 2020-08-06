from http import HTTPStatus

from aiohttp.web_response import Response
from aiohttp.web_urldispatcher import View
from sqlalchemy import desc

from app.db.schema import price_updates_table, Status, flights_table
from app.utils.pg import SelectQuery


class PricesView(View):

    async def get(self):
        city_from = self.request.query.get('city_from', None)
        city_to = self.request.query.get('city_to', None)

        last_update = await self._get_last_update()
        if not last_update:
            return Response(status=HTTPStatus.ACCEPTED)

        body = SelectQuery(self._get_flights_query(city_from, city_to, last_update['id']),
                           self.request.app['pg'].transaction())

        return Response(body=body)

    async def _get_last_update(self):
        last_update_query = price_updates_table.select() \
            .where(price_updates_table.c.status == Status.completed.value) \
            .order_by(desc(price_updates_table.c.created_at))
        return await self.request.app['pg'].fetchrow(last_update_query)

    @classmethod
    def _get_flights_query(cls, city_from, city_to, update_id):
        query = flights_table.select()\
            .where(flights_table.c.update_id == update_id)
        if city_from:
            query = query.where(flights_table.c.city_code_from == city_from)
        if city_to:
            query = query.where(flights_table.c.city_code_to == city_to)
        return query
