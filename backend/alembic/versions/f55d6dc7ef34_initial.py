"""initial — create core tables (roles, users, user_preferences, etc.)

Revision ID: f55d6dc7ef34
Revises: 
Create Date: 2026-07-13 19:15:51.435653
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'f55d6dc7ef34'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Roles ────────────────────────────────────────────────────
    op.create_table(
        'roles',
        sa.Column('role_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('role_name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('role_id'),
        sa.UniqueConstraint('role_name'),
    )

    # ── Users ────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('role_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('idx_users_email', 'users', ['email'])

    # ── Officers ─────────────────────────────────────────────────
    op.create_table(
        'officers',
        sa.Column('officer_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('badge_number', sa.String(length=30), nullable=False),
        sa.Column('designation', sa.String(length=100), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('police_station', sa.String(length=150), nullable=True),
        sa.Column('joining_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('officer_id'),
        sa.UniqueConstraint('badge_number'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('idx_officer_badge', 'officers', ['badge_number'])

    # ── Locations ────────────────────────────────────────────────
    op.create_table(
        'locations',
        sa.Column('location_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('district', sa.String(length=100), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('area', sa.String(length=150), nullable=False),
        sa.Column('pincode', sa.String(length=10), nullable=True),
        sa.Column('latitude', sa.DECIMAL(10, 8), nullable=True),
        sa.Column('longitude', sa.DECIMAL(11, 8), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('location_id'),
    )
    op.create_index('idx_city', 'locations', ['city'])

    # ── Crime Types ──────────────────────────────────────────────
    op.create_table(
        'crime_types',
        sa.Column('crime_type_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('crime_name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('severity', mysql.ENUM('Low', 'Medium', 'High', 'Critical'), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('crime_type_id'),
    )
    op.create_index('idx_crime_name', 'crime_types', ['crime_name'])

    # ── FIRs ─────────────────────────────────────────────────────
    op.create_table(
        'firs',
        sa.Column('fir_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fir_number', sa.String(length=50), nullable=False),
        sa.Column('crime_type_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('officer_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('incident_date', sa.DateTime(), nullable=False),
        sa.Column('complaint_date', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('investigation_status', mysql.ENUM('Pending', 'Under Investigation', 'Solved', 'Closed'), server_default='Pending', nullable=True),
        sa.Column('priority', mysql.ENUM('Low', 'Medium', 'High', 'Critical'), server_default='Medium', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['crime_type_id'], ['crime_types.crime_type_id'], ),
        sa.ForeignKeyConstraint(['location_id'], ['locations.location_id'], ),
        sa.ForeignKeyConstraint(['officer_id'], ['officers.officer_id'], ),
        sa.PrimaryKeyConstraint('fir_id'),
        sa.UniqueConstraint('fir_number'),
    )
    op.create_index('idx_fir_number', 'firs', ['fir_number'])
    op.create_index('idx_incident_date', 'firs', ['incident_date'])

    # ── Accused ──────────────────────────────────────────────────
    op.create_table(
        'accused',
        sa.Column('accused_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('gender', mysql.ENUM('Male', 'Female', 'Other'), nullable=True),
        sa.Column('dob', sa.Date(), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('occupation', sa.String(length=100), nullable=True),
        sa.Column('aadhaar_number', sa.String(length=20), nullable=True),
        sa.Column('risk_score', sa.DECIMAL(5, 2), server_default='0', nullable=True),
        sa.Column('is_repeat_offender', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('accused_id'),
    )
    op.create_index('idx_accused_name', 'accused', ['full_name'])

    # ── Victims ──────────────────────────────────────────────────
    op.create_table(
        'victims',
        sa.Column('victim_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('gender', mysql.ENUM('Male', 'Female', 'Other'), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('occupation', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('victim_id'),
    )
    op.create_index('idx_victim_name', 'victims', ['full_name'])

    # ── FIR ↔ Accused (Many-to-Many) ─────────────────────────────
    op.create_table(
        'fir_accused',
        sa.Column('fir_id', sa.Integer(), nullable=False),
        sa.Column('accused_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['accused_id'], ['accused.accused_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fir_id'], ['firs.fir_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('fir_id', 'accused_id'),
    )

    # ── FIR ↔ Victims (Many-to-Many) ─────────────────────────────
    op.create_table(
        'fir_victims',
        sa.Column('fir_id', sa.Integer(), nullable=False),
        sa.Column('victim_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['fir_id'], ['firs.fir_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['victim_id'], ['victims.victim_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('fir_id', 'victim_id'),
    )

    # ── Evidence ─────────────────────────────────────────────────
    op.create_table(
        'evidence',
        sa.Column('evidence_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fir_id', sa.Integer(), nullable=False),
        sa.Column('evidence_type', mysql.ENUM('Photo', 'Video', 'Document', 'Fingerprint', 'DNA', 'Weapon', 'Digital', 'Other'), nullable=True),
        sa.Column('evidence_name', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=255), nullable=True),
        sa.Column('collected_by', sa.Integer(), nullable=True),
        sa.Column('collected_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['collected_by'], ['officers.officer_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['fir_id'], ['firs.fir_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('evidence_id'),
    )
    op.create_index('idx_evidence_type', 'evidence', ['evidence_type'])

    # ── Crime History ────────────────────────────────────────────
    op.create_table(
        'crime_history',
        sa.Column('history_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('accused_id', sa.Integer(), nullable=False),
        sa.Column('fir_id', sa.Integer(), nullable=True),
        sa.Column('crime_type', sa.String(length=100), nullable=True),
        sa.Column('arrest_date', sa.Date(), nullable=True),
        sa.Column('conviction_status', mysql.ENUM('Pending', 'Convicted', 'Acquitted'), server_default='Pending', nullable=True),
        sa.Column('sentence', sa.Text(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['accused_id'], ['accused.accused_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fir_id'], ['firs.fir_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('history_id'),
    )
    op.create_index('idx_history_accused', 'crime_history', ['accused_id'])

    # ── Financial Transactions ───────────────────────────────────
    op.create_table(
        'financial_transactions',
        sa.Column('transaction_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('accused_id', sa.Integer(), nullable=True),
        sa.Column('fir_id', sa.Integer(), nullable=True),
        sa.Column('bank_name', sa.String(length=100), nullable=True),
        sa.Column('account_number', sa.String(length=50), nullable=True),
        sa.Column('transaction_reference', sa.String(length=100), nullable=True),
        sa.Column('amount', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('transaction_type', mysql.ENUM('Credit', 'Debit'), nullable=True),
        sa.Column('transaction_date', sa.DateTime(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['accused_id'], ['accused.accused_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['fir_id'], ['firs.fir_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('transaction_id'),
    )
    op.create_index('idx_transaction_accused', 'financial_transactions', ['accused_id'])

    # ── Conversation History ─────────────────────────────────────
    op.create_table(
        'conversation_history',
        sa.Column('conversation_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('question', sa.Text(), nullable=True),
        sa.Column('ai_response', sa.Text(), nullable=True),
        sa.Column('language', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('conversation_id'),
    )
    op.create_index('idx_conversation_user', 'conversation_history', ['user_id'])

    # ── Audit Logs ───────────────────────────────────────────────
    op.create_table(
        'audit_logs',
        sa.Column('log_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=255), nullable=True),
        sa.Column('table_name', sa.String(length=100), nullable=True),
        sa.Column('record_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('log_time', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('log_id'),
    )
    op.create_index('idx_audit_user', 'audit_logs', ['user_id'])

    # ── Predictions ──────────────────────────────────────────────
    op.create_table(
        'predictions',
        sa.Column('prediction_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('crime_type_id', sa.Integer(), nullable=True),
        sa.Column('prediction_date', sa.Date(), nullable=True),
        sa.Column('predicted_cases', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.DECIMAL(5, 2), nullable=True),
        sa.Column('risk_level', mysql.ENUM('Low', 'Medium', 'High', 'Critical'), nullable=True),
        sa.Column('generated_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['crime_type_id'], ['crime_types.crime_type_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.location_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('prediction_id'),
    )
    op.create_index('idx_prediction_location', 'predictions', ['location_id'])
    op.create_index('idx_prediction_date', 'predictions', ['prediction_date'])

    # ═══════════════════════════════════════════════════════════
    # User Preferences (Settings module)
    # ═══════════════════════════════════════════════════════════
    op.create_table(
        'user_preferences',
        sa.Column('preference_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('theme', sa.String(length=20), server_default='dark', nullable=False),
        sa.Column('language', sa.String(length=10), server_default='en', nullable=False),
        sa.Column('timezone', sa.String(length=50), server_default='Asia/Kolkata', nullable=False),
        sa.Column('date_format', sa.String(length=20), server_default='DD/MM/YYYY', nullable=False),
        sa.Column('email_notifications', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('sms_notifications', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('ai_notifications', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('report_notifications', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('security_alerts', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('preference_id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('idx_preferences_user', 'user_preferences', ['user_id'])


def downgrade() -> None:
    op.drop_index('idx_preferences_user', table_name='user_preferences')
    op.drop_table('user_preferences')
    op.drop_index('idx_prediction_date', table_name='predictions')
    op.drop_index('idx_prediction_location', table_name='predictions')
    op.drop_table('predictions')
    op.drop_index('idx_audit_user', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('idx_conversation_user', table_name='conversation_history')
    op.drop_table('conversation_history')
    op.drop_index('idx_transaction_accused', table_name='financial_transactions')
    op.drop_table('financial_transactions')
    op.drop_index('idx_history_accused', table_name='crime_history')
    op.drop_table('crime_history')
    op.drop_index('idx_evidence_type', table_name='evidence')
    op.drop_table('evidence')
    op.drop_table('fir_victims')
    op.drop_table('fir_accused')
    op.drop_index('idx_victim_name', table_name='victims')
    op.drop_table('victims')
    op.drop_index('idx_accused_name', table_name='accused')
    op.drop_table('accused')
    op.drop_index('idx_incident_date', table_name='firs')
    op.drop_index('idx_fir_number', table_name='firs')
    op.drop_table('firs')
    op.drop_index('idx_crime_name', table_name='crime_types')
    op.drop_table('crime_types')
    op.drop_index('idx_city', table_name='locations')
    op.drop_table('locations')
    op.drop_index('idx_officer_badge', table_name='officers')
    op.drop_table('officers')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
    op.drop_table('roles')
