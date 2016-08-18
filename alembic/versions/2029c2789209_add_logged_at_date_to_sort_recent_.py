"""add logged_at date to sort recent entries

Revision ID: 2029c2789209
Revises: 79f5f7602ba5
Create Date: 2016-08-18 15:53:15.959565

"""

# revision identifiers, used by Alembic.
revision = '2029c2789209'
down_revision = '79f5f7602ba5'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('analysis', sa.Column('logged_at', sa.DateTime(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('analysis', 'logged_at')
    ### end Alembic commands ###
