"""Changed proposal_invite account fk

Revision ID: a78fa8b62a2
Revises: e7254f01f08
Create Date: 2016-08-02 14:11:32.731137

"""

# revision identifiers, used by Alembic.
revision = 'a78fa8b62a2'
down_revision = 'e7254f01f08'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'proposal_invite', sa.Column('account_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'proposal_invite', 'account', ['account_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'proposal_invite', type_='foreignkey')
    op.drop_column(u'proposal_invite', 'account_id')
    ### end Alembic commands ###
