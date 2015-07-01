"""created promocode table and related changes

Revision ID: 1802fdfd2408
Revises: 5a11b40ca10d
Create Date: 2015-07-01 15:39:38.991135

"""

# revision identifiers, used by Alembic.
revision = '1802fdfd2408'
down_revision = '5a11b40ca10d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('promocode',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('creator_id', sa.Integer(), nullable=True),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.Column('hash_code', sa.String(length=32), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('discount', sa.Numeric(), nullable=True),
    sa.ForeignKeyConstraint(['creator_id'], ['account.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('promo_code')
    op.add_column('payment', sa.Column('pc_promocode_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'payment', 'promocode', ['pc_promocode_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'payment', type_='foreignkey')
    op.drop_column('payment', 'pc_promocode_id')
    op.create_table('promo_code',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('creator_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('product_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('payment_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('hash_code', sa.VARCHAR(length=32), autoincrement=False, nullable=True),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['creator_id'], [u'account.id'], name=u'promo_code_creator_id_fkey'),
    sa.ForeignKeyConstraint(['payment_id'], [u'payment.id'], name=u'promo_code_payment_id_fkey'),
    sa.ForeignKeyConstraint(['product_id'], [u'product.id'], name=u'promo_code_product_id_fkey'),
    sa.PrimaryKeyConstraint('id', name=u'promo_code_pkey')
    )
    op.drop_table('promocode')
    ### end Alembic commands ###
