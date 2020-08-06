import asyncio
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import call

import asynctest
import pytest
from freezegun import freeze_time

from app.price_updater import PriceMonitor, SkypickerProvider
from tests.helpers import FileBasedAirlineTicketProvider, UnstableFileBasedAirlineTicketProvider


@pytest.mark.asyncio
async def test_price_monitor_cheapest():
    base_dir = Path(__file__).parent
    with open(base_dir / 'fixture_data' / 'get_flights.json', 'r') as get_flights_file:
        raw_flights_data = json.load(get_flights_file)

    provider = FileBasedAirlineTicketProvider(raw_flights_data)
    price_monitor = PriceMonitor(provider=provider,
                                 number_of_days=30,
                                 directions=(('TSE', 'ALA'),))

    cheapest_flights = await price_monitor.get_cheapest_flights()

    for cheapest_flight in cheapest_flights:
        for flight in raw_flights_data['data']:
            flight_departure_date = date.fromtimestamp(flight['dTime'])
            if (cheapest_flight.departure_date == flight_departure_date and
                    cheapest_flight.price > Decimal(flight['price'])):
                assert f'There is a flight at {flight_departure_date} that is cheaper than monitor found'


@pytest.mark.asyncio
@freeze_time('2020-01-01')
async def test_price_monitor_calls_get_flights_with_proper_args(simple_tse_ala_flight,
                                                                default_directions):

    skypicker_patched = asynctest.MagicMock(SkypickerProvider(None))
    skypicker_patched.get_flights = asynctest.CoroutineMock(return_value=[simple_tse_ala_flight])
    skypicker_patched.confirm_flight = asynctest.CoroutineMock(return_value=(simple_tse_ala_flight, True))

    price_monitor = PriceMonitor(provider=skypicker_patched,
                                 number_of_days=30,
                                 directions=default_directions)

    await price_monitor.get_cheapest_flights()

    date_from = date.fromisoformat('2020-01-01')
    date_to = date.fromisoformat('2020-01-31')
    get_flights_calls = [
        call(
            city_code_from=city_code_from,
            city_code_to=city_code_to,
            date_from=date_from,
            date_to=date_to
        ) for city_code_from, city_code_to in default_directions
    ]
    skypicker_patched.get_flights.assert_has_awaits(get_flights_calls, any_order=True)


@pytest.mark.asyncio
async def test_price_monitor_calls_confirm_flights_with_proper_args():
    base_dir = Path(__file__).parent
    with open(base_dir / 'fixture_data' / 'get_flights.json', 'r') as get_flights_file:
        raw_flights_data = json.load(get_flights_file)

    provider = FileBasedAirlineTicketProvider(raw_flights_data)
    provider.confirm_flight = asynctest.CoroutineMock(side_effect=provider.confirm_flight)

    price_monitor = PriceMonitor(provider=provider,
                                 number_of_days=30,
                                 directions=(('TSE', 'ALA'),))
    cheapest_flights = await price_monitor.get_cheapest_flights()

    provider.confirm_flight.assert_has_awaits([call(flight) for flight in cheapest_flights])


@pytest.mark.asyncio
async def test_price_monitor_retries_unconfirmed_flights(mock_sleep):
    base_dir = Path(__file__).parent
    with open(base_dir / 'fixture_data' / 'get_flights.json', 'r') as get_flights_file:
        raw_flights_data = json.load(get_flights_file)

    provider = UnstableFileBasedAirlineTicketProvider(raw_flights_data)
    provider.confirm_flight = asynctest.CoroutineMock(side_effect=provider.confirm_flight)

    price_monitor = PriceMonitor(provider=provider,
                                 number_of_days=30,
                                 directions=(('TSE', 'ALA'),))
    await price_monitor.get_cheapest_flights()

    assert provider.confirm_flight.await_count == provider.confirm_calls
