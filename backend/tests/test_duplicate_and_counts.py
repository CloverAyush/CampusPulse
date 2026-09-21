from tests.conftest import auth_headers


def test_no_suggestion_when_nothing_matches(client, campus):
    response = client.post(
        "/api/v1/reports/check-duplicate",
        json={"issue_type_id": campus["fan_type"].id, "location_id": campus["room_204"].id,
              "specific_asset": "Ceiling fan 1"},
        headers=auth_headers(campus["aarav"]),
    )

    assert response.json()["has_match"] is False


def test_a_matching_issue_is_suggested_but_never_merged_automatically(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"], asset="Ceiling fan 1").json()["issue_id"]

    suggestion = client.post(
        "/api/v1/reports/check-duplicate",
        json={"issue_type_id": campus["fan_type"].id, "location_id": campus["room_204"].id,
              "specific_asset": "Ceiling fan 1"},
        headers=auth_headers(campus["priya"]),
    ).json()

    assert suggestion["has_match"] is True
    candidate = suggestion["candidates"][0]
    assert candidate["issue_id"] == issue_id
    assert candidate["asset_match"] is True
    assert candidate["already_reported_by_you"] is False

    # Declining the suggestion creates a genuinely separate issue.
    separate = submit_report(campus["priya"], asset="Ceiling fan 1")
    assert separate.status_code == 201
    assert separate.json()["issue_id"] != issue_id


def test_a_different_asset_is_still_offered_but_marked_as_not_matching(client, campus, submit_report):
    submit_report(campus["aarav"], asset="Ceiling fan 1")

    suggestion = client.post(
        "/api/v1/reports/check-duplicate",
        json={"issue_type_id": campus["fan_type"].id, "location_id": campus["room_204"].id,
              "specific_asset": "Ceiling fan 4"},
        headers=auth_headers(campus["priya"]),
    ).json()

    assert suggestion["candidates"][0]["asset_match"] is False


def test_the_student_is_told_when_they_already_reported_a_candidate(client, campus, submit_report):
    submit_report(campus["aarav"], asset="Ceiling fan 1")

    suggestion = client.post(
        "/api/v1/reports/check-duplicate",
        json={"issue_type_id": campus["fan_type"].id, "location_id": campus["room_204"].id,
              "specific_asset": "Ceiling fan 1"},
        headers=auth_headers(campus["aarav"]),
    ).json()

    assert suggestion["candidates"][0]["already_reported_by_you"] is True


def test_affected_count_reflects_people_not_submissions(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"]).json()["issue_id"]
    submit_report(campus["priya"], existing_issue_id=issue_id)

    repeat = submit_report(campus["aarav"], existing_issue_id=issue_id)
    assert repeat.status_code == 409

    detail = client.get(f"/api/v1/issues/{issue_id}", headers=auth_headers(campus["facilities"])).json()
    assert detail["affected_student_count"] == 2
    assert detail["report_count"] == 2


def test_a_report_cannot_be_attached_to_an_unrelated_issue(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"]).json()["issue_id"]

    response = submit_report(
        campus["priya"],
        issue_type=campus["bin_type"],
        location=campus["canteen"],
        description="Completely different problem in a completely different building.",
        existing_issue_id=issue_id,
    )

    assert response.status_code == 422
    assert "does not match" in response.json()["error"]["message"]


def test_a_report_cannot_be_attached_to_a_closed_issue(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"], issue_type=campus["bin_type"], location=campus["canteen"],
                             description="The bin by the canteen entrance is overflowing.").json()["issue_id"]
    client.post(f"/api/v1/issues/{issue_id}/resolve",
                json={"evidence_type": "description", "notes": "Emptied the bin and swept up."},
                headers=auth_headers(campus["estate"]))

    response = submit_report(campus["priya"], issue_type=campus["bin_type"], location=campus["canteen"],
                             description="The bin by the canteen entrance is overflowing.",
                             existing_issue_id=issue_id)

    assert response.status_code == 409


def test_closed_issues_are_not_offered_as_duplicates(client, campus, submit_report):
    issue_id = submit_report(campus["aarav"], issue_type=campus["bin_type"], location=campus["canteen"],
                             description="The bin by the canteen entrance is overflowing.").json()["issue_id"]
    client.post(f"/api/v1/issues/{issue_id}/resolve",
                json={"evidence_type": "description", "notes": "Emptied the bin and swept up."},
                headers=auth_headers(campus["estate"]))

    suggestion = client.post(
        "/api/v1/reports/check-duplicate",
        json={"issue_type_id": campus["bin_type"].id, "location_id": campus["canteen"].id},
        headers=auth_headers(campus["priya"]),
    ).json()

    assert suggestion["has_match"] is False


def test_students_can_switch_between_their_own_issues_and_the_whole_board(client, campus, submit_report):
    submit_report(campus["aarav"])
    submit_report(campus["priya"], issue_type=campus["wifi_type"], location=campus["canteen"],
                  description="No Wi-Fi signal anywhere in the canteen seating area.")

    mine = client.get("/api/v1/issues?scope=mine", headers=auth_headers(campus["aarav"])).json()
    everything = client.get("/api/v1/issues?scope=all", headers=auth_headers(campus["aarav"])).json()

    assert mine["total"] == 1
    assert everything["total"] == 2


def test_listing_is_paginated(client, campus, submit_report):
    for index in range(5):
        submit_report(campus["aarav"], asset=f"Ceiling fan {index}")

    page = client.get("/api/v1/issues?scope=mine&limit=2&offset=2", headers=auth_headers(campus["aarav"])).json()

    assert page["total"] == 5
    assert len(page["items"]) == 2
    assert page["offset"] == 2
