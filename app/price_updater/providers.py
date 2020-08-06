import abc
import asyncio
import logging
from datetime import date
from decimal import Decimal
from typing import List

from retry import retry

from .flight import Flight


log = logging.getLogger(__name__)


class AsyncAirlineTicketProvider(abc.ABC):

    async def get_flights(self, city_code_from: str, city_code_to: str,
                          date_from: date, date_to: date) -> List[Flight]:
        raise NotImplementedError

    async def confirm_flight(self, flight: Flight) -> (Flight, bool):
        raise NotImplementedError


class SkypickerProvider(AsyncAirlineTicketProvider):
    """
    Facade for Skypicker API to retrieve and confirm flights
    """

    GET_FLIGHTS_ENDPOINT = 'https://api.skypicker.com/flights?' \
                           'fly_from={city_code_from}&' \
                           'fly_to={city_code_to}&' \
                           'date_from={date_from}&' \
                           'date_to={date_to}&' \
                           'partner=picky'

    CONFIRM_FLIGHT_ENDPOINT = 'https://booking-api.skypicker.com/api/v0.1/check_flights?' \
                              'v=2&' \
                              'booking_token={booking_token}&' \
                              'bnum=0&' \
                              'pnum=1&' \
                              'affily=picky_{{market}}&' \
                              'currency=EUR&' \
                              'adults=1&' \
                              'children=0&' \
                              'infants=0'

    def __init__(self, client_session):
        self._client_session = client_session

    @retry(tries=3, delay=2)
    async def get_flights(self, city_code_from: str, city_code_to: str,
                          date_from: date, date_to: date) -> List[Flight]:
        """
        Fetches flight information for a given direction within given dates.
        :return: List of Flights which contain all available flights for all
                 the dates within a given date span
        """
        logging.info(f'Called get_flights({city_code_from}, {city_code_to}, '
                     f'{date_from}, {date_to})')
        get_flights_endpoint = self.GET_FLIGHTS_ENDPOINT.format(
            city_code_from=city_code_from,
            city_code_to=city_code_to,
            date_from=date_from.strftime('%d/%m/%Y'),
            date_to=date_to.strftime('%d/%m/%Y')
        )

        async with self._client_session.get(get_flights_endpoint) as get_flights_response:
            data = await get_flights_response.json()
        flights = []
        for flight in data['data']:
            flights.append(
                Flight(
                    city_code_from=flight['cityCodeFrom'],
                    city_code_to=flight['cityCodeTo'],
                    departure_date=date.fromtimestamp(flight['dTime']),
                    price=Decimal(flight['price']),
                    booking_token=flight['booking_token']
                )
            )
        return flights

    async def confirm_flight(self, flight: Flight) -> (Flight, bool):
        """
        Check booking confirmation and price for a given Flight.
        :return: a tuple where the first value is always a Flight,
                 the second value is True iff flight is valid
                 and price didn't change
        """
        log.info(f'Checking {flight}')
        confirm_flight_endpoint = self.CONFIRM_FLIGHT_ENDPOINT.format(
            booking_token=flight.booking_token
        )

        flights_checked = False
        while not flights_checked:
            try:
                async with self._client_session.get(confirm_flight_endpoint) as confirm_flight_response:
                    data = await confirm_flight_response.json(content_type='text/html')
            except Exception:
                return flight, False
            flights_checked = data.get('flights_checked', False)
            if not flights_checked:
                await asyncio.sleep(5)

        if data['flights_invalid'] or data['price_change']:
            return flight, False

        return flight, True
