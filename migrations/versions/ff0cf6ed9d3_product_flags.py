"""product_flags

Revision ID: ff0cf6ed9d3
Revises: 11dd09c50161
Create Date: 2015-06-30 14:53:57.159994

"""

# revision identifiers, used by Alembic.
revision = 'ff0cf6ed9d3'
down_revision = '11dd09c50161'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product', sa.Column('gives_kit', sa.Boolean(), server_default='t', nullable=True))
    op.add_column('product', sa.Column('is_promo', sa.Boolean(), server_default='f', nullable=True))
    op.add_column('product', sa.Column('is_speaker', sa.Boolean(), server_default='f', nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('product', 'is_speaker')
    op.drop_column('product', 'is_promo')
    op.drop_column('product', 'gives_kit')
    ### end Alembic commands ###
