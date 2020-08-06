import logging
import os

from aiohttp.web import run_app
from aiomisc.log import basic_config

from app.app import create_app

LOG_LEVEL = os.getenv('LOG_LEVEL', logging.INFO)
LOG_FORMAT = os.getenv('LOG_FORMAT', 'color')


def main():
    basic_config(LOG_LEVEL, LOG_FORMAT, buffered=True)
    app = create_app()
    run_app(app)


if __name__ == '__main__':
    main()
