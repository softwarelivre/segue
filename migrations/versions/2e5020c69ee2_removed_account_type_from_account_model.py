"""Removed account type from account model

Revision ID: 2e5020c69ee2
Revises: 3aec24d1b31a
Create Date: 2016-02-07 21:57:53.816777

"""

# revision identifiers, used by Alembic.
revision = '2e5020c69ee2'
down_revision = '3aec24d1b31a'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker, Session

def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    
    op.drop_column('account', 'type')
    op.execute('COMMIT')
    op.execute("ALTER TYPE  account_roles ADD VALUE 'corporate'")

    session.commit()
	

def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    op.add_column(u'account', sa.Column('type', postgresql.ENUM(u'person', u'company', name='account_types'), autoincrement=False, nullable=True))
    op.execute('COMMIT')
    op.execute("ALTER TYPE account_roles DROP VALUE 'corporate'")

    session.commit()
