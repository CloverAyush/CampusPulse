export type UserRole = "student" | "handler" | "higher_authority" | "admin";

export type IssueStatus =
  | "OPEN"
  | "IN_PROGRESS"
  | "ESCALATED"
  | "RESOLVED_PENDING_VERIFICATION"
  | "VERIFIED_CLOSED"
  | "REOPENED";

export type ReportStatus = "SUBMITTED" | "LINKED_TO_ISSUE";
export type EvidenceType = "photo" | "description" | "maintenance_record" | "screenshot" | "other";
export type VerificationStatus = "confirmed" | "disputed";
export type IssueScope = "mine" | "all" | "assigned" | "escalated" | "triage";

export interface UserPublic {
  id: number;
  full_name: string;
  role: UserRole;
}

export interface User extends UserPublic {
  email: string;
  department?: string | null;
  phone?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    request_id?: string;
    details?: { field: string; message: string }[];
  };
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

export interface TaxonomyData {
  issue_types: IssueType[];
  locations: Location[];
}

export interface RoutingRule {
  id: number;
  issue_type_id?: number | null;
  location_id?: number | null;
  handler_id: number;
  priority: number;
  is_active: boolean;
  created_at: string;
  handler?: UserPublic | null;
  issue_type?: IssueType | null;
  location?: Location | null;
}

export interface RoutingPreview {
  handler: UserPublic | null;
  matched_rule_id: number | null;
  match_kind: string;
}

export interface ReporterContact {
  email: string;
  phone?: string | null;
  department?: string | null;
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
  reporter?: UserPublic | null;
  reporter_contact?: ReporterContact | null;
  issue_type?: IssueType | null;
  location?: Location | null;
}

export interface ResolutionEvidence {
  id: number;
  issue_id: number;
  submitted_by_id: number;
  evidence_type: EvidenceType;
  notes: string;
  attachment_url?: string | null;
  resolution_round: number;
  created_at: string;
  submitted_by?: UserPublic | null;
}

export interface Verification {
  id: number;
  issue_id: number;
  verified_by_id: number;
  status: VerificationStatus;
  comment?: string | null;
  resolution_round: number;
  created_at: string;
  verified_by?: UserPublic | null;
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
  escalated_by?: UserPublic | null;
  escalated_to?: UserPublic | null;
}

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

export interface TimelineEvent {
  id: number;
  issue_id: number;
  actor_id?: number | null;
  event_type: TimelineEventType;
  from_status?: IssueStatus | null;
  to_status?: IssueStatus | null;
  title: string;
  details?: string | null;
  created_at: string;
  actor?: UserPublic | null;
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
  needs_triage: boolean;
  affected_student_count: number;
  report_count: number;
  created_at: string;
  updated_at: string;
  current_handler?: UserPublic | null;
  issue_type?: IssueType | null;
  location?: Location | null;
}

export interface IssueDetail extends Issue {
  reports: Report[];
  escalations: Escalation[];
  evidences: ResolutionEvidence[];
  verifications: Verification[];
  timeline_events: TimelineEvent[];
  viewer_is_affected: boolean;
  viewer_can_verify: boolean;
}

export interface DuplicateIssueCandidate {
  issue_id: number;
  title: string;
  description: string;
  status: IssueStatus;
  created_at: string;
  affected_student_count: number;
  report_count: number;
  location_name: string;
  issue_category: string;
  issue_sub_type: string;
  specific_asset?: string | null;
  asset_match: boolean;
  already_reported_by_you: boolean;
}

export interface DuplicateCheckResponse {
  has_match: boolean;
  message: string;
  candidates: DuplicateIssueCandidate[];
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
