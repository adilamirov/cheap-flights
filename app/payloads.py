import json
from datetime import date
from decimal import Decimal
from functools import singledispatch, partial

from aiohttp import Payload
from asyncpg.protocol.protocol import Record


@singledispatch
def convert(value):
    raise TypeError(f'Unserializable value: {value!r}')


@convert.register(Record)
def convert_asyncpg_record(value: Record):
    return dict(value)


@convert.register(date)
def convert_date(value: date):
    return value.isoformat()


@convert.register(Decimal)
def convert_decimal(value: Decimal):
    return float(value)


dumps = partial(json.dumps, default=convert, ensure_ascii=False)


class AsyncGenJSONListPayload(Payload):
    """
    Итерируется по объектам AsyncIterable, частями сериализует данные из них
    в JSON и отправляет клиенту.
    """
    def __init__(self, value, encoding: str = 'utf-8',
                 content_type: str = 'application/json',
                 root_object: str = 'data',
                 *args, **kwargs):
        self.root_object = root_object
        super().__init__(value, content_type=content_type, encoding=encoding,
                         *args, **kwargs)

    async def write(self, writer):
        await writer.write(
            ('{"%s":[' % self.root_object).encode(self._encoding)
        )

        first = True
        async for row in self._value:
            if not first:
                await writer.write(b',')
            else:
                first = False

            await writer.write(dumps(row).encode(self._encoding))

        await writer.write(b']}')
