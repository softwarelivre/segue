"""Changed amount type from Float to Numeric

Revision ID: 57470ac33e54
Revises: 2e5020c69ee2
Create Date: 2016-02-13 17:03:41.009013

"""

# revision identifiers, used by Alembic.
revision = '57470ac33e54'
down_revision = '2e5020c69ee2'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.execute('ALTER TABLE purchase ALTER COLUMN amount TYPE NUMERIC USING amount::NUMERIC')


def downgrade():
    op.execute('ALTER TABLE purchase ALTER COLUMN amount TYPE REAL USING amount::REAL')
