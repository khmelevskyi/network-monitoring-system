"""Added a table for blacklist/whitelist

Revision ID: 4fd6ad0c4d21
Revises: 628d35bdfc5a
Create Date: 2025-05-22 13:54:43.305254

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4fd6ad0c4d21'
down_revision = '628d35bdfc5a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('custom_ip_list_entries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ip_address', sa.String(length=64), nullable=False),
    sa.Column('label', sa.String(length=16), nullable=False),
    sa.Column('reason', sa.String(length=256), nullable=True),
    sa.Column('added_by', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ip_address')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('custom_ip_list_entries')
    # ### end Alembic commands ###
