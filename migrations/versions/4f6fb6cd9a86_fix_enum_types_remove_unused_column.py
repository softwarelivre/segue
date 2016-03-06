"""Fix enum types remove unused column

Revision ID: 4f6fb6cd9a86
Revises: 18fcdf2142e1
Create Date: 2016-03-06 15:45:48.972665

"""

# revision identifiers, used by Alembic.
revision = '4f6fb6cd9a86'
down_revision = '18fcdf2142e1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute('COMMIT')
    op.execute('ALTER TABLE ACCOUNT DROP COLUMN IF EXISTS receive_emails')
    op.execute('ALTER TYPE account_roles ADD VALUE IF NOT EXISTS \'foreign\'')
    op.execute('ALTER TYPE account_roles ADD VALUE IF NOT EXISTS \'employee\'')
    op.execute('ALTER TYPE account_roles ADD VALUE IF NOT EXISTS \'cashier\'')
    op.execute('ALTER TYPE buyer_types ADD VALUE IF NOT EXISTS \'foreign\'')

def downgrade():
    op.add_column(u'account', sa.Column('receive_emails', sa.BOOLEAN(), autoincrement=False, nullable=True))
