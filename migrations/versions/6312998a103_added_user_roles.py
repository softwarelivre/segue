"""Added user roles

Revision ID: 6312998a103
Revises: 9388cc1122c
Create Date: 2016-03-09 14:26:16.992459

"""

# revision identifiers, used by Alembic.
revision = '6312998a103'
down_revision = '9388cc1122c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=True),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('roles_accounts',
    sa.Column('account_id', sa.Integer(), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.ForeignKeyConstraint(['account_id'], ['account.id'], )
    )


def downgrade():
    op.drop_table('roles_users')
    op.drop_table('role')
