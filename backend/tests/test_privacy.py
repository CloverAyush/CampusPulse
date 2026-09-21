"""Students can browse the campus board, which means other people's reports are
visible. Their contact details are not."""

import pytest

from tests.conftest import auth_headers


@pytest.fixture
def issue_reported_by_aarav(submit_report, campus, db):
    campus["aarav"].phone = "+91-9876543210"
    campus["aarav"].department = "Computer Science"
    db.commit()

    response = submit_report(campus["aarav"])
    return response.json()["issue_id"]


def test_an_unaffected_student_sees_the_issue_but_not_who_reported_it(client, campus, issue_reported_by_aarav):
    detail = client.get(f"/api/v1/issues/{issue_reported_by_aarav}",
                        headers=auth_headers(campus["rohit"])).json()

    assert detail["affected_student_count"] == 1
    assert detail["viewer_is_affected"] is False
    assert all(report["reporter"] is None for report in detail["reports"])

    body = client.get(f"/api/v1/issues/{issue_reported_by_aarav}",
                      headers=auth_headers(campus["rohit"])).text
    assert "aarav@student.edu" not in body
    assert "9876543210" not in body
    assert "Aarav Sharma" not in body


def test_an_affected_student_sees_names_but_still_no_contact_details(client, campus, issue_reported_by_aarav, submit_report):
    submit_report(campus["priya"], existing_issue_id=issue_reported_by_aarav)

    response = client.get(f"/api/v1/issues/{issue_reported_by_aarav}",
                          headers=auth_headers(campus["priya"]))
    detail = response.json()

    assert detail["viewer_is_affected"] is True
    assert any(r["reporter"] and r["reporter"]["full_name"] == "Aarav Sharma" for r in detail["reports"])
    assert all(r["reporter_contact"] is None for r in detail["reports"])
    assert "aarav@student.edu" not in response.text
    assert "9876543210" not in response.text


def test_the_assigned_handler_can_reach_the_people_who_reported_it(client, campus, issue_reported_by_aarav):
    response = client.get(f"/api/v1/issues/{issue_reported_by_aarav}",
                          headers=auth_headers(campus["facilities"]))

    contacts = [r["reporter_contact"] for r in response.json()["reports"]]
    assert contacts[0]["email"] == "aarav@student.edu"
    assert contacts[0]["phone"] == "+91-9876543210"


def test_an_unrelated_handler_does_not_get_contact_details(client, campus, issue_reported_by_aarav):
    response = client.get(f"/api/v1/issues/{issue_reported_by_aarav}",
                          headers=auth_headers(campus["it_handler"]))

    assert response.status_code == 200
    assert "aarav@student.edu" not in response.text


def test_the_timeline_masks_student_names_from_unaffected_students(client, campus, issue_reported_by_aarav):
    response = client.get(f"/api/v1/issues/{issue_reported_by_aarav}/history",
                          headers=auth_headers(campus["rohit"]))

    actors = {event["actor"]["full_name"] for event in response.json() if event["actor"]}
    assert "Aarav Sharma" not in actors
    assert "A student" in actors


def test_the_report_form_taxonomy_does_not_leak_staff_contact_details(client, campus):
    response = client.get("/api/v1/admin/taxonomies", headers=auth_headers(campus["aarav"]))

    assert response.status_code == 200
    assert "facilities@campus.edu" not in response.text
    assert "handlers" not in response.json()


def test_the_handler_dropdown_exposes_names_only(client, campus):
    response = client.get("/api/v1/admin/handlers", headers=auth_headers(campus["facilities"]))

    assert response.status_code == 200
    assert "facilities@campus.edu" not in response.text
    assert all(set(item) == {"id", "full_name", "role"} for item in response.json())


def test_error_responses_never_expose_internals(client, campus):
    response = client.get("/api/v1/issues/999999", headers=auth_headers(campus["aarav"]))

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert "Traceback" not in response.text
    assert "request_id" in body["error"]
