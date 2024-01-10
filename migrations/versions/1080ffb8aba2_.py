"""empty message

Revision ID: 1080ffb8aba2
Revises: a81879876c2b
Create Date: 2024-01-10 12:47:54.020474

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1080ffb8aba2'
down_revision = 'a81879876c2b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('equipments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('equipment_name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('faulty', sa.Boolean(), nullable=True),
    sa.Column('bought_on', sa.DateTime(), nullable=True),
    sa.Column('price', sa.Integer(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['shop_id'], ['barbershops.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('equipments')
    # ### end Alembic commands ###
