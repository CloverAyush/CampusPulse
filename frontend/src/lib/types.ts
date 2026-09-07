export type UserRole = "student" | "handler" | "higher_authority" | "admin";

export type IssueStatus =
  | "OPEN"
  | "IN_PROGRESS"
  | "ESCALATED"
  | "RESOLVED_PENDING_VERIFICATION"
  | "VERIFIED_CLOSED"
  | "REOPENED";

export type ReportStatus = "SUBMITTED" | "LINKED_TO_ISSUE";

export type EvidenceType =
  | "photo"
  | "description"
  | "maintenance_record"
  | "screenshot"
  | "other";

export type VerificationStatus = "confirmed" | "disputed";

export type TimelineEventType =
  | "REPORT_SUBMITTED"
  | "REPORT_LINKED"
  | "ISSUE_CREATED"
  | "ROUTED"
  | "STATUS_CHANGED"
  | "STARTED_PROGRESS"
  | "RESOLVED"
  | "ESCALATED"
  | "VERIFIED"
  | "DISPUTED"
  | "REOPENED"
  | "REASSIGNED";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  department?: string | null;
  phone?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface IssueType {
  id: number;
  category: string;
  sub_type: string;
  description?: string | null;
  requires_verification: boolean;
  is_active: boolean;
  created_at: string;
}

export interface Location {
  id: number;
  name: string;
  code: string;
  building: string;
  floor?: string | null;
  room?: string | null;
  parent_id?: number | null;
  is_active: boolean;
  created_at: string;
}

export interface RoutingRule {
  id: number;
  issue_type_id?: number | null;
  location_id?: number | null;
  handler_id: number;
  priority: number;
  is_active: boolean;
  created_at: string;
  handler?: User | null;
  issue_type?: IssueType | null;
  location?: Location | null;
}

export interface Report {
  id: number;
  issue_id?: number | null;
  reporter_id: number;
  issue_type_id: number;
  location_id: number;
  specific_asset?: string | null;
  description: string;
  photo_url?: string | null;
  status: ReportStatus;
  created_at: string;
  reporter?: User | null;
  issue_type?: IssueType | null;
  location?: Location | null;
}

export interface DuplicateIssueCandidate {
  issue_id: number;
  title: string;
  description: string;
  status: string;
  created_at: string;
  report_count: number;
  location_name: string;
  issue_category: string;
  issue_sub_type: string;
  specific_asset?: string | null;
}

export interface DuplicateCheckResponse {
  has_match: boolean;
  message: string;
  candidates: DuplicateIssueCandidate[];
}

export interface ResolutionEvidence {
  id: number;
  issue_id: number;
  submitted_by_id: number;
  evidence_type: EvidenceType;
  notes: string;
  attachment_url?: string | null;
  created_at: string;
  submitted_by?: User | null;
}

export interface Verification {
  id: number;
  issue_id: number;
  verified_by_id: number;
  status: VerificationStatus;
  comment?: string | null;
  created_at: string;
  verified_by?: User | null;
}

export interface Escalation {
  id: number;
  issue_id: number;
  escalated_by_id: number;
  escalated_to_id?: number | null;
  reason: string;
  previous_status: string;
  history_snapshot?: string | null;
  created_at: string;
  escalated_by?: User | null;
  escalated_to?: User | null;
}

export interface TimelineEvent {
  id: number;
  issue_id: number;
  actor_id?: number | null;
  event_type: TimelineEventType;
  from_status?: IssueStatus | null;
  to_status?: IssueStatus | null;
  title: string;
  details?: string | null;
  metadata_json?: string | null;
  created_at: string;
  actor?: User | null;
}

export interface Issue {
  id: number;
  issue_type_id: number;
  location_id: number;
  specific_asset?: string | null;
  title: string;
  description: string;
  status: IssueStatus;
  current_handler_id?: number | null;
  requires_verification: boolean;
  created_at: string;
  updated_at: string;
  report_count: number;
  current_handler?: User | null;
  issue_type?: IssueType | null;
  location?: Location | null;
}

export interface IssueDetail extends Issue {
  reports: Report[];
  escalations: Escalation[];
  evidences: ResolutionEvidence[];
  verifications: Verification[];
  timeline_events: TimelineEvent[];
}

export interface Notification {
  id: number;
  user_id: number;
  issue_id?: number | null;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface TaxonomyData {
  issue_types: IssueType[];
  locations: Location[];
  handlers: User[];
}

