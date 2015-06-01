"""added proposal tags table

Revision ID: 317c258a7219
Revises: f7016fed489
Create Date: 2015-06-01 03:03:15.285709

"""

# revision identifiers, used by Alembic.
revision = '317c258a7219'
down_revision = 'f7016fed489'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('proposal_tag',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=True),
    sa.Column('proposal_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['proposal_id'], ['proposal.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('proposal_tag')
    ### end Alembic commands ###
