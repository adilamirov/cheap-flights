"""Initial migration 2

Revision ID: 061072b78dea
Revises: 26528292161a
Create Date: 2020-08-04 01:15:38.904071

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '061072b78dea'
down_revision = '26528292161a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('flights', sa.Column('booking_token', sa.String(), nullable=False))
    op.add_column('flights', sa.Column('city_code_from', sa.String(length=3), nullable=False))
    op.add_column('flights', sa.Column('city_code_to', sa.String(length=3), nullable=False))
    op.drop_column('flights', 'city_from_code')
    op.drop_column('flights', 'city_to_code')
    op.drop_column('flights', 'booking_token,')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('flights', sa.Column('booking_token,', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.add_column('flights', sa.Column('city_to_code', sa.VARCHAR(length=3), autoincrement=False, nullable=False))
    op.add_column('flights', sa.Column('city_from_code', sa.VARCHAR(length=3), autoincrement=False, nullable=False))
    op.drop_column('flights', 'city_code_to')
    op.drop_column('flights', 'city_code_from')
    op.drop_column('flights', 'booking_token')
    # ### end Alembic commands ###
