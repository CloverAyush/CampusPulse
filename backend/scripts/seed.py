"""Populate a development database with campus taxonomy, locations, routing rules
and staff accounts.

Run from the backend directory, after `alembic upgrade head`:

    python -m scripts.seed

There is no HTTP endpoint for this on purpose: seeding rewrites institutional
configuration and belongs in an operator's hands, not behind a request. Every
account gets its own randomly generated password, printed once. Nothing is
hardcoded and nothing is shared.
"""

import argparse
import secrets
import string
import sys
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.enums import UserRole
from app.models.issue_type import IssueType
from app.models.location import Location
from app.models.routing_rule import RoutingRule
from app.models.user import User
from app.services.auth import get_password_hash

STAFF = [
    ("facilities.sharma@campus.edu", "Rajesh Sharma", UserRole.HANDLER, "Facilities & Electrical"),
    ("it.deshmukh@campus.edu", "Amit Deshmukh", UserRole.HANDLER, "Campus IT Centre"),
    ("plumbing.kumar@campus.edu", "Suresh Kumar", UserRole.HANDLER, "Civil & Maintenance"),
    ("sanitation.rani@campus.edu", "Anita Rani", UserRole.HANDLER, "Housekeeping"),
    ("estate.office@campus.edu", "Campus Estate Office", UserRole.HANDLER, "Estate Office"),
    ("dean.verma@campus.edu", "Dr K. Verma", UserRole.HIGHER_AUTHORITY, "Dean of Infrastructure"),
]

ISSUE_TYPES = [
    ("Electrical", "Ceiling fan", "Stopped spinning, noisy, or broken regulator", True),
    ("Electrical", "Tube light or bulb", "Flickering or fused lighting", True),
    ("Electrical", "Switchboard or socket", "Loose socket, sparking, or dead outlet", True),
    ("Plumbing", "Tap or washbasin", "Continuous drip or blocked drain", True),
    ("Plumbing", "Washroom flush or drainage", "Blocked line or broken flush", True),
    ("Wi-Fi & network", "Access point or weak signal", "Cannot connect, or unusably slow", True),
    ("Wi-Fi & network", "Lab ethernet port", "No link light on the port", True),
    ("Cleanliness", "Dustbin overflowing", "Waste not cleared in a shared space", False),
    ("Cleanliness", "Washroom sanitation", "Floor unmopped or dispenser empty", False),
    ("Water supply", "Water cooler warm or empty", "Cooling stopped or no water", True),
    ("Water supply", "RO purifier alert", "Filter alarm or slow dispensing", True),
    ("Library facilities", "Reading hall air conditioning", "Not cooling or excessively noisy", True),
    ("Library facilities", "Furniture or shelving damaged", "Broken chair, table or book stack", False),
    ("Transport & parking", "Bicycle stand shed", "Leaking shed or damaged rack", False),
    ("Canteen & common areas", "Seating or common furniture", "Damaged or missing furniture", False),
    ("Miscellaneous", "Something else", "Anything not covered by the other categories", True),
]

LOCATIONS = [
    ("Block A (main academic wing)", "BLK-A", "Block A", None, None, None),
    ("Block A - ground floor", "BLK-A-FL-0", "Block A", "Ground floor", None, "BLK-A"),
    ("Room 101 (lecture hall)", "BLK-A-RM-101", "Block A", "Ground floor", "Room 101", "BLK-A-FL-0"),
    ("Computer lab 1", "BLK-A-LAB-1", "Block A", "Ground floor", "Lab 1", "BLK-A-FL-0"),
    ("Block A - second floor", "BLK-A-FL-2", "Block A", "Second floor", None, "BLK-A"),
    ("Room 204 (classroom)", "BLK-A-RM-204", "Block A", "Second floor", "Room 204", "BLK-A-FL-2"),
    ("Room 205 (tutorial room)", "BLK-A-RM-205", "Block A", "Second floor", "Room 205", "BLK-A-FL-2"),
    ("Block B (science wing)", "BLK-B", "Block B", None, None, None),
    ("Block B - first floor", "BLK-B-FL-1", "Block B", "First floor", None, "BLK-B"),
    ("Physics lab", "BLK-B-PHY-LAB", "Block B", "First floor", "Physics lab", "BLK-B-FL-1"),
    ("Chemistry lab", "BLK-B-CHEM-LAB", "Block B", "First floor", "Chemistry lab", "BLK-B-FL-1"),
    ("Central library", "LIB", "Library", None, None, None),
    ("Reading hall (first floor)", "LIB-READ-HALL", "Library", "First floor", "Reading hall", "LIB"),
    ("Circulation desk", "LIB-CIRC", "Library", "Ground floor", "Circulation desk", "LIB"),
    ("Hostel block 1", "HST-1", "Hostel 1", None, None, None),
    ("Hostel 1 - room 112", "HST-1-RM-112", "Hostel 1", "First floor", "Room 112", "HST-1"),
    ("Student canteen", "CANTEEN", "Amenities", "Ground floor", "Main dining area", None),
]

