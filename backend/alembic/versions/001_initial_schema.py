"""Initial schema with pgvector support

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.Enum('admin', 'host', 'viewer', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('subscription_tier', sa.Enum('free', 'premium', 'enterprise', name='subscriptiontier'), nullable=False, default='free'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    
    # Create sources table
    op.create_table('sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_type', sa.Enum('book', 'article', 'document', 'letter', 'speech', 'manuscript', 'other', name='sourcetype'), nullable=False),
        sa.Column('author', sa.String(length=200), nullable=True),
        sa.Column('publication_date', sa.Date(), nullable=True),
        sa.Column('publisher', sa.String(length=200), nullable=True),
        sa.Column('isbn', sa.String(length=20), nullable=True),
        sa.Column('url', sa.String(length=2000), nullable=True),
        sa.Column('reliability_score', sa.Float(), nullable=False, default=0.5),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True, default=[]),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create documents table
    op.create_table('documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=False, default=0),
        sa.Column('character_count', sa.Integer(), nullable=False, default=0),
        sa.Column('processing_status', sa.Enum('pending', 'processing', 'chunking', 'indexing', 'completed', 'error', name='processingstatus'), nullable=False, default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create chunks table with vector embeddings
    op.create_table('chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=False),
        sa.Column('character_count', sa.Integer(), nullable=False),
        sa.Column('start_position', sa.Integer(), nullable=True),
        sa.Column('end_position', sa.Integer(), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),  # OpenAI ada-002 embedding size
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create episodes table
    op.create_table('episodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('persona_pack_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('active', 'paused', 'completed', 'archived', name='episodestatus'), nullable=False, default='active'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create beats table (conversation exchanges)
    op.create_table('beats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('episode_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('user_message', sa.Text(), nullable=False),
        sa.Column('lincoln_response', sa.Text(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['episode_id'], ['episodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create citations table
    op.create_table('citations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('episode_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('beat_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('chunk_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('citation_text', sa.String(length=500), nullable=False),
        sa.Column('context_snippet', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('validation_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['beat_id'], ['beats.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chunk_id'], ['chunks.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['episode_id'], ['episodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_role', 'users', ['role'])
    
    op.create_index('idx_sources_type', 'sources', ['source_type'])
    op.create_index('idx_sources_created_by', 'sources', ['created_by'])
    op.create_index('idx_sources_reliability', 'sources', ['reliability_score'])
    
    op.create_index('idx_documents_source_id', 'documents', ['source_id'])
    op.create_index('idx_documents_status', 'documents', ['processing_status'])
    op.create_index('idx_documents_hash', 'documents', ['file_hash'])
    
    op.create_index('idx_chunks_document_id', 'chunks', ['document_id'])
    op.create_index('idx_chunks_sequence', 'chunks', ['document_id', 'sequence_number'])
    
    # Vector similarity search index
    op.execute('CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')
    
    op.create_index('idx_episodes_created_by', 'episodes', ['created_by'])
    op.create_index('idx_episodes_status', 'episodes', ['status'])
    op.create_index('idx_episodes_created_at', 'episodes', ['created_at'])
    
    op.create_index('idx_beats_episode_id', 'beats', ['episode_id'])
    op.create_index('idx_beats_sequence', 'beats', ['episode_id', 'sequence_number'])
    
    op.create_index('idx_citations_episode_id', 'citations', ['episode_id'])
    op.create_index('idx_citations_beat_id', 'citations', ['beat_id'])
    op.create_index('idx_citations_chunk_id', 'citations', ['chunk_id'])
    op.create_index('idx_citations_source_id', 'citations', ['source_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('citations')
    op.drop_table('beats')
    op.drop_table('episodes')
    op.drop_table('chunks')
    op.drop_table('documents')
    op.drop_table('sources')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS subscriptiontier')
    op.execute('DROP TYPE IF EXISTS sourcetype')
    op.execute('DROP TYPE IF EXISTS processingstatus')
    op.execute('DROP TYPE IF EXISTS episodestatus')
    
    # Drop pgvector extension (optional, might be used by other apps)
    # op.execute('DROP EXTENSION IF EXISTS vector')