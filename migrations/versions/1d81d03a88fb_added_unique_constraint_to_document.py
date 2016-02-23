"""Added unique constraint to document

Revision ID: 1d81d03a88fb
Revises: 57470ac33e54
Create Date: 2016-02-15 13:57:09.769716

"""

# revision identifiers, used by Alembic.
revision = '1d81d03a88fb'
down_revision = '57470ac33e54'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute('ALTER TABLE account ADD CONSTRAINT "account_document_UK" UNIQUE (document)')


def downgrade():
    op.execute('ALTER TABLE account DROP CONSTRAINT "account_document_UK"')	
