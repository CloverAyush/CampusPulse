"""Every endpoint, every role. The previous suite only proved the happy path worked,
which is how a public registration endpoint that minted admin tokens survived."""

import pytest

from tests.conftest import auth_headers

ROLES = ["aarav", "facilities", "dean", "admin"]


@pytest.fixture
def an_issue(submit_report, campus):
    response = submit_report(campus["aarav"])
    assert response.status_code == 201
    return response.json()["issue_id"]


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/v1/auth/me"),
        ("get", "/api/v1/issues"),
        ("get", "/api/v1/reports/my"),
        ("get", "/api/v1/notifications"),
        ("get", "/api/v1/admin/taxonomies"),
        ("post", "/api/v1/reports"),
        ("post", "/api/v1/admin/routing-rules"),
    ],
)
def test_every_endpoint_rejects_anonymous_callers(client, campus, method, path):
    response = client.request(method.upper(), path, json={} if method == "post" else None)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_a_forged_token_signed_with_another_key_is_rejected(client, campus):
    import jwt

    forged = jwt.encode({"sub": str(campus["admin"].id), "role": "admin", "exp": 4102444800},
                        "a-different-secret-entirely", algorithm="HS256")

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})

    assert response.status_code == 401


def test_registration_cannot_grant_a_role(client, campus):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "attacker@campus.edu", "full_name": "Mallory",
              "password": "Passw0rdLong", "role": "admin"},
    )

    assert response.status_code == 201
    assert response.json()["user"]["role"] == "student"


def test_the_demo_login_endpoint_no_longer_exists(client, campus):
    response = client.post("/api/v1/auth/demo-login", json={"role": "admin"})

    assert response.status_code in (404, 405)


def test_the_seed_endpoint_no_longer_exists(client, campus):
    response = client.post("/api/v1/admin/seed-data", headers=auth_headers(campus["admin"]))

    assert response.status_code in (404, 405)


@pytest.mark.parametrize("actor,expected", [("aarav", 403), ("facilities", 403), ("dean", 403), ("admin", 201)])
def test_only_admins_can_create_routing_rules(client, campus, actor, expected):
    response = client.post(
        "/api/v1/admin/routing-rules",
        json={"handler_id": campus["facilities"].id, "priority": 5},
        headers=auth_headers(campus[actor]),
    )

    assert response.status_code == expected


@pytest.mark.parametrize("actor,expected", [("aarav", 403), ("facilities", 403), ("dean", 403), ("admin", 200)])
def test_only_admins_can_list_the_user_directory(client, campus, actor, expected):
    response = client.get("/api/v1/admin/users", headers=auth_headers(campus[actor]))

    assert response.status_code == expected


@pytest.mark.parametrize("actor,expected", [("aarav", 403), ("facilities", 200), ("dean", 200), ("admin", 200)])
def test_handler_directory_is_staff_only(client, campus, actor, expected):
    response = client.get("/api/v1/admin/handlers", headers=auth_headers(campus[actor]))

    assert response.status_code == expected


def test_a_handler_can_load_their_own_dashboard_without_admin_rights(client, campus, an_issue):
    """The handler dashboard used to call the admin directory, get a 403, and render
    an empty queue that looked exactly like 'nothing is broken'."""
    issues = client.get("/api/v1/issues?scope=assigned", headers=auth_headers(campus["facilities"]))
    targets = client.get(f"/api/v1/issues/{an_issue}/escalation-targets",
                         headers=auth_headers(campus["facilities"]))

    assert issues.status_code == 200
    assert issues.json()["total"] == 1
    assert targets.status_code == 200
    assert any(target["id"] == campus["dean"].id for target in targets.json())


def test_a_handler_cannot_act_on_an_issue_assigned_to_someone_else(client, campus, an_issue):
    response = client.post(f"/api/v1/issues/{an_issue}/progress",
                           headers=auth_headers(campus["it_handler"]))

    assert response.status_code == 403


def test_a_student_cannot_resolve_their_own_issue(client, campus, an_issue):
    response = client.post(
        f"/api/v1/issues/{an_issue}/resolve",
        json={"evidence_type": "description", "notes": "I decided this is fine now."},
        headers=auth_headers(campus["aarav"]),
    )

    assert response.status_code == 403


def test_a_student_cannot_escalate(client, campus, an_issue):
    response = client.post(
        f"/api/v1/issues/{an_issue}/escalate",
        json={"reason": "I would like the Dean to look at this immediately please"},
        headers=auth_headers(campus["aarav"]),
    )

    assert response.status_code == 403


def test_a_student_cannot_reassign(client, campus, an_issue):
    response = client.post(
        f"/api/v1/issues/{an_issue}/reassign",
        json={"handler_id": campus["it_handler"].id},
        headers=auth_headers(campus["aarav"]),
    )

    assert response.status_code == 403


def test_students_cannot_request_staff_scopes(client, campus):
    for scope in ("assigned", "escalated", "triage"):
        response = client.get(f"/api/v1/issues?scope={scope}", headers=auth_headers(campus["aarav"]))
        assert response.status_code == 403, scope


def test_only_admins_see_the_triage_queue(client, campus):
    assert client.get("/api/v1/issues?scope=triage", headers=auth_headers(campus["dean"])).status_code == 403
    assert client.get("/api/v1/issues?scope=triage", headers=auth_headers(campus["admin"])).status_code == 200


def test_notifications_are_scoped_to_their_owner(client, campus, an_issue):
    handler_notifications = client.get("/api/v1/notifications", headers=auth_headers(campus["facilities"]))
    student_notifications = client.get("/api/v1/notifications", headers=auth_headers(campus["priya"]))

    assert handler_notifications.json()["total"] == 1
    assert student_notifications.json()["total"] == 0


def test_a_user_cannot_mark_someone_elses_notification_read(client, campus, an_issue):
    handler_notification = client.get(
        "/api/v1/notifications", headers=auth_headers(campus["facilities"])
    ).json()["items"][0]

    response = client.post(f"/api/v1/notifications/{handler_notification['id']}/read",
                           headers=auth_headers(campus["priya"]))

    assert response.status_code == 404


def test_an_admin_cannot_deactivate_their_own_account(client, campus):
    response = client.put(
        f"/api/v1/admin/users/{campus['admin'].id}",
        json={"is_active": False},
        headers=auth_headers(campus["admin"]),
    )

    assert response.status_code == 422


def test_a_deactivated_account_cannot_use_an_existing_token(client, db, campus):
    headers = auth_headers(campus["aarav"])
    campus["aarav"].is_active = False
    db.commit()

    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
