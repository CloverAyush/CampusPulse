import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_db
from app.main import app
from app.models.enums import UserRole
from app.models.user import User
from app.models.issue_type import IssueType
from app.models.location import Location
from app.models.routing_rule import RoutingRule
from app.services.auth import get_password_hash, create_access_token

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def seed_data(db):
    """
    Creates standard base users, issue types, locations, and routing rules for test cases.
    """
    pw_hash = get_password_hash("testpass123")

    # Users
    student_aarav = User(
        email="aarav@student.edu",
        full_name="Aarav Sharma",
        role=UserRole.STUDENT,
        hashed_password=pw_hash,
        is_active=True
    )
    student_priya = User(
        email="priya@student.edu",
        full_name="Priya Patel",
        role=UserRole.STUDENT,
        hashed_password=pw_hash,
        is_active=True
    )
    facilities_handler = User(
        email="facilities@campus.edu",
        full_name="Rajesh Sharma (Facilities)",
        role=UserRole.HANDLER,
        hashed_password=pw_hash,
        is_active=True
    )
    it_handler = User(
        email="it@campus.edu",
        full_name="Amit Deshmukh (IT)",
        role=UserRole.HANDLER,
        hashed_password=pw_hash,
        is_active=True
    )
    dean_authority = User(
        email="dean@campus.edu",
        full_name="Dr. K. Verma (Dean)",
        role=UserRole.HIGHER_AUTHORITY,
        hashed_password=pw_hash,
        is_active=True
    )
    admin_user = User(
        email="admin@campus.edu",
        full_name="Admin",
        role=UserRole.ADMIN,
        hashed_password=pw_hash,
        is_active=True
    )

    db.add_all([student_aarav, student_priya, facilities_handler, it_handler, dean_authority, admin_user])
    db.flush()

    # Issue Types
    fan_type = IssueType(
        category="Electrical",
        sub_type="Ceiling Fan",
        description="Ceiling fan issue",
        requires_verification=True,
        is_active=True
    )
    wifi_type = IssueType(
        category="Wi-Fi & Network",
        sub_type="Access Point Offline",
        description="Wi-Fi issue",
        requires_verification=True,
        is_active=True
    )
    cleanliness_type = IssueType(
        category="Cleanliness",
        sub_type="Dustbin Full",
        description="Cleanliness issue",
        requires_verification=False, # Does not require student verification
        is_active=True
    )
    db.add_all([fan_type, wifi_type, cleanliness_type])
    db.flush()

    # Locations
    block_a = Location(
        name="Block A",
        code="BLK-A",
        building="Block A",
        is_active=True
    )
    db.add(block_a)
    db.flush()

    floor_2 = Location(
        name="Block A - 2nd Floor",
        code="BLK-A-FL-2",
        building="Block A",
        floor="2nd Floor",
        parent_id=block_a.id,
        is_active=True
    )
    db.add(floor_2)
    db.flush()

    room_204 = Location(
        name="Room 204",
        code="BLK-A-RM-204",
        building="Block A",
        floor="2nd Floor",
        room="Room 204",
        parent_id=floor_2.id,
        is_active=True
    )
    db.add(room_204)
    db.flush()

    # Routing Rules
    # Rule 1: Electrical Fan in Block A -> Facilities Handler (Priority 20)
    rule_fan_block_a = RoutingRule(
        issue_type_id=fan_type.id,
        location_id=block_a.id,
        handler_id=facilities_handler.id,
        priority=20,
        is_active=True
    )
    # Rule 2: Wi-Fi everywhere -> IT Handler (Priority 10)
    rule_wifi_global = RoutingRule(
        issue_type_id=wifi_type.id,
        location_id=None,
        handler_id=it_handler.id,
        priority=10,
        is_active=True
    )
    # Rule 3: Global Fallback -> Facilities Handler (Priority 1)
    rule_global_fallback = RoutingRule(
        issue_type_id=None,
        location_id=None,
        handler_id=facilities_handler.id,
        priority=1,
        is_active=True
    )
    db.add_all([rule_fan_block_a, rule_wifi_global, rule_global_fallback])
    db.commit()

    return {
        "student_aarav": student_aarav,
        "student_priya": student_priya,
        "facilities_handler": facilities_handler,
        "it_handler": it_handler,
        "dean_authority": dean_authority,
        "admin_user": admin_user,
        "fan_type": fan_type,
        "wifi_type": wifi_type,
        "cleanliness_type": cleanliness_type,
        "block_a": block_a,
        "floor_2": floor_2,
        "room_204": room_204,
    }

def get_auth_headers(user: User) -> dict:
    token = create_access_token(subject=user.id, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}

