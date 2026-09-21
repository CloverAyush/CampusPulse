from datetime import datetime, timezone

from tests.conftest import auth_headers


def test_timestamps_are_returned_with_an_explicit_utc_offset(client, campus, submit_report):
    """Naive timestamps were being parsed by the browser as local time, so everything
    displayed five and a half hours out in IST."""
    submit_report(campus["aarav"])

    created_at = client.get("/api/v1/reports/my", headers=auth_headers(campus["aarav"])).json()["items"][0]["created_at"]
    parsed = datetime.fromisoformat(created_at)

    assert parsed.tzinfo is not None
    assert abs((datetime.now(timezone.utc) - parsed).total_seconds()) < 60
