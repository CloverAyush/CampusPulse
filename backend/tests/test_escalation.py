import json

from app.models.enums import IssueStatus
from tests.conftest import auth_headers


def _reported_issue(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"]).json()["issue_id"]
    submit_report(campus["priya"], existing_issue_id=issue_id)
    client.post(f"/api/v1/issues/{issue_id}/progress", headers=auth_headers(campus["facilities"]))
    return issue_id


def test_escalation_hands_over_the_complete_case(client, campus, submit_report):
    issue_id = _reported_issue(client, campus, submit_report)

    response = client.post(
        f"/api/v1/issues/{issue_id}/escalate",
        json={"reason": "Replacing the whole circuit needs a budget sanction beyond my authority"},
        headers=auth_headers(campus["facilities"]),
    )

    assert response.status_code == 200
    escalation = response.json()
    assert escalation["escalated_to_id"] == campus["dean"].id
    assert escalation["previous_status"] == IssueStatus.IN_PROGRESS.value

    snapshot = json.loads(escalation["history_snapshot"])
    assert snapshot["affected_student_count"] == 2
    assert len(snapshot["reports"]) == 2
    assert len(snapshot["timeline"]) >= 4
    assert snapshot["location"] == "Room 204"


def test_the_authority_is_notified_and_sees_it_in_their_queue(client, campus, submit_report):
    issue_id = _reported_issue(client, campus, submit_report)
    client.post(f"/api/v1/issues/{issue_id}/escalate",
                json={"reason": "This requires an external vendor contract to be raised"},
                headers=auth_headers(campus["facilities"]))

    notifications = client.get("/api/v1/notifications", headers=auth_headers(campus["dean"])).json()
    queue = client.get("/api/v1/issues?scope=escalated", headers=auth_headers(campus["dean"])).json()

    assert notifications["total"] == 1
    assert queue["total"] == 1
    assert queue["items"][0]["id"] == issue_id


def test_affected_students_are_told_their_issue_was_escalated(client, campus, submit_report):
    issue_id = _reported_issue(client, campus, submit_report)
    client.post(f"/api/v1/issues/{issue_id}/escalate",
                json={"reason": "The rewiring work needs approval from the Dean's office"},
                headers=auth_headers(campus["facilities"]))

    for student in ("aarav", "priya"):
        messages = client.get("/api/v1/notifications", headers=auth_headers(campus[student])).json()["items"]
        assert any("escalated" in item["title"].lower() for item in messages)


def test_an_issue_cannot_be_escalated_twice(client, campus, submit_report):
    issue_id = _reported_issue(client, campus, submit_report)
    payload = {"reason": "This needs a budget sanction well beyond my authority"}

    assert client.post(f"/api/v1/issues/{issue_id}/escalate", json=payload,
                       headers=auth_headers(campus["facilities"])).status_code == 200
    assert client.post(f"/api/v1/issues/{issue_id}/escalate", json=payload,
                       headers=auth_headers(campus["facilities"])).status_code == 409


def test_an_authority_can_resolve_an_escalated_issue(client, campus, submit_report):
    issue_id = _reported_issue(client, campus, submit_report)
    client.post(f"/api/v1/issues/{issue_id}/escalate",
                json={"reason": "Needs a vendor contract that only the Dean can authorise"},
                headers=auth_headers(campus["facilities"]))

    response = client.post(
        f"/api/v1/issues/{issue_id}/resolve",
        json={"evidence_type": "maintenance_record", "notes": "Vendor completed the rewiring, invoice attached."},
        headers=auth_headers(campus["dean"]),
    )

    assert response.status_code == 200


def test_reassignment_takes_an_escalated_issue_back_into_progress(client, campus, submit_report):
    issue_id = _reported_issue(client, campus, submit_report)
    client.post(f"/api/v1/issues/{issue_id}/escalate",
                json={"reason": "I do not have access to the electrical riser on this floor"},
                headers=auth_headers(campus["facilities"]))

    response = client.post(f"/api/v1/issues/{issue_id}/reassign",
                           json={"handler_id": campus["it_handler"].id, "reason": "Riser access sits with IT"},
                           headers=auth_headers(campus["dean"]))

    assert response.status_code == 200
    assert response.json()["status"] == IssueStatus.IN_PROGRESS.value
    assert response.json()["current_handler"]["full_name"] == "Amit Deshmukh"
