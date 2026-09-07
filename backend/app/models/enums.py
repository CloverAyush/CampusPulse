import enum

class UserRole(str, enum.Enum):
    STUDENT = "student"
    HANDLER = "handler"
    HIGHER_AUTHORITY = "higher_authority"
    ADMIN = "admin"

class IssueStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    ESCALATED = "ESCALATED"
    RESOLVED_PENDING_VERIFICATION = "RESOLVED_PENDING_VERIFICATION"
    VERIFIED_CLOSED = "VERIFIED_CLOSED"
    REOPENED = "REOPENED"

class ReportStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    LINKED_TO_ISSUE = "LINKED_TO_ISSUE"

class EvidenceType(str, enum.Enum):
    PHOTO = "photo"
    DESCRIPTION = "description"
    MAINTENANCE_RECORD = "maintenance_record"
    SCREENSHOT = "screenshot"
    OTHER = "other"

class VerificationStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"

class TimelineEventType(str, enum.Enum):
    REPORT_SUBMITTED = "REPORT_SUBMITTED"
    REPORT_LINKED = "REPORT_LINKED"
    ISSUE_CREATED = "ISSUE_CREATED"
    ROUTED = "ROUTED"
    STATUS_CHANGED = "STATUS_CHANGED"
    STARTED_PROGRESS = "STARTED_PROGRESS"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    VERIFIED = "VERIFIED"
    DISPUTED = "DISPUTED"
    REOPENED = "REOPENED"
    REASSIGNED = "REASSIGNED"

