import datetime
from enum import Enum, unique

from sqlalchemy import (
    Column, Date, Enum as PgEnum, ForeignKey, Integer,
    MetaData, String, Table, Numeric, DateTime)


convention = {
    'all_column_names': lambda constraint, table: '_'.join([
        column.name for column in constraint.columns.values()
    ]),
    'ix': 'ix__%(table_name)s__%(all_column_names)s',
    'uq': 'uq__%(table_name)s__%(all_column_names)s',
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    'fk': 'fk__%(table_name)s__%(all_column_names)s__%(referred_table_name)s',
    'pk': 'pk__%(table_name)s'
}

metadata = MetaData(naming_convention=convention)


@unique
class Status(Enum):
    pending = 'pending'
    in_process = 'in_process'
    completed = 'completed'
    failed = 'failed'


price_updates_table = Table(
    'price_updates',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('status', PgEnum(Status, name='stauts'), nullable=False, default=Status.pending.value),
    Column('created_at', DateTime, nullable=False, default=datetime.datetime.utcnow)
)

flights_table = Table(
    'flights',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('update_id', Integer, ForeignKey('price_updates.id')),
    Column('city_code_from', String(3), nullable=False),
    Column('city_code_to', String(3), nullable=False),
    Column('departure_date', Date, nullable=False),
    Column('price', Numeric(precision=10, scale=2), nullable=False),
    Column('booking_token', String, nullable=False),
)
