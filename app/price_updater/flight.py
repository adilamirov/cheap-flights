import logging
from datetime import date
from decimal import Decimal
from typing import Dict, Any, List

from app.db.schema import flights_table


logger = logging.getLogger(__name__)


class Flight:
    __slots__ = ('city_code_from', 'city_code_to', 'departure_date', 'price', 'booking_token')

    def __init__(self,
                 city_code_from: str,
                 city_code_to: str,
                 departure_date: date,
                 price: Decimal,
                 booking_token: str):
        self.city_code_from = city_code_from
        self.city_code_to = city_code_to
        self.departure_date = departure_date
        self.price = price
        self.booking_token = booking_token

    def __repr__(self):
        return f'<Flight: {self.city_code_from} → {self.city_code_to} @ {self.departure_date} €{self.price}>'


async def bulk_insert_flights(flights: List[Flight], price_update_id: int, db_conn):
    if len(flights) == 0:
        return 0
    query = flights_table.insert()
    values = []
    for flight in flights:
        values.append(get_flight_values_to_insert(flight, price_update_id))
    result = await db_conn.execute(query.values(values))
    # return number of inserted rows
    return int(result.split(' ')[-1])


def get_flight_values_to_insert(flight: Flight, price_update_id: int) -> Dict[str, Any]:
    values = {slot: getattr(flight, slot) for slot in flight.__slots__}
    values['update_id'] = price_update_id
    return values
