"""Revert to the old permission system

Revision ID: 3d0edcdd2486
Revises: 34b8c096e9b5
Create Date: 2017-02-15 19:30:55.465239

"""

# revision identifiers, used by Alembic.
revision = '3d0edcdd2486'
down_revision = '34b8c096e9b5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('roles_accounts',
    sa.Column('account_id', sa.Integer(), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['account.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], )
    )
    op.drop_table('permission')
    op.drop_table('accounts_roles')
    op.add_column(u'account', sa.Column('role', sa.Enum('user', 'operator', 'admin', 'employee', 'cashier', 'corporate', 'foreign', name='account_roles'), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'account', 'role')
    op.create_table('accounts_roles',
    sa.Column('account_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('role_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['account_id'], [u'account.id'], name=u'accounts_roles_account_id_fkey'),
    sa.ForeignKeyConstraint(['role_id'], [u'role.id'], name=u'accounts_roles_role_id_fkey')
    )
    op.create_table('permission',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('role_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['role_id'], [u'role.id'], name=u'permission_role_id_fkey'),
    sa.PrimaryKeyConstraint('id', name=u'permission_pkey'),
    sa.UniqueConstraint('name', name=u'permission_name_key')
    )
    op.drop_table('roles_accounts')
    ### end Alembic commands ###
