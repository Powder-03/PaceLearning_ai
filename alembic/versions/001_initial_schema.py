"""Initial schema - learning_sessions table

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the learning_sessions table."""
    op.create_table(
        'learning_sessions',
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mode', sa.String(50), nullable=False, server_default='generation'),
        sa.Column('status', sa.String(50), nullable=False, server_default='PLANNING'),
        sa.Column('topic', sa.String(500), nullable=False),
        sa.Column('total_days', sa.Integer(), nullable=False),
        sa.Column('time_per_day', sa.String(50), nullable=False),
        sa.Column('lesson_plan', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('current_day', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('current_topic_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('session_id')
    )
    
    # Create indexes for common query patterns
    op.create_index('ix_learning_sessions_session_id', 'learning_sessions', ['session_id'], unique=False)
    op.create_index('ix_learning_sessions_user_id', 'learning_sessions', ['user_id'], unique=False)
    op.create_index('ix_learning_sessions_mode', 'learning_sessions', ['mode'], unique=False)
    op.create_index('ix_learning_sessions_status', 'learning_sessions', ['status'], unique=False)


def downgrade() -> None:
    """Drop the learning_sessions table."""
    op.drop_index('ix_learning_sessions_status', table_name='learning_sessions')
    op.drop_index('ix_learning_sessions_mode', table_name='learning_sessions')
    op.drop_index('ix_learning_sessions_user_id', table_name='learning_sessions')
    op.drop_index('ix_learning_sessions_session_id', table_name='learning_sessions')
    op.drop_table('learning_sessions')
