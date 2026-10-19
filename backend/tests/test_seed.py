"""The seeded taxonomy is configuration, but it carries product rules worth
pinning: the category set, the scope boundary, and that nothing in it can fall
through to the catch-all by accident."""

import pytest

from app.models.issue_type import IssueType
from app.models.location import Location
from app.services.routing import resolve_handler
from scripts.seed import seed

EXPECTED_CATEGORIES = {
    "Physical Infrastructure",
    "Academic Resources",
    "Food & Health",
    "Hostel & Accommodation",
    "Safety & Social Environment",
    "Extracurricular & Engagement",
}

PERSONAL_TERMS = ("ragging", "harass", "bully", "bullying", "abuse")


@pytest.fixture
def seeded(db):
    credentials = seed(db)
    return credentials


def test_seeding_creates_the_six_categories_plus_the_catch_all(db, seeded):
    categories = {row.category for row in db.query(IssueType).all()}

    assert categories == EXPECTED_CATEGORIES | {"Miscellaneous"}


def test_no_seeded_issue_type_describes_a_personal_matter(db, seeded):
    """This platform shows handlers who reported. Ragging, harassment and bullying
    need anonymity and legal handling, so they are out of scope by design."""
    for issue_type in db.query(IssueType).all():
        text = f"{issue_type.sub_type} {issue_type.description}".lower()
        assert not any(term in text for term in PERSONAL_TERMS), issue_type.sub_type


def test_every_sub_type_has_a_dedicated_owner_at_every_location(db, seeded):
    """The catch-all is for genuinely miscellaneous issues. A listed sub-type that
    resolves to it, anywhere on campus, means a rule is missing."""
    locations = db.query(Location).all()
    sub_types = db.query(IssueType).filter(IssueType.category != "Miscellaneous").all()
    assert sub_types and locations

    orphans = []
    for issue_type in sub_types:
        for location in locations:
            result = resolve_handler(db, issue_type.id, location.id)
            if result.handler is None or result.match_kind in {"catch_all", "unrouted"}:
                orphans.append((issue_type.sub_type, location.code))

    assert orphans == []


def test_miscellaneous_goes_to_the_catch_all_handler(db, seeded):
    misc = db.query(IssueType).filter(IssueType.category == "Miscellaneous").one()
    location = db.query(Location).filter(Location.code == "CANTEEN").one()

    result = resolve_handler(db, misc.id, location.id)

    assert result.match_kind == "catch_all"
    assert result.handler.email == "estate.office@campus.edu"


def test_a_hostel_location_claims_physical_problems_for_the_warden(db, seeded):
    fan = db.query(IssueType).filter(IssueType.sub_type == "Ceiling fan").one()
    hostel_room = db.query(Location).filter(Location.code == "HST-1-RM-112").one()
    classroom = db.query(Location).filter(Location.code == "BLK-A-RM-204").one()

    assert resolve_handler(db, fan.id, hostel_room.id).handler.email == "hostel.kulkarni@campus.edu"
    assert resolve_handler(db, fan.id, classroom.id).handler.email == "facilities.sharma@campus.edu"


def test_seeding_twice_creates_nothing_new(db, seeded):
    second = seed(db)

    assert second == {}
    assert db.query(IssueType).count() == len(
        {(row.category, row.sub_type) for row in db.query(IssueType).all()}
    )
