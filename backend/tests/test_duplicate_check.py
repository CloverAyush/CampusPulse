from tests.conftest import get_auth_headers
from app.models.enums import IssueStatus

def test_duplicate_check_and_linking(client, seed_data):
    """
    Test deterministic duplicate suggestion and subsequent linking flow:
    1. Student Aarav checks duplicates in Room 204 for Fan -> None.
    2. Aarav submits report -> Issue created.
    3. Student Priya checks duplicates in Room 204 for Fan -> Match found.
    4. Priya confirms and links her report to the existing Issue.
    5. Issue now has 2 linked reports and 2 affected students.
    """
    aarav_headers = get_auth_headers(seed_data["student_aarav"])
    priya_headers = get_auth_headers(seed_data["student_priya"])

    # 1. Check duplicate before any issue exists
    resp = client.post(
        "/api/v1/reports/check-duplicate",
        json={
            "issue_type_id": seed_data["fan_type"].id,
            "location_id": seed_data["room_204"].id,
            "specific_asset": "Ceiling Fan 1"
        },
        headers=aarav_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_match"] is False
    assert len(data["candidates"]) == 0

    # 2. Aarav submits initial report
    resp_submit1 = client.post(
        "/api/v1/reports",
        json={
            "issue_type_id": seed_data["fan_type"].id,
            "location_id": seed_data["room_204"].id,
            "specific_asset": "Ceiling Fan 1",
            "description": "Fan 1 is making a very loud screeching sound and not rotating."
        },
        headers=aarav_headers
    )
    assert resp_submit1.status_code == 201
    report1 = resp_submit1.json()
    issue_id = report1["issue_id"]
    assert issue_id is not None

    # 3. Priya checks duplicates for the same location and issue type
    resp_check2 = client.post(
        "/api/v1/reports/check-duplicate",
        json={
            "issue_type_id": seed_data["fan_type"].id,
            "location_id": seed_data["room_204"].id,
            "specific_asset": "Ceiling Fan 1"
        },
        headers=priya_headers
    )
    assert resp_check2.status_code == 200
    data2 = resp_check2.json()
    assert data2["has_match"] is True
    assert len(data2["candidates"]) == 1
    candidate = data2["candidates"][0]
    assert candidate["issue_id"] == issue_id
    assert candidate["report_count"] == 1
    assert candidate["status"] == IssueStatus.OPEN.value

    # 4. Priya confirms this is the same problem and links her report
    resp_submit2 = client.post(
        "/api/v1/reports",
        json={
            "issue_type_id": seed_data["fan_type"].id,
            "location_id": seed_data["room_204"].id,
            "specific_asset": "Ceiling Fan 1",
            "description": "Also noticed Fan 1 completely stopped spinning during 2pm lecture.",
            "existing_issue_id": issue_id
        },
        headers=priya_headers
    )
    assert resp_submit2.status_code == 201
    report2 = resp_submit2.json()
    assert report2["issue_id"] == issue_id

    # 5. Verify the underlying Issue now reflects 2 reports
    resp_issue = client.get(f"/api/v1/issues/{issue_id}", headers=aarav_headers)
    assert resp_issue.status_code == 200
    issue_detail = resp_issue.json()
    assert issue_detail["report_count"] == 2
    assert len(issue_detail["reports"]) == 2
    reporters = [r["reporter_id"] for r in issue_detail["reports"]]
    assert seed_data["student_aarav"].id in reporters
    assert seed_data["student_priya"].id in reporters

