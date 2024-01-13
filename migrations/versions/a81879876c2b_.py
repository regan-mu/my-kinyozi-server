"""empty message

Revision ID: a81879876c2b
Revises: 
Create Date: 2024-01-10 01:14:08.728368

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a81879876c2b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('title', sa.String(length=100), nullable=False))
        batch_op.add_column(sa.Column('read', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_column('read')
        batch_op.drop_column('title')

    # ### end Alembic commands ###