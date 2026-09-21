"""Initial CampusPulse schema: users, taxonomy, routing rules, issues, reports,
evidence, verifications, escalations, timeline and notifications.

Revision ID: c24ce836a89e
Revises: 
Create Date: 2026-09-21 10:51:01.937631

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c24ce836a89e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    
    op.create_table('issue_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('category', sa.String(length=100), nullable=False),
    sa.Column('sub_type', sa.String(length=100), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('requires_verification', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('category', 'sub_type', name='uq_issue_type_category_subtype')
    )
    op.create_index(op.f('ix_issue_types_category'), 'issue_types', ['category'], unique=False)
    op.create_index(op.f('ix_issue_types_id'), 'issue_types', ['id'], unique=False)
    op.create_index(op.f('ix_issue_types_sub_type'), 'issue_types', ['sub_type'], unique=False)
    op.create_table('locations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('building', sa.String(length=100), nullable=False),
    sa.Column('floor', sa.String(length=50), nullable=True),
    sa.Column('room', sa.String(length=50), nullable=True),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['locations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_locations_building'), 'locations', ['building'], unique=False)
    op.create_index(op.f('ix_locations_code'), 'locations', ['code'], unique=True)
    op.create_index(op.f('ix_locations_id'), 'locations', ['id'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('role', sa.Enum('STUDENT', 'HANDLER', 'HIGHER_AUTHORITY', 'ADMIN', name='userrole', native_enum=False, length=32), nullable=False),
    sa.Column('department', sa.String(length=255), nullable=True),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_table('issues',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('issue_type_id', sa.Integer(), nullable=False),
    sa.Column('location_id', sa.Integer(), nullable=False),
    sa.Column('specific_asset', sa.String(length=150), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('status', sa.Enum('OPEN', 'IN_PROGRESS', 'ESCALATED', 'RESOLVED_PENDING_VERIFICATION', 'VERIFIED_CLOSED', 'REOPENED', name='issuestatus', native_enum=False, length=40), nullable=False),
    sa.Column('current_handler_id', sa.Integer(), nullable=True),
    sa.Column('requires_verification', sa.Boolean(), nullable=False),
    sa.Column('needs_triage', sa.Boolean(), nullable=False),
    sa.Column('affected_student_count', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['current_handler_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['issue_type_id'], ['issue_types.id'], ),
    sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_issues_current_handler_id'), 'issues', ['current_handler_id'], unique=False)
    op.create_index(op.f('ix_issues_id'), 'issues', ['id'], unique=False)
    op.create_index(op.f('ix_issues_issue_type_id'), 'issues', ['issue_type_id'], unique=False)
    op.create_index(op.f('ix_issues_location_id'), 'issues', ['location_id'], unique=False)
    op.create_index(op.f('ix_issues_needs_triage'), 'issues', ['needs_triage'], unique=False)
    op.create_index(op.f('ix_issues_specific_asset'), 'issues', ['specific_asset'], unique=False)
    op.create_index(op.f('ix_issues_status'), 'issues', ['status'], unique=False)
    op.create_index('ix_issues_type_location_status', 'issues', ['issue_type_id', 'location_id', 'status'], unique=False)
    op.create_table('routing_rules',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('issue_type_id', sa.Integer(), nullable=True),
    sa.Column('location_id', sa.Integer(), nullable=True),
    sa.Column('handler_id', sa.Integer(), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['handler_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['issue_type_id'], ['issue_types.id'], ),
    sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_routing_rules_handler_id'), 'routing_rules', ['handler_id'], unique=False)
    op.create_index(op.f('ix_routing_rules_id'), 'routing_rules', ['id'], unique=False)
    op.create_index(op.f('ix_routing_rules_issue_type_id'), 'routing_rules', ['issue_type_id'], unique=False)
    op.create_index(op.f('ix_routing_rules_location_id'), 'routing_rules', ['location_id'], unique=False)
    op.create_table('escalations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('issue_id', sa.Integer(), nullable=False),
    sa.Column('escalated_by_id', sa.Integer(), nullable=False),
    sa.Column('escalated_to_id', sa.Integer(), nullable=True),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('previous_status', sa.String(length=50), nullable=False),
    sa.Column('history_snapshot', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['escalated_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['escalated_to_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_escalations_escalated_by_id'), 'escalations', ['escalated_by_id'], unique=False)
    op.create_index(op.f('ix_escalations_escalated_to_id'), 'escalations', ['escalated_to_id'], unique=False)
    op.create_index(op.f('ix_escalations_id'), 'escalations', ['id'], unique=False)
    op.create_index(op.f('ix_escalations_issue_id'), 'escalations', ['issue_id'], unique=False)
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('issue_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('is_read', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_issue_id'), 'notifications', ['issue_id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_table('reports',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('issue_id', sa.Integer(), nullable=True),
    sa.Column('reporter_id', sa.Integer(), nullable=False),
    sa.Column('issue_type_id', sa.Integer(), nullable=False),
    sa.Column('location_id', sa.Integer(), nullable=False),
    sa.Column('specific_asset', sa.String(length=150), nullable=True),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('photo_url', sa.String(length=500), nullable=True),
    sa.Column('status', sa.Enum('SUBMITTED', 'LINKED_TO_ISSUE', name='reportstatus', native_enum=False, length=40), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ),
    sa.ForeignKeyConstraint(['issue_type_id'], ['issue_types.id'], ),
    sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
    sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_id'), 'reports', ['id'], unique=False)
    op.create_index(op.f('ix_reports_issue_id'), 'reports', ['issue_id'], unique=False)
    op.create_index(op.f('ix_reports_issue_type_id'), 'reports', ['issue_type_id'], unique=False)
    op.create_index(op.f('ix_reports_location_id'), 'reports', ['location_id'], unique=False)
    op.create_index(op.f('ix_reports_reporter_id'), 'reports', ['reporter_id'], unique=False)
    op.create_table('resolution_evidences',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('issue_id', sa.Integer(), nullable=False),
    sa.Column('submitted_by_id', sa.Integer(), nullable=False),
    sa.Column('evidence_type', sa.Enum('PHOTO', 'DESCRIPTION', 'MAINTENANCE_RECORD', 'SCREENSHOT', 'OTHER', name='evidencetype', native_enum=False, length=40), nullable=False),
    sa.Column('notes', sa.Text(), nullable=False),
    sa.Column('attachment_url', sa.String(length=500), nullable=True),
    sa.Column('resolution_round', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ),
    sa.ForeignKeyConstraint(['submitted_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resolution_evidences_id'), 'resolution_evidences', ['id'], unique=False)
    op.create_index(op.f('ix_resolution_evidences_issue_id'), 'resolution_evidences', ['issue_id'], unique=False)
    op.create_index(op.f('ix_resolution_evidences_submitted_by_id'), 'resolution_evidences', ['submitted_by_id'], unique=False)
    op.create_table('timeline_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('issue_id', sa.Integer(), nullable=False),
    sa.Column('actor_id', sa.Integer(), nullable=True),
    sa.Column('event_type', sa.Enum('REPORT_SUBMITTED', 'REPORT_LINKED', 'ISSUE_CREATED', 'ROUTED', 'STATUS_CHANGED', 'STARTED_PROGRESS', 'RESOLVED', 'ESCALATED', 'VERIFIED', 'DISPUTED', 'REOPENED', 'REASSIGNED', name='timelineeventtype', native_enum=False, length=40), nullable=False),
    sa.Column('from_status', sa.Enum('OPEN', 'IN_PROGRESS', 'ESCALATED', 'RESOLVED_PENDING_VERIFICATION', 'VERIFIED_CLOSED', 'REOPENED', name='issuestatus', native_enum=False, length=40), nullable=True),
    sa.Column('to_status', sa.Enum('OPEN', 'IN_PROGRESS', 'ESCALATED', 'RESOLVED_PENDING_VERIFICATION', 'VERIFIED_CLOSED', 'REOPENED', name='issuestatus', native_enum=False, length=40), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('details', sa.Text(), nullable=True),
    sa.Column('metadata_json', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_timeline_events_actor_id'), 'timeline_events', ['actor_id'], unique=False)
    op.create_index(op.f('ix_timeline_events_id'), 'timeline_events', ['id'], unique=False)
    op.create_index(op.f('ix_timeline_events_issue_id'), 'timeline_events', ['issue_id'], unique=False)
    op.create_table('verifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('issue_id', sa.Integer(), nullable=False),
    sa.Column('verified_by_id', sa.Integer(), nullable=False),
    sa.Column('resolution_round', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('CONFIRMED', 'DISPUTED', name='verificationstatus', native_enum=False, length=32), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ),
    sa.ForeignKeyConstraint(['verified_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('issue_id', 'verified_by_id', 'resolution_round', name='uq_verification_per_round')
    )
    op.create_index(op.f('ix_verifications_id'), 'verifications', ['id'], unique=False)
    op.create_index(op.f('ix_verifications_issue_id'), 'verifications', ['issue_id'], unique=False)
    op.create_index(op.f('ix_verifications_verified_by_id'), 'verifications', ['verified_by_id'], unique=False)
    


def downgrade() -> None:
    
    op.drop_index(op.f('ix_verifications_verified_by_id'), table_name='verifications')
    op.drop_index(op.f('ix_verifications_issue_id'), table_name='verifications')
    op.drop_index(op.f('ix_verifications_id'), table_name='verifications')
    op.drop_table('verifications')
    op.drop_index(op.f('ix_timeline_events_issue_id'), table_name='timeline_events')
    op.drop_index(op.f('ix_timeline_events_id'), table_name='timeline_events')
    op.drop_index(op.f('ix_timeline_events_actor_id'), table_name='timeline_events')
    op.drop_table('timeline_events')
    op.drop_index(op.f('ix_resolution_evidences_submitted_by_id'), table_name='resolution_evidences')
    op.drop_index(op.f('ix_resolution_evidences_issue_id'), table_name='resolution_evidences')
    op.drop_index(op.f('ix_resolution_evidences_id'), table_name='resolution_evidences')
    op.drop_table('resolution_evidences')
    op.drop_index(op.f('ix_reports_reporter_id'), table_name='reports')
    op.drop_index(op.f('ix_reports_location_id'), table_name='reports')
    op.drop_index(op.f('ix_reports_issue_type_id'), table_name='reports')
    op.drop_index(op.f('ix_reports_issue_id'), table_name='reports')
    op.drop_index(op.f('ix_reports_id'), table_name='reports')
    op.drop_table('reports')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_issue_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_index(op.f('ix_escalations_issue_id'), table_name='escalations')
    op.drop_index(op.f('ix_escalations_id'), table_name='escalations')
    op.drop_index(op.f('ix_escalations_escalated_to_id'), table_name='escalations')
    op.drop_index(op.f('ix_escalations_escalated_by_id'), table_name='escalations')
    op.drop_table('escalations')
    op.drop_index(op.f('ix_routing_rules_location_id'), table_name='routing_rules')
    op.drop_index(op.f('ix_routing_rules_issue_type_id'), table_name='routing_rules')
    op.drop_index(op.f('ix_routing_rules_id'), table_name='routing_rules')
    op.drop_index(op.f('ix_routing_rules_handler_id'), table_name='routing_rules')
    op.drop_table('routing_rules')
    op.drop_index('ix_issues_type_location_status', table_name='issues')
    op.drop_index(op.f('ix_issues_status'), table_name='issues')
    op.drop_index(op.f('ix_issues_specific_asset'), table_name='issues')
    op.drop_index(op.f('ix_issues_needs_triage'), table_name='issues')
    op.drop_index(op.f('ix_issues_location_id'), table_name='issues')
    op.drop_index(op.f('ix_issues_issue_type_id'), table_name='issues')
    op.drop_index(op.f('ix_issues_id'), table_name='issues')
    op.drop_index(op.f('ix_issues_current_handler_id'), table_name='issues')
    op.drop_table('issues')
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_locations_id'), table_name='locations')
    op.drop_index(op.f('ix_locations_code'), table_name='locations')
    op.drop_index(op.f('ix_locations_building'), table_name='locations')
    op.drop_table('locations')
    op.drop_index(op.f('ix_issue_types_sub_type'), table_name='issue_types')
    op.drop_index(op.f('ix_issue_types_id'), table_name='issue_types')
    op.drop_index(op.f('ix_issue_types_category'), table_name='issue_types')
    op.drop_table('issue_types')
    

