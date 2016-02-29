"""Updated proposal model

Revision ID: 3f90a28ff0f0
Revises: 1d81d03a88fb
Create Date: 2016-02-24 21:03:14.436643

"""

# revision identifiers, used by Alembic.
revision = '3f90a28ff0f0'
down_revision = '1d81d03a88fb'

from alembic import op
import sqlalchemy as sa


def upgrade():
    enum = sa.Enum('talk', 'workshop', name='proposal_types')
    enum.create(op.get_bind(), checkfirst=False)
    op.add_column(u'proposal', sa.Column('demands', sa.Text(), nullable=True))
    op.add_column(u'proposal', sa.Column('expected_duration', sa.Numeric(scale=2), nullable=True))
    op.add_column(u'proposal', sa.Column('restrictions', sa.Text(), nullable=True))
    op.add_column(u'proposal', sa.Column('type', enum, nullable=True))


def downgrade():
    op.drop_column(u'proposal', 'type')
    op.drop_column(u'proposal', 'restrictions')
    op.drop_column(u'proposal', 'expected_duration')
    op.drop_column(u'proposal', 'demands')
    sa.Enum(name="proposal_types").drop(op.get_bind(), checkfirst=False)
