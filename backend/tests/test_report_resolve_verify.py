from tests.conftest import get_auth_headers
from app.models.enums import IssueStatus, EvidenceType, VerificationStatus

def test_full_report_resolve_verify_happy_path(client, seed_data):
    """
    Test complete end-to-end happy path:
    Student submits report -> Handler marks IN_PROGRESS -> Handler resolves with Evidence
    -> Student confirms verification -> Issue is VERIFIED_CLOSED.
    """
    student_headers = get_auth_headers(seed_data["student_aarav"])
    handler_headers = get_auth_headers(seed_data["facilities_handler"])

    # 1. Student submits report
    resp_report = client.post(
        "/api/v1/reports",
        json={
            "issue_type_id": seed_data["fan_type"].id,
            "location_id": seed_data["room_204"].id,
            "specific_asset": "Fan 2",
            "description": "Blades are wobbling dangerously."
        },
        headers=student_headers
    )
    assert resp_report.status_code == 201
    issue_id = resp_report.json()["issue_id"]

    # 2. Handler checks assigned issues and marks IN_PROGRESS
    resp_progress = client.post(f"/api/v1/issues/{issue_id}/progress", headers=handler_headers)
    assert resp_progress.status_code == 200
    assert resp_progress.json()["status"] == IssueStatus.IN_PROGRESS.value

    # 3. Handler resolves issue with evidence
    resp_resolve = client.post(
        f"/api/v1/issues/{issue_id}/resolve",
        json={
            "evidence_type": EvidenceType.MAINTENANCE_RECORD.value,
            "notes": "Replaced the central shaft and tightened mounting bracket.",
            "attachment_url": "https://example.com/repair_receipt.jpg"
        },
        headers=handler_headers
    )
    assert resp_resolve.status_code == 200
    assert resp_resolve.json()["evidence_type"] == EvidenceType.MAINTENANCE_RECORD.value

    # Check that issue is now RESOLVED_PENDING_VERIFICATION
    resp_issue = client.get(f"/api/v1/issues/{issue_id}", headers=student_headers)
    assert resp_issue.json()["status"] == IssueStatus.RESOLVED_PENDING_VERIFICATION.value

    # 4. Student verifies and confirms resolution
    resp_verify = client.post(
        f"/api/v1/issues/{issue_id}/verify",
        json={
            "status": VerificationStatus.CONFIRMED.value,
            "comment": "Checked during morning class, fan is working quietly now. Thanks!"
        },
        headers=student_headers
    )
    assert resp_verify.status_code == 200
    assert resp_verify.json()["status"] == VerificationStatus.CONFIRMED.value

    # 5. Issue is now VERIFIED_CLOSED
    resp_issue_final = client.get(f"/api/v1/issues/{issue_id}", headers=student_headers)
    assert resp_issue_final.json()["status"] == IssueStatus.VERIFIED_CLOSED.value

def test_dispute_verification_reopens_issue(client, seed_data):
    """
    Test dispute path:
    Student disputes resolution -> Issue status changes back to REOPENED.
    """
    student_headers = get_auth_headers(seed_data["student_aarav"])
    handler_headers = get_auth_headers(seed_data["facilities_handler"])

    # 1. Student submits report
    resp_report = client.post(
        "/api/v1/reports",
        json={
            "issue_type_id": seed_data["fan_type"].id,
            "location_id": seed_data["room_204"].id,
            "description": "Speed regulator does not adjust speed."
        },
        headers=student_headers
    )
    issue_id = resp_report.json()["issue_id"]

    # 2. Handler marks resolved
    client.post(f"/api/v1/issues/{issue_id}/progress", headers=handler_headers)
    client.post(
        f"/api/v1/issues/{issue_id}/resolve",
        json={
            "evidence_type": EvidenceType.DESCRIPTION.value,
            "notes": "Reset main circuit breaker."
        },
        headers=handler_headers
    )

    # 3. Student disputes resolution
    resp_dispute = client.post(
        f"/api/v1/issues/{issue_id}/verify",
        json={
            "status": VerificationStatus.DISPUTED.value,
            "comment": "Regulator is still stuck on high speed only."
        },
        headers=student_headers
    )
    assert resp_dispute.status_code == 200

    # 4. Verify issue is now REOPENED
    resp_issue = client.get(f"/api/v1/issues/{issue_id}", headers=student_headers)
    assert resp_issue.json()["status"] == IssueStatus.REOPENED.value

def test_issue_type_without_verification_closes_directly(client, seed_data):
    """
    Test that for issue types with requires_verification=False (e.g. Cleanliness),
    marking resolved transitions directly to VERIFIED_CLOSED.
    """
    student_headers = get_auth_headers(seed_data["student_aarav"])
    handler_headers = get_auth_headers(seed_data["facilities_handler"])

    resp_report = client.post(
        "/api/v1/reports",
        json={
            "issue_type_id": seed_data["cleanliness_type"].id,
            "location_id": seed_data["room_204"].id,
            "description": "Dustbin overflowing in back corner."
        },
        headers=student_headers
    )
    issue_id = resp_report.json()["issue_id"]

    # Handler resolves with evidence
    client.post(
        f"/api/v1/issues/{issue_id}/resolve",
        json={
            "evidence_type": EvidenceType.PHOTO.value,
            "notes": "Dustbin emptied and sanitized by housekeeping.",
            "attachment_url": "https://example.com/clean_photo.jpg"
        },
        headers=handler_headers
    )

    # Verify directly closed without needing student confirmation
    resp_issue = client.get(f"/api/v1/issues/{issue_id}", headers=student_headers)
    assert resp_issue.json()["status"] == IssueStatus.VERIFIED_CLOSED.value

