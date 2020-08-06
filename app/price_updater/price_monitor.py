import asyncio
import logging
import operator
from functools import reduce
from typing import List, Tuple, Iterable
from datetime import datetime, timedelta

from app.price_updater.providers import AsyncAirlineTicketProvider
from .flight import Flight

log = logging.getLogger(__name__)


class PriceMonitor:
    """
    Class for retrieving cheapest tickets through provider
    for given directions in a given date span from today.
    """

    def __init__(self,
                 provider: AsyncAirlineTicketProvider,
                 number_of_days: int,
                 directions: Iterable[Tuple[str, str]]):
        self.provider = provider
        self.number_of_days = number_of_days
        self.directions = directions

    async def get_cheapest_flights(self) -> List[Flight]:
        """
        Method to get cheapest prices for top flights within a month
        """
        date_from, date_to = self._get_date_span()

        log.info(f'Started cheapest prices update in {date_from} {date_to} for:')
        for src, dst in self.directions:
            log.info(f'{src} -> {dst}')

        cheapest_flights = await self._get_cheapest_flights_for_all_directions(date_from, date_to)
        confirmed_flights = await self._confirm_flights(cheapest_flights)

        return confirmed_flights

    def _get_date_span(self) -> (str, str):
        date_from = datetime.today().date()
        date_to = (datetime.today() + timedelta(days=self.number_of_days)).date()
        return date_from, date_to

    async def _get_cheapest_flights_for_all_directions(self,
                                                       date_from: datetime.date,
                                                       date_to: datetime.date) -> List[Flight]:
        """
        Schedules coroutines to get cheapest prices for each direction within
        given dates.
        :return: List of Flights with minimal cost
        """
        get_cheapest_flights_coros = []
        for city_code_from, city_code_to in self.directions:
            get_cheapest_flights_coros.append(
                self._get_cheapest_flights_for_a_direction(
                    city_code_from=city_code_from,
                    city_code_to=city_code_to,
                    date_from=date_from,
                    date_to=date_to
                )
            )
        cheapest_flights = await asyncio.gather(*get_cheapest_flights_coros)
        return reduce(operator.concat, cheapest_flights)

    async def _get_cheapest_flights_for_a_direction(self,
                                                    city_code_from: str,
                                                    city_code_to: str,
                                                    date_from: datetime.date,
                                                    date_to: datetime.date) -> List[Flight]:
        """
        Retrieves a list of flights available for a given direction and time period.
        Then selects flights with minimal cost.
        :return: List of Flights with only one cheapest Flight for a direction per date
        """
        try:
            all_flights = await self.provider.get_flights(
                city_code_from=city_code_from,
                city_code_to=city_code_to,
                date_from=date_from,
                date_to=date_to
            )
        except Exception:
            return []
        actual_flights = self._filter_outliers(all_flights, date_from, date_to)
        cheapest_flights = self._get_cheapest_flight_for_each_date(actual_flights)
        return cheapest_flights

    @classmethod
    def _get_cheapest_flight_for_each_date(cls, flights: List[Flight]) -> List[Flight]:
        """
        Form a List of Flights for one direction where multiple flights at same date
        might occur, return List of Flights where only one cheapest Flight per date
        exists.
        """
        result = {}
        for flight in flights:
            if flight.departure_date not in result or flight.price < result[flight.departure_date].price:
                result[flight.departure_date] = flight
        return list(result.values())

    @classmethod
    def _filter_outliers(cls, flights, date_from, date_to):
        result = []
        for flight in flights:
            if date_from <= flight.departure_date <= date_to:
                result.append(flight)
        return result

    async def _confirm_flights(self, flights: List[Flight], retries: int = 0):
        """
        Confirm given flights using provider API.
        Retry to get cheapest price for Flight that is not confirmed.
        If retries number reached 3, then assume that flights are not available.
        :return: List of confirmed Flights
        """
        if len(flights) == 0 or retries == 3:
            return []
        log.info(f'Trying to confirm {len(flights)} flights')
        confirm_flight_coros = []
        for flight in flights:
            confirm_flight_coros.append(self.provider.confirm_flight(flight))
        confirm_flight_results = await asyncio.gather(*confirm_flight_coros)

        # Split confirmed flights and flights that need to retry to find cheapest cost
        confirmed_flights = []
        retry_get_cheapest_flight_list = []
        for flight, confirmed in confirm_flight_results:
            if confirmed:
                confirmed_flights.append(flight)
            else:
                retry_get_cheapest_flight_list.append(
                    self._get_cheapest_flights_for_a_direction(
                        flight.city_code_from,
                        flight.city_code_to,
                        flight.departure_date,
                        flight.departure_date
                    )
                )

        log.info(f'{len(confirmed_flights)} flights confirmed, {len(retry_get_cheapest_flight_list)} need to retry')

        # Retry cheapest cost find for unconfirmed Flights and add confirmed Flights
        # to the result list
        retried_flights_requests = await asyncio.gather(*retry_get_cheapest_flight_list)
        retried_flights_requests = reduce(operator.concat, retried_flights_requests, [])
        confirmed_flights.extend(await self._confirm_flights(retried_flights_requests, retries + 1))

        return confirmed_flights
