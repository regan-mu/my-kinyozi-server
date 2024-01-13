"""empty message

Revision ID: 7c2460f62e5e
Revises: 593798ad38fd
Create Date: 2024-01-11 12:07:28.043781

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c2460f62e5e'
down_revision = '593798ad38fd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('employees', schema=None) as batch_op:
        batch_op.add_column(sa.Column('shop_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'barbershops', ['shop_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('employees', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('shop_id')

    # ### end Alembic commands ###