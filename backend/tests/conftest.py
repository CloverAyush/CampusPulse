import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

# Settings are read at import time, so the test environment has to be in place before
# anything under app.* is imported.
_TEST_DB_FILE = Path(tempfile.gettempdir()) / "campuspulse_test.db"
os.environ.update(
    {
        "ENVIRONMENT": "development",
        "DATABASE_URL": f"sqlite:///{_TEST_DB_FILE}",
        "SECRET_KEY": "test-only-secret-key-that-is-long-enough-to-pass-validation",
        "LOG_JSON": "false",
        "LOG_LEVEL": "WARNING",
        "LOGIN_RATE_LIMIT_PER_MINUTE": "1000",
        "REGISTER_RATE_LIMIT_PER_HOUR": "1000",
        "WRITE_RATE_LIMIT_PER_MINUTE": "1000",
        "BCRYPT_ROUNDS": "4",
    }
)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.database import engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.issue_type import IssueType  # noqa: E402
from app.models.location import Location  # noqa: E402
from app.models.routing_rule import RoutingRule  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.auth import create_access_token, get_password_hash  # noqa: E402

TEST_PASSWORD = "TestPassw0rd!2026"


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    """Builds the schema by running the real migrations, so a migration that drifts
    from the models breaks the test suite instead of breaking a deployment."""
    if _TEST_DB_FILE.exists():
        _TEST_DB_FILE.unlink()

    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    command.upgrade(config, "head")

    yield

    engine.dispose()
    if _TEST_DB_FILE.exists():
        _TEST_DB_FILE.unlink()


@pytest.fixture
def db(migrated_database):
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection, expire_on_commit=False)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth_headers(user: User) -> dict:
    token, _ = create_access_token(subject=user.id, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


def make_user(db, email: str, role: UserRole, full_name: str = None) -> User:
    user = User(
        email=email,
        full_name=full_name or email.split("@")[0].replace(".", " ").title(),
        role=role,
        hashed_password=get_password_hash(TEST_PASSWORD),
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def campus(db):
    """A small but realistic campus: two students, two handlers, an authority, an
    admin, a location hierarchy, and routing rules including a catch-all."""
    aarav = make_user(db, "aarav@student.edu", UserRole.STUDENT, "Aarav Sharma")
    priya = make_user(db, "priya@student.edu", UserRole.STUDENT, "Priya Patel")
    rohit = make_user(db, "rohit@student.edu", UserRole.STUDENT, "Rohit Verma")
    facilities = make_user(db, "facilities@campus.edu", UserRole.HANDLER, "Rajesh Sharma")
    it_handler = make_user(db, "it@campus.edu", UserRole.HANDLER, "Amit Deshmukh")
    estate = make_user(db, "estate@campus.edu", UserRole.HANDLER, "Estate Office")
    dean = make_user(db, "dean@campus.edu", UserRole.HIGHER_AUTHORITY, "Dr K. Verma")
    admin = make_user(db, "admin@campus.edu", UserRole.ADMIN, "Administrator")

    fan_type = IssueType(category="Electrical", sub_type="Ceiling fan", requires_verification=True)
    wifi_type = IssueType(category="Wi-Fi & network", sub_type="Access point", requires_verification=True)
    bin_type = IssueType(category="Cleanliness", sub_type="Dustbin overflowing", requires_verification=False)
    misc_type = IssueType(category="Miscellaneous", sub_type="Something else", requires_verification=True)
    db.add_all([fan_type, wifi_type, bin_type, misc_type])
    db.flush()

    block_a = Location(name="Block A", code="BLK-A", building="Block A")
    db.add(block_a)
    db.flush()
    floor_2 = Location(name="Block A second floor", code="BLK-A-FL-2", building="Block A",
                       floor="Second floor", parent_id=block_a.id)
    db.add(floor_2)
    db.flush()
    room_204 = Location(name="Room 204", code="BLK-A-RM-204", building="Block A",
                        floor="Second floor", room="Room 204", parent_id=floor_2.id)
    canteen = Location(name="Student canteen", code="CANTEEN", building="Amenities")
    db.add_all([room_204, canteen])
    db.flush()

    db.add_all([
        RoutingRule(issue_type_id=fan_type.id, location_id=block_a.id, handler_id=facilities.id, priority=25),
        RoutingRule(issue_type_id=wifi_type.id, location_id=None, handler_id=it_handler.id, priority=20),
        RoutingRule(issue_type_id=None, location_id=None, handler_id=estate.id, priority=1),
    ])
    db.commit()

    return {
        "aarav": aarav, "priya": priya, "rohit": rohit,
        "facilities": facilities, "it_handler": it_handler, "estate": estate,
        "dean": dean, "admin": admin,
        "fan_type": fan_type, "wifi_type": wifi_type, "bin_type": bin_type, "misc_type": misc_type,
        "block_a": block_a, "floor_2": floor_2, "room_204": room_204, "canteen": canteen,
    }


@pytest.fixture
def submit_report(client, campus):
    def _submit(user, issue_type=None, location=None, description=None, asset=None, existing_issue_id=None):
        payload = {
            "issue_type_id": (issue_type or campus["fan_type"]).id,
            "location_id": (location or campus["room_204"]).id,
            "description": description or "The ceiling fan has stopped working entirely.",
        }
        if asset is not None:
            payload["specific_asset"] = asset
        if existing_issue_id is not None:
            payload["existing_issue_id"] = existing_issue_id
        return client.post("/api/v1/reports", json=payload, headers=auth_headers(user))

    return _submit
