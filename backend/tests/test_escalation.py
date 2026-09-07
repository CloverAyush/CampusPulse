import json
from tests.conftest import get_auth_headers
from app.models.enums import IssueStatus, EvidenceType

def test_escalation_flow_and_history_snapshot(client, seed_data):
    """
    Test handler escalation:
    1. Student reports complex issue.
    2. Handler marks in progress, realizes replacement budget requires Dean approval, and escalates.
    3. Escalation record contains full case history snapshot.
    4. Higher Authority views history timeline and resolves issue directly.
    """
    student_headers = get_auth_headers(seed_data["student_aarav"])
    handler_headers = get_auth_headers(seed_data["facilities_handler"])
    dean_headers = get_auth_headers(seed_data["dean_authority"])

    # 1. Student reports issue
    resp_report = client.post(
        "/api/v1/reports",
        json={
            "issue_type_id": seed_data["fan_type"].id,
            "location_id": seed_data["room_204"].id,
            "specific_asset": "Master Exhaust Fan",
            "description": "Entire room exhaust motor has burned out and requires complete replacement."
        },
        headers=student_headers
    )
    issue_id = resp_report.json()["issue_id"]

    # 2. Handler marks in progress
    client.post(f"/api/v1/issues/{issue_id}/progress", headers=handler_headers)

    # 3. Handler attempts escalation with empty reason -> Should fail
    resp_fail = client.post(
        f"/api/v1/issues/{issue_id}/escalate",
        json={"reason": "   "},
        headers=handler_headers
    )
    assert resp_fail.status_code == 400

    # 4. Handler escalates with valid reason to Dean
    escalate_reason = "Motor unit requires complete commercial replacement costing > 15,000 INR. Exceeds department approval threshold."
    resp_escalate = client.post(
        f"/api/v1/issues/{issue_id}/escalate",
        json={
            "reason": escalate_reason,
            "escalated_to_id": seed_data["dean_authority"].id
        },
        headers=handler_headers
    )
    assert resp_escalate.status_code == 200
    escalation_data = resp_escalate.json()
    assert escalation_data["reason"] == escalate_reason
    assert escalation_data["escalated_by_id"] == seed_data["facilities_handler"].id
    assert escalation_data["escalated_to_id"] == seed_data["dean_authority"].id

    # Verify history snapshot exists and is valid JSON
    assert escalation_data["history_snapshot"] is not None
    snapshot = json.loads(escalation_data["history_snapshot"])
    assert snapshot["issue_id"] == issue_id
    assert len(snapshot["reports"]) >= 1

    # 5. Verify issue status is now ESCALATED
    resp_issue = client.get(f"/api/v1/issues/{issue_id}", headers=dean_headers)
    assert resp_issue.json()["status"] == IssueStatus.ESCALATED.value

    # 6. Dean views full chronological history
    resp_history = client.get(f"/api/v1/issues/{issue_id}/history", headers=dean_headers)
    assert resp_history.status_code == 200
    timeline = resp_history.json()
    event_types = [t["event_type"] for t in timeline]
    assert "REPORT_SUBMITTED" in event_types
    assert "ROUTED" in event_types
    assert "STARTED_PROGRESS" in event_types
    assert "ESCALATED" in event_types

    # 7. Dean resolves the escalated issue with executive procurement approval
    resp_resolve = client.post(
        f"/api/v1/issues/{issue_id}/resolve",
        json={
            "evidence_type": EvidenceType.MAINTENANCE_RECORD.value,
            "notes": "Deanery PO #4092 approved and replacement motor installed by vendor.",
            "attachment_url": "https://example.com/po_4092.pdf"
        },
        headers=dean_headers
    )
    assert resp_resolve.status_code == 200

