from datetime import datetime, date
from decimal import Decimal

import pytest

from app.price_updater import Flight


@pytest.fixture
def mock_sleep(mocker):
    class MockAwaitable:
        def __await__(self):
            pass
    mocker.patch('asyncio.sleep', return_value=MockAwaitable)


@pytest.fixture
def simple_tse_ala_flight():
    return Flight(
        city_code_from='TSE',
        city_code_to='ALA',
        price=Decimal(123),
        departure_date=date.fromisoformat('2020-08-05'),
        booking_token='simple_tse_ala_flight_token'
    )


@pytest.fixture
def get_flights_simple_response():
    return {
        'data': [
            {
                'cityCodeFrom': 'TSE',
                'cityCodeTo': 'ALA',
                'price': 123,
                'booking_token': 'some_long_token_1',
                "dTime": int(datetime.fromisoformat('2020-08-03T00:00:00').timestamp()),
            },
            {
                'cityCodeFrom': 'TSE',
                'cityCodeTo': 'ALA',
                'price': 234,
                'booking_token': 'some_long_token_2',
                "dTime": int(datetime.fromisoformat('2020-08-03T22:04:12').timestamp()),
            },
            {
                'cityCodeFrom': 'TSE',
                'cityCodeTo': 'ALA',
                'price': 132,
                'booking_token': 'some_long_token_3',
                "dTime": int(datetime.fromisoformat('2020-08-04T00:01:56').timestamp()),
            },
            {
                'cityCodeFrom': 'TSE',
                'cityCodeTo': 'ALA',
                'price': 412,
                'booking_token': 'some_long_token_4',
                "dTime": int(datetime.fromisoformat('2020-08-05T23:59:59').timestamp()),
            }
        ]
    }


@pytest.fixture
def confirm_flight_simple_ok_response():
    return {
        'flights_checked': True,
        'flights_invalid': False,
        'price_change': False,
    }


@pytest.fixture
def confirm_flight_three_trials_confirmed():
    return [
        {
            'flights_checked': False,
            'flights_invalid': False,
            'price_change': False,
        },
        {
            'flights_checked': False,
            'flights_invalid': False,
            'price_change': False,
        },
        {
            'flights_checked': True,
            'flights_invalid': False,
            'price_change': False,
        }
    ]


@pytest.fixture
def confirm_flight_three_trials_price_changed():
    return [
        {
            'flights_checked': False,
            'flights_invalid': False,
            'price_change': False,
        },
        {
            'flights_checked': False,
            'flights_invalid': False,
            'price_change': False,
        },
        {
            'flights_checked': True,
            'flights_invalid': False,
            'price_change': True,
        }
    ]


@pytest.fixture
def confirm_flight_three_trials_flight_invalid():
    return [
        {
            'flights_checked': False,
            'flights_invalid': False,
            'price_change': False,
        },
        {
            'flights_checked': False,
            'flights_invalid': False,
            'price_change': False,
        },
        {
            'flights_checked': True,
            'flights_invalid': True,
            'price_change': False,
        }
    ]


@pytest.fixture
def default_directions():
    return (
        ('ALA', 'TSE'),
        ('TSE', 'ALA'),
        ('ALA', 'MOW'),
        ('MOW', 'ALA'),
        ('ALA', 'CIT'),
        ('CIT', 'ALA'),
        ('TSE', 'MOW'),
        ('MOW', 'TSE'),
        ('TSE', 'LED'),
        ('LED', 'TSE'),
    )
