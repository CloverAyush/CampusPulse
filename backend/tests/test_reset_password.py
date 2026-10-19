import pytest

from app.services.auth import verify_password
from scripts.reset_password import reset_password


def test_reset_changes_the_password_and_only_that_account(db, campus):
    other_hash = campus["priya"].hashed_password

    assert reset_password(db, "facilities@campus.edu", "NewPassw0rdLong") is True

    db.refresh(campus["facilities"])
    assert verify_password("NewPassw0rdLong", campus["facilities"].hashed_password)
    assert not verify_password("TestPassw0rd!2026", campus["facilities"].hashed_password)
    assert campus["priya"].hashed_password == other_hash


def test_reset_works_for_a_differently_cased_email(db, campus):
    assert reset_password(db, "Facilities@Campus.edu", "NewPassw0rdLong") is True


def test_unknown_email_is_reported_not_raised(db, campus):
    assert reset_password(db, "nobody@campus.edu", "NewPassw0rdLong") is False


@pytest.mark.parametrize("weak", ["short1", "alllettersnodigits", "1234567890123"])
def test_weak_passwords_are_rejected_like_at_registration(db, campus, weak):
    with pytest.raises(ValueError):
        reset_password(db, "facilities@campus.edu", weak)
