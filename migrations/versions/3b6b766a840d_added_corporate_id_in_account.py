"""added_corporate_id_in_account

Revision ID: 3b6b766a840d
Revises: 2e28fc5d405
Create Date: 2015-07-04 14:03:38.582235

"""

# revision identifiers, used by Alembic.
revision = '3b6b766a840d'
down_revision = '2e28fc5d405'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('account', sa.Column('corporate_id', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('account', 'corporate_id')
    ### end Alembic commands ###
