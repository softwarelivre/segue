"""Fix circular dependency between account and corporate

Revision ID: 47ef68d22e47
Revises: 3d0edcdd2486
Create Date: 2017-02-15 19:52:10.545452

"""

# revision identifiers, used by Alembic.
revision = '47ef68d22e47'
down_revision = '3d0edcdd2486'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(u'account', sa.Column('corporate_id', sa.Integer(), nullable=True))
    op.create_foreign_key('employee_fk', 'account', 'corporate', ['corporate_id'], ['id'])


def downgrade():
    op.drop_constraint('employee_fk', 'account', type_='foreignkey')
    op.drop_column(u'account', 'corporate_id')