ROUTING_RULES = [
    ("Electrical|Ceiling fan", "BLK-A", "facilities.sharma@campus.edu", 25),
    ("Electrical|Tube light or bulb", "BLK-A", "facilities.sharma@campus.edu", 25),
    ("Electrical|Switchboard or socket", "BLK-A", "facilities.sharma@campus.edu", 25),
    ("Electrical|Ceiling fan", None, "facilities.sharma@campus.edu", 10),
    ("Electrical|Tube light or bulb", None, "facilities.sharma@campus.edu", 10),
    ("Electrical|Switchboard or socket", None, "facilities.sharma@campus.edu", 10),
    ("Wi-Fi & network|Access point or weak signal", None, "it.deshmukh@campus.edu", 20),
    ("Wi-Fi & network|Lab ethernet port", None, "it.deshmukh@campus.edu", 20),
    ("Plumbing|Tap or washbasin", None, "plumbing.kumar@campus.edu", 20),
    ("Plumbing|Washroom flush or drainage", None, "plumbing.kumar@campus.edu", 20),
    ("Water supply|Water cooler warm or empty", None, "plumbing.kumar@campus.edu", 20),
    ("Water supply|RO purifier alert", None, "plumbing.kumar@campus.edu", 20),
    ("Cleanliness|Dustbin overflowing", None, "sanitation.rani@campus.edu", 20),
    ("Cleanliness|Washroom sanitation", None, "sanitation.rani@campus.edu", 20),
    ("Library facilities|Reading hall air conditioning", "LIB", "facilities.sharma@campus.edu", 25),
    ("Library facilities|Furniture or shelving damaged", "LIB", "estate.office@campus.edu", 25),
    ("Transport & parking|Bicycle stand shed", None, "estate.office@campus.edu", 20),
    ("Canteen & common areas|Seating or common furniture", None, "estate.office@campus.edu", 20),
    # Catch-all for miscellaneous issues. Anything no other rule matches lands here,
    # so no report is ever created without a handler.
    (None, None, "estate.office@campus.edu", 1),
]

ALPHABET = string.ascii_letters + string.digits


def generate_password() -> str:
    """Random per account. A shared seed password is how a demo database becomes a
    production breach."""
    while True:
        candidate = "".join(secrets.choice(ALPHABET) for _ in range(16))
        if any(c.isalpha() for c in candidate) and any(c.isdigit() for c in candidate):
            return candidate


def seed(db: Session) -> Dict[str, str]:
    created_credentials: Dict[str, str] = {}

    users: Dict[str, User] = {}
    for email, full_name, role, department in STAFF:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            users[email] = existing
            continue

        password = generate_password()
        user = User(
            email=email,
            full_name=full_name,
            role=role,
            department=department,
            hashed_password=get_password_hash(password),
            is_active=True,
        )
        db.add(user)
        db.flush()
        users[email] = user
        created_credentials[email] = password

    issue_types: Dict[str, IssueType] = {}
    for category, sub_type, description, requires_verification in ISSUE_TYPES:
        key = f"{category}|{sub_type}"
        existing = db.query(IssueType).filter(
            IssueType.category == category, IssueType.sub_type == sub_type
        ).first()
        if existing:
            issue_types[key] = existing
            continue

        issue_type = IssueType(
            category=category,
            sub_type=sub_type,
            description=description,
            requires_verification=requires_verification,
            is_active=True,
        )
        db.add(issue_type)
        db.flush()
        issue_types[key] = issue_type

    locations: Dict[str, Location] = {}
    for name, code, building, floor, room, parent_code in LOCATIONS:
        existing = db.query(Location).filter(Location.code == code).first()
        if existing:
            locations[code] = existing
            continue

        location = Location(
            name=name,
            code=code,
            building=building,
            floor=floor,
            room=room,
            parent_id=locations[parent_code].id if parent_code else None,
            is_active=True,
        )
        db.add(location)
        db.flush()
        locations[code] = location

    for type_key, location_code, handler_email, priority in ROUTING_RULES:
        issue_type_id = issue_types[type_key].id if type_key else None
        location_id = locations[location_code].id if location_code else None
        handler = users[handler_email]

        existing = db.query(RoutingRule).filter(
            RoutingRule.issue_type_id.is_(None) if issue_type_id is None else RoutingRule.issue_type_id == issue_type_id,
            RoutingRule.location_id.is_(None) if location_id is None else RoutingRule.location_id == location_id,
            RoutingRule.handler_id == handler.id,
        ).first()
        if existing:
            continue

        db.add(
            RoutingRule(
                issue_type_id=issue_type_id,
                location_id=location_id,
                handler_id=handler.id,
                priority=priority,
                is_active=True,
            )
        )

    db.commit()
    return created_credentials


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Seed CampusPulse reference data.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Required to run when ENVIRONMENT=production.",
    )
    args = parser.parse_args(argv)

    if settings.ENVIRONMENT == "production" and not args.force:
        print("Refusing to seed a production database without --force.", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        credentials = seed(db)
    finally:
        db.close()

    if credentials:
        print("\nCreated staff accounts. These passwords are shown once:\n")
        width = max(len(email) for email in credentials)
        for email, password in credentials.items():
            print(f"  {email.ljust(width)}  {password}")
        print("\nStore them somewhere safe, then change them at first sign-in.\n")
    else:
        print("Reference data already present. No new accounts created.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
