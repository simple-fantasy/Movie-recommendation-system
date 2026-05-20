"""add security question fields and movie submitted_by

Revision ID: abc123def456
Revises: 7643b9729fe3
Create Date: 2026-05-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abc123def456'
down_revision = '7643b9729fe3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('security_question', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('security_answer_hash', sa.String(length=256), nullable=True))

    with op.batch_alter_table('movies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('submitted_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_movies_submitted_by_users', 'users', ['submitted_by'], ['id'])


def downgrade():
    with op.batch_alter_table('movies', schema=None) as batch_op:
        batch_op.drop_constraint('fk_movies_submitted_by_users', type_='foreignkey')
        batch_op.drop_column('submitted_by')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('security_answer_hash')
        batch_op.drop_column('security_question')
