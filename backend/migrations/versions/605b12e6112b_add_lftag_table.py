"""add_lftag_table

Revision ID: 605b12e6112b
Revises: 509997f0a51e
Create Date: 2022-12-23 09:33:32.564299

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String

# revision identifiers, used by Alembic.
revision = '605b12e6112b'
down_revision = '509997f0a51e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'lftags',
        sa.Column('lftagUri', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('LFTagKey', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('LFTagValues', postgresql.ARRAY(String), autoincrement=False, nullable=False),
        sa.Column('teams', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('owner', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column(
            'created', postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.Column(
            'updated', postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.Column(
            'deleted', postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        )
    )


def downgrade():
    op.drop_table('lftags')