# Lowest Flight Ticket Prices Monitor

## Run

`docker-compose up`

## Request example

GET `http://localhost:8080/prices?city_from=TSE&city_to=ALA`

## Run tests

First install dependencies (`pip install -r requirements_dev.txt`).

Then run `pytest`: `python -m pytest`