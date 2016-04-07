"""Added qty to corporate purchase

Revision ID: d545899a6ca
Revises: 4f89d195687c
Create Date: 2016-04-01 15:07:42.001784

"""

# revision identifiers, used by Alembic.
revision = 'd545899a6ca'
down_revision = '4f89d195687c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'purchase', sa.Column('cr_qty', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'purchase', 'cr_qty')
    ### end Alembic commands ###
