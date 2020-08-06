from datetime import date

import pytest
from aiohttp import ClientSession

from app.price_updater import SkypickerProvider
from tests.helpers import MockResponse


@pytest.mark.asyncio
async def test_get_flights(mocker, get_flights_simple_response):
    resp = MockResponse(get_flights_simple_response, 200)

    mocker.patch('aiohttp.ClientSession.get',
                 return_value=resp)

    async with ClientSession() as client_session:
        skypicker = SkypickerProvider(client_session)
        flights = await skypicker.get_flights(
            'TSE',
            'ALA',
            date.fromisoformat('2020-08-03'),
            date.fromisoformat('2020-09-03')
        )

    assert len(flights) == len(get_flights_simple_response['data'])

    for flight in flights:
        for data in get_flights_simple_response['data']:
            if (data['cityCodeFrom'] == flight.city_code_from and
                    data['cityCodeTo'] == flight.city_code_to and
                    data['price'] == flight.price and
                    data['booking_token'] == flight.booking_token and
                    date.fromtimestamp(data['dTime']) == flight.departure_date):
                break
        else:
            assert 'SkypickerProvider returned Flight which was not presented in original data'


@pytest.mark.asyncio
async def test_get_flights_endpoint(mocker):
    empty_response = MockResponse({'data': []}, 200)
    mock_get = mocker.patch('aiohttp.ClientSession.get',
                            return_value=empty_response)
    async with ClientSession() as client_session:
        skypicker = SkypickerProvider(client_session)
        await skypicker.get_flights(
            'TSE',
            'ALA',
            date.fromisoformat('2020-08-03'),
            date.fromisoformat('2020-09-03')
        )
    valid_endpoint = 'https://api.skypicker.com/flights?' \
                     'fly_from=TSE&' \
                     'fly_to=ALA&' \
                     'date_from=03/08/2020&' \
                     'date_to=03/09/2020&' \
                     'partner=picky'
    mock_get.assert_called_with(valid_endpoint)


@pytest.mark.asyncio
async def test_confirm_flight_ok(mocker,
                                 simple_tse_ala_flight,
                                 confirm_flight_simple_ok_response):
    ok_response = MockResponse(confirm_flight_simple_ok_response, 200)
    mock_get = mocker.patch('aiohttp.ClientSession.get',
                            return_value=ok_response)

    async with ClientSession() as client_session:
        skypicker = SkypickerProvider(client_session)
        flight, confirmed = await skypicker.confirm_flight(simple_tse_ala_flight)

    mock_get.assert_called_once()
    assert flight == simple_tse_ala_flight
    assert confirmed


@pytest.mark.asyncio
async def test_confirm_flight_retries_confirmed(mocker, mock_sleep,
                                                simple_tse_ala_flight,
                                                confirm_flight_three_trials_confirmed):
    responses = [MockResponse(response, 200) for response in confirm_flight_three_trials_confirmed]
    mock_get = mocker.patch('aiohttp.ClientSession.get', side_effect=responses)

    async with ClientSession() as client_session:
        skypicker = SkypickerProvider(client_session)
        flight, confirmed = await skypicker.confirm_flight(simple_tse_ala_flight)

    assert mock_get.call_count == len(confirm_flight_three_trials_confirmed)
    assert flight == simple_tse_ala_flight
    assert confirmed


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'confirm_flight_responses',
    [
        pytest.lazy_fixture('confirm_flight_three_trials_price_changed'),
        pytest.lazy_fixture('confirm_flight_three_trials_flight_invalid')
    ]
)
async def test_confirm_flight_retries_not_confirmed(mocker, mock_sleep,
                                                    simple_tse_ala_flight,
                                                    confirm_flight_responses):
    responses = [MockResponse(response, 200) for response in confirm_flight_responses]
    mock_get = mocker.patch('aiohttp.ClientSession.get',
                            side_effect=responses)

    async with ClientSession() as client_session:
        skypicker = SkypickerProvider(client_session)
        flight, confirmed = await skypicker.confirm_flight(simple_tse_ala_flight)

    assert mock_get.call_count == len(confirm_flight_responses)
    assert flight == simple_tse_ala_flight
    assert not confirmed
