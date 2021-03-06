"""Added product information column

Revision ID: 335d1b6ab5d0
Revises: 3515f5a108f7
Create Date: 2016-01-21 08:49:33.682588

"""

# revision identifiers, used by Alembic.
revision = '335d1b6ab5d0'
down_revision = '3515f5a108f7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'product', sa.Column('information', sa.Text(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'product', 'information')
    ### end Alembic commands ###
