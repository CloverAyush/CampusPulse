import pytest

from tests.conftest import auth_headers


@pytest.mark.parametrize(
    "password,should_pass",
    [
        ("x", False),
        ("short1", False),
        ("alllettersnodigits", False),
        ("1234567890123", False),
        ("  Passw0rdLong  ", False),
        ("Passw0rdLong", True),
    ],
)
def test_password_policy_is_enforced_at_registration(client, campus, password, should_pass):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": f"user{abs(hash(password))}@campus.edu", "full_name": "Test User", "password": password},
    )

    assert (response.status_code == 201) is should_pass


def test_duplicate_email_registration_is_rejected_cleanly(client, campus):
    payload = {"email": "aarav@student.edu", "full_name": "Impostor", "password": "Passw0rdLong"}

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_login_does_not_reveal_whether_an_email_exists(client, campus):
    unknown = client.post("/api/v1/auth/login",
                          json={"email": "nobody@campus.edu", "password": "Passw0rdLong"})
    wrong_password = client.post("/api/v1/auth/login",
                                 json={"email": "aarav@student.edu", "password": "Passw0rdLong"})

    assert unknown.status_code == wrong_password.status_code
    assert unknown.json()["error"]["message"] == wrong_password.json()["error"]["message"]


@pytest.mark.parametrize(
    "photo_url,should_pass",
    [
        ("javascript:alert(document.cookie)", False),
        ("data:text/html;base64,PHNjcmlwdD4=", False),
        ("http://example.com/photo.jpg", False),
        ("https://localhost/photo.jpg", False),
        ("https://127.0.0.1:8000/admin", False),
        ("file:///etc/passwd", False),
        ("https://drive.example.edu/photo.jpg", True),
        (None, True),
    ],
)
def test_attachment_urls_are_restricted_to_safe_schemes_and_hosts(client, campus, photo_url, should_pass):
    payload = {
        "issue_type_id": campus["fan_type"].id,
        "location_id": campus["room_204"].id,
        "description": "The fan in this room has completely stopped working.",
    }
    if photo_url is not None:
        payload["photo_url"] = photo_url

    response = client.post("/api/v1/reports", json=payload, headers=auth_headers(campus["aarav"]))

    assert (response.status_code == 201) is should_pass


@pytest.mark.parametrize("description", ["", "   ", "too short"])
def test_reports_require_a_real_description(client, campus, description):
    response = client.post(
        "/api/v1/reports",
        json={"issue_type_id": campus["fan_type"].id, "location_id": campus["room_204"].id,
              "description": description},
        headers=auth_headers(campus["aarav"]),
    )

    assert response.status_code == 422


def test_oversized_text_is_rejected_rather_than_stored(client, campus):
    response = client.post(
        "/api/v1/reports",
        json={"issue_type_id": campus["fan_type"].id, "location_id": campus["room_204"].id,
              "description": "a" * 5000},
        headers=auth_headers(campus["aarav"]),
    )

    assert response.status_code == 422


def test_resolution_requires_a_substantive_note(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"]).json()["issue_id"]

    response = client.post(
        f"/api/v1/issues/{issue_id}/resolve",
        json={"evidence_type": "description", "notes": "fixed"},
        headers=auth_headers(campus["facilities"]),
    )

    assert response.status_code == 422


def test_escalation_requires_a_stated_reason(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"]).json()["issue_id"]

    response = client.post(
        f"/api/v1/issues/{issue_id}/escalate",
        json={"reason": "no"},
        headers=auth_headers(campus["facilities"]),
    )

    assert response.status_code == 422


def test_a_location_cannot_become_its_own_ancestor(client, campus):
    response = client.put(
        f"/api/v1/admin/locations/{campus['block_a'].id}",
        json={"parent_id": campus["room_204"].id},
        headers=auth_headers(campus["admin"]),
    )

    assert response.status_code == 422
    assert "loop" in response.json()["error"]["message"].lower()


def test_a_location_cannot_be_its_own_parent(client, campus):
    response = client.put(
        f"/api/v1/admin/locations/{campus['block_a'].id}",
        json={"parent_id": campus["block_a"].id},
        headers=auth_headers(campus["admin"]),
    )

    assert response.status_code == 422


def test_routing_rules_cannot_target_a_student(client, campus):
    response = client.post(
        "/api/v1/admin/routing-rules",
        json={"handler_id": campus["aarav"].id},
        headers=auth_headers(campus["admin"]),
    )

    assert response.status_code == 422


def test_pagination_bounds_are_enforced(client, campus):
    assert client.get("/api/v1/issues?limit=0", headers=auth_headers(campus["admin"])).status_code == 422
    assert client.get("/api/v1/issues?limit=9999", headers=auth_headers(campus["admin"])).status_code == 422
    assert client.get("/api/v1/issues?offset=-1", headers=auth_headers(campus["admin"])).status_code == 422
