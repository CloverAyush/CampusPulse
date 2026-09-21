from app.models.enums import IssueStatus
from tests.conftest import auth_headers


def test_report_routes_to_the_configured_handler(client, campus, submit_report):
    response = submit_report(campus["aarav"], asset="Ceiling fan 2")

    assert response.status_code == 201
    issue_id = response.json()["issue_id"]

    detail = client.get(f"/api/v1/issues/{issue_id}", headers=auth_headers(campus["facilities"])).json()
    assert detail["current_handler"]["full_name"] == "Rajesh Sharma"
    assert detail["status"] == IssueStatus.OPEN.value
    assert detail["needs_triage"] is False
    assert "Ceiling fan 2" in detail["title"]


def test_the_handler_is_notified_when_an_issue_is_routed_to_them(client, campus, submit_report):
    submit_report(campus["aarav"])

    notifications = client.get("/api/v1/notifications", headers=auth_headers(campus["facilities"])).json()

    assert notifications["total"] == 1
    assert "routed to you" in notifications["items"][0]["message"]


def test_full_lifecycle_from_report_to_verified_close(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"]).json()["issue_id"]
    handler = auth_headers(campus["facilities"])
    student = auth_headers(campus["aarav"])

    assert client.post(f"/api/v1/issues/{issue_id}/progress", headers=handler).status_code == 200

    resolve = client.post(
        f"/api/v1/issues/{issue_id}/resolve",
        json={"evidence_type": "photo", "notes": "Replaced the fan regulator and tested it.",
              "attachment_url": "https://drive.example.edu/fan-fixed.jpg"},
        headers=handler,
    )
    assert resolve.status_code == 200
    assert resolve.json()["resolution_round"] == 1

    pending = client.get(f"/api/v1/issues/{issue_id}", headers=student).json()
    assert pending["status"] == IssueStatus.RESOLVED_PENDING_VERIFICATION.value
    assert pending["viewer_can_verify"] is True

    verify = client.post(f"/api/v1/issues/{issue_id}/verify",
                         json={"status": "confirmed", "comment": "Working now, thanks."},
                         headers=student)
    assert verify.status_code == 200

    closed = client.get(f"/api/v1/issues/{issue_id}", headers=student).json()
    assert closed["status"] == IssueStatus.VERIFIED_CLOSED.value


def test_disputing_a_resolution_reopens_the_issue(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"]).json()["issue_id"]
    handler = auth_headers(campus["facilities"])
    student = auth_headers(campus["aarav"])

    client.post(f"/api/v1/issues/{issue_id}/resolve",
                json={"evidence_type": "description", "notes": "Tightened the mounting bracket."},
                headers=handler)
    client.post(f"/api/v1/issues/{issue_id}/verify",
                json={"status": "disputed", "comment": "Still not spinning at all."},
                headers=student)

    reopened = client.get(f"/api/v1/issues/{issue_id}", headers=handler).json()
    assert reopened["status"] == IssueStatus.REOPENED.value

    second = client.post(f"/api/v1/issues/{issue_id}/resolve",
                         json={"evidence_type": "maintenance_record", "notes": "Replaced the entire motor unit."},
                         headers=handler)
    assert second.status_code == 200
    assert second.json()["resolution_round"] == 2

    assert client.post(f"/api/v1/issues/{issue_id}/verify", json={"status": "confirmed"},
                       headers=student).status_code == 200


def test_an_issue_type_that_does_not_require_verification_closes_immediately(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"], issue_type=campus["bin_type"],
                             location=campus["canteen"],
                             description="The bin by the canteen counter is overflowing again.").json()["issue_id"]

    client.post(f"/api/v1/issues/{issue_id}/resolve",
                json={"evidence_type": "description", "notes": "Emptied and the area was swept."},
                headers=auth_headers(campus["estate"]))

    detail = client.get(f"/api/v1/issues/{issue_id}", headers=auth_headers(campus["aarav"])).json()
    assert detail["status"] == IssueStatus.VERIFIED_CLOSED.value


def test_an_issue_cannot_be_resolved_twice(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"]).json()["issue_id"]
    handler = auth_headers(campus["facilities"])
    evidence = {"evidence_type": "description", "notes": "Replaced the fan regulator unit."}

    assert client.post(f"/api/v1/issues/{issue_id}/resolve", json=evidence, headers=handler).status_code == 200

    second = client.post(f"/api/v1/issues/{issue_id}/resolve", json=evidence, headers=handler)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "invalid_transition"


def test_a_closed_issue_cannot_be_reopened_by_a_handler_action(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"], issue_type=campus["bin_type"], location=campus["canteen"],
                             description="Bin outside the canteen has not been cleared.").json()["issue_id"]
    handler = auth_headers(campus["estate"])

    client.post(f"/api/v1/issues/{issue_id}/resolve",
                json={"evidence_type": "description", "notes": "Cleared and disinfected the area."},
                headers=handler)

    assert client.post(f"/api/v1/issues/{issue_id}/progress", headers=handler).status_code == 409
    assert client.post(f"/api/v1/issues/{issue_id}/escalate",
                       json={"reason": "This needs the Dean to allocate a bigger budget"},
                       headers=handler).status_code == 409


def test_a_student_cannot_verify_before_a_resolution_exists(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"]).json()["issue_id"]

    response = client.post(f"/api/v1/issues/{issue_id}/verify", json={"status": "confirmed"},
                           headers=auth_headers(campus["aarav"]))

    assert response.status_code == 409


def test_a_student_who_did_not_report_it_cannot_verify(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"]).json()["issue_id"]
    client.post(f"/api/v1/issues/{issue_id}/resolve",
                json={"evidence_type": "description", "notes": "Replaced the regulator switch."},
                headers=auth_headers(campus["facilities"]))

    response = client.post(f"/api/v1/issues/{issue_id}/verify", json={"status": "confirmed"},
                           headers=auth_headers(campus["rohit"]))

    assert response.status_code == 403


def test_a_student_cannot_verify_the_same_resolution_twice(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"]).json()["issue_id"]
    student = auth_headers(campus["aarav"])

    client.post(f"/api/v1/issues/{issue_id}/resolve",
                json={"evidence_type": "description", "notes": "Replaced the regulator switch."},
                headers=auth_headers(campus["facilities"]))

    assert client.post(f"/api/v1/issues/{issue_id}/verify", json={"status": "disputed"},
                       headers=student).status_code == 200
    client.post(f"/api/v1/issues/{issue_id}/resolve",
                json={"evidence_type": "description", "notes": "Second attempt, replaced the motor."},
                headers=auth_headers(campus["facilities"]))

    first = client.post(f"/api/v1/issues/{issue_id}/verify", json={"status": "confirmed"}, headers=student)
    assert first.status_code == 200


def test_an_unroutable_issue_reaches_the_catch_all_handler(client, campus, submit_report):
    response = submit_report(campus["aarav"], issue_type=campus["misc_type"], location=campus["canteen"],
                             description="The noticeboard by the canteen has fallen off the wall.")

    issue_id = response.json()["issue_id"]
    detail = client.get(f"/api/v1/issues/{issue_id}", headers=auth_headers(campus["estate"])).json()

    assert detail["current_handler"]["full_name"] == "Estate Office"
    assert detail["needs_triage"] is False


def test_an_issue_with_no_rules_at_all_is_flagged_for_triage_and_admins_are_told(client, db, campus, submit_report):
    from app.models.routing_rule import RoutingRule

    db.query(RoutingRule).delete()
    db.commit()

    issue_id = submit_report(campus["aarav"]).json()["issue_id"]

    detail = client.get(f"/api/v1/issues/{issue_id}", headers=auth_headers(campus["admin"])).json()
    assert detail["needs_triage"] is True
    assert detail["current_handler"] is None

    admin_notifications = client.get("/api/v1/notifications", headers=auth_headers(campus["admin"])).json()
    assert admin_notifications["total"] == 1
    assert "triage" in admin_notifications["items"][0]["title"].lower()

    triage_queue = client.get("/api/v1/issues?scope=triage", headers=auth_headers(campus["admin"])).json()
    assert triage_queue["total"] == 1
