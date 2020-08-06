import random
from datetime import date
from decimal import Decimal
from typing import List

from app.price_updater import AsyncAirlineTicketProvider, Flight


class MockResponse:
    def __init__(self, json, status):
        self._json = json
        self.status = status

    async def json(self, *args, **kwargs):
        return self._json

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self


class FileBasedAirlineTicketProvider(AsyncAirlineTicketProvider):
    def __init__(self, raw_flights_data):
        self._raw_flights_data = raw_flights_data

    async def get_flights(self, city_code_from: str, city_code_to: str,
                          date_from: date, date_to: date) -> List[Flight]:
        flights = []
        for flight in self._raw_flights_data['data']:
            flight_date = date.fromtimestamp(flight['dTime'])
            if date_from <= flight_date <= date_to:
                flights.append(
                    Flight(city_code_from=flight['cityCodeFrom'],
                           city_code_to=flight['cityCodeTo'],
                           departure_date=flight_date,
                           price=Decimal(flight['price']),
                           booking_token=flight['booking_token'])
                )
        return flights

    async def confirm_flight(self, flight: Flight) -> (Flight, bool):
        return flight, True


class UnstableFileBasedAirlineTicketProvider(FileBasedAirlineTicketProvider):

    def __init__(self, raw_flights_data):
        super().__init__(raw_flights_data)
        self.confirm_calls = 0

    async def confirm_flight(self, flight: Flight) -> (Flight, bool):
        self.confirm_calls += 1
        return flight, bool(random.randint(0, 1))
