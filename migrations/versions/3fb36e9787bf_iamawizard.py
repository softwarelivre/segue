"""IamAWizard

Revision ID: 3fb36e9787bf
Revises: cbd0f6a4415
Create Date: 2016-04-05 19:45:28.808500

"""

# revision identifiers, used by Alembic.
revision = '3fb36e9787bf'
down_revision = 'cbd0f6a4415'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'account', 'corporate_id')
    op.add_column(u'purchase', sa.Column('qty', sa.Integer(), nullable=True))
    op.drop_column(u'purchase', 'cr_qty')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'purchase', sa.Column('cr_qty', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column(u'purchase', 'qty')
    op.add_column(u'account', sa.Column('corporate_id', sa.INTEGER(), autoincrement=False, nullable=True))
    ### end Alembic commands ###
