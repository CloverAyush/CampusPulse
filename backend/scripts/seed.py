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

# The six top-level categories the platform is organised around. Each handler
# below owns a slice of them; routing rules further down map every sub-type to
# exactly one of these people.
STAFF = [
    ("facilities.sharma@campus.edu", "Rajesh Sharma", UserRole.HANDLER, "Facilities & Electrical"),
    ("it.deshmukh@campus.edu", "Amit Deshmukh", UserRole.HANDLER, "Campus IT Centre"),
    ("plumbing.kumar@campus.edu", "Suresh Kumar", UserRole.HANDLER, "Civil & Maintenance"),
    ("sanitation.rani@campus.edu", "Anita Rani", UserRole.HANDLER, "Housekeeping & Pest Control"),
    ("estate.office@campus.edu", "Campus Estate Office", UserRole.HANDLER, "Estate Office"),
    ("library.nair@campus.edu", "Meera Nair", UserRole.HANDLER, "Central Library"),
    ("lab.joshi@campus.edu", "Prakash Joshi", UserRole.HANDLER, "Laboratory Services"),
    ("canteen.patil@campus.edu", "Sunita Patil", UserRole.HANDLER, "Canteen & Health Services"),
    ("hostel.kulkarni@campus.edu", "Vikram Kulkarni", UserRole.HANDLER, "Hostel Administration"),
    ("sports.office@campus.edu", "Sports & Activities Office", UserRole.HANDLER, "Student Activities"),
    ("safety.officer@campus.edu", "Campus Safety Officer", UserRole.HANDLER, "Campus Safety"),
    ("dean.verma@campus.edu", "Dr K. Verma", UserRole.HIGHER_AUTHORITY, "Dean of Infrastructure"),
]

# (category, sub_type, description, requires_verification)
#
# requires_verification is True where "fixed" is something a student can check
# for themselves, and False where it is a judgement call (a menu, a crowded
# room) that would otherwise sit unclosed forever waiting for confirmation.
#
# "Safety & Social Environment" is deliberately limited to the NON-PERSONAL half
# of that theme: unsafe places and broken safety equipment. Ragging, harassment
# and bullying are personal, need anonymity and legal handling, and this
# platform shows handlers who reported -- so they do not belong here. Route
# those to the institution's anti-ragging committee and ICC instead.
ISSUE_TYPES = [
    # 1. Physical Infrastructure -- high frequency, low severity
    ("Physical Infrastructure", "Broken bench or furniture", "Damaged bench, desk, chair or cupboard", False),
    ("Physical Infrastructure", "Ceiling fan", "Stopped spinning, noisy, or broken regulator", True),
    ("Physical Infrastructure", "Tube light or bulb", "Flickering or fused lighting", True),
    ("Physical Infrastructure", "Switchboard or socket", "Loose socket, sparking, or dead outlet", True),
    ("Physical Infrastructure", "Air conditioning or ventilation", "Not cooling, noisy, or no airflow", True),
    ("Physical Infrastructure", "Wi-Fi access point or weak signal", "Cannot connect, or unusably slow", True),
    ("Physical Infrastructure", "Lab ethernet port", "No link light on the port", True),
    ("Physical Infrastructure", "Unsafe walkway", "Broken paving, missing railing, standing water", True),
    # 2. Academic Resources -- direct effect on learning
    ("Academic Resources", "Book missing or outdated", "A required title is unavailable or an old edition", False),
    ("Academic Resources", "Journal or database access", "Subscription not working or not available", True),
    ("Academic Resources", "Broken lab equipment", "Instrument, bench apparatus or computer not working", True),
    # 3. Food & Health -- health-critical
    ("Food & Health", "Canteen hygiene", "Dirty counters, utensils or serving area", True),
    ("Food & Health", "Menu or food quality", "Limited menu, stale or undercooked food", False),
    ("Food & Health", "Unsafe drinking water", "Cooler warm or empty, RO alarm, bad taste or smell", True),
    ("Food & Health", "Medical room supplies or availability", "Room locked, no first-aid stock, no staff present", True),
    # 4. Hostel & Accommodation -- quality of life
    ("Hostel & Accommodation", "Water outage", "No water, or no hot water, in a hostel block", True),
    ("Hostel & Accommodation", "Electricity outage", "Power cut or repeated tripping in a hostel block", True),
    ("Hostel & Accommodation", "Pest control", "Rodents, cockroaches, mosquitoes or bedbugs", True),
    ("Hostel & Accommodation", "Overcrowded room or common area", "More occupants than the space supports", False),
    ("Hostel & Accommodation", "Hostel security hazard", "Faulty lock or gate, missing fire equipment", True),
    # 5. Safety & Social Environment -- non-personal only (see note above)
    ("Safety & Social Environment", "Poorly lit or unsafe campus zone", "Dark corridor or car park, blind spot, hazard", True),
    ("Safety & Social Environment", "Broken safety equipment", "Fire extinguisher, CCTV, emergency light or alarm", True),
    # 6. Extracurricular & Engagement
    ("Extracurricular & Engagement", "Sports facility damaged", "Court, net, pitch or changing room in poor repair", True),
    ("Extracurricular & Engagement", "Recreational equipment broken", "Gym, indoor games or music room equipment", True),
    ("Extracurricular & Engagement", "Event venue or equipment support", "Hall, sound system or projector unavailable for an event", False),
    # Catch-all for anything that fits none of the above
    ("Miscellaneous", "Something else", "Anything not covered by the other categories", True),
]

# (name, code, building, floor, room, parent_code)
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
    ("Hostel 1 - mess hall", "HST-1-MESS", "Hostel 1", "Ground floor", "Mess hall", "HST-1"),
    ("Student canteen", "CANTEEN", "Amenities", "Ground floor", "Main dining area", None),
    ("Medical room", "MED-ROOM", "Amenities", "Ground floor", "Medical room", None),
    ("Campus grounds", "GROUNDS", "Campus grounds", None, None, None),
    ("Main walkway", "GROUNDS-WALKWAY", "Campus grounds", None, None, "GROUNDS"),
    ("Main car park", "GROUNDS-CARPARK", "Campus grounds", None, None, "GROUNDS"),
    ("Sports ground", "GROUNDS-SPORTS", "Campus grounds", None, None, "GROUNDS"),
    ("Indoor sports hall", "SPORTS-HALL", "Sports complex", "Ground floor", "Indoor hall", None),
    ("Auditorium", "AUDITORIUM", "Amenities", "Ground floor", "Auditorium", None),
]

# (issue-type key, location code or None, handler email, priority)
#
# One rule per sub-type, matching "this kind of problem, anywhere", so nothing in
# the taxonomy can fall through to the catch-all by accident. The few
# location-scoped rules show the hierarchy at work: a library or hostel location
# claims the problem before the general owner of that sub-type does.
ROUTING_RULES = [
    ("Physical Infrastructure|Broken bench or furniture", None, "estate.office@campus.edu", 20),
    ("Physical Infrastructure|Ceiling fan", None, "facilities.sharma@campus.edu", 20),
    ("Physical Infrastructure|Tube light or bulb", None, "facilities.sharma@campus.edu", 20),
    ("Physical Infrastructure|Switchboard or socket", None, "facilities.sharma@campus.edu", 20),
    ("Physical Infrastructure|Air conditioning or ventilation", None, "facilities.sharma@campus.edu", 20),
    ("Physical Infrastructure|Wi-Fi access point or weak signal", None, "it.deshmukh@campus.edu", 20),
    ("Physical Infrastructure|Lab ethernet port", None, "it.deshmukh@campus.edu", 20),
    ("Physical Infrastructure|Unsafe walkway", None, "estate.office@campus.edu", 20),
    # Library furniture is the library's to repair, not the estate office's.
    ("Physical Infrastructure|Broken bench or furniture", "LIB", "library.nair@campus.edu", 25),
    # Hostel blocks answer to the warden for everything physical inside them.
    ("Physical Infrastructure|Broken bench or furniture", "HST-1", "hostel.kulkarni@campus.edu", 25),
    ("Physical Infrastructure|Ceiling fan", "HST-1", "hostel.kulkarni@campus.edu", 25),
    ("Physical Infrastructure|Tube light or bulb", "HST-1", "hostel.kulkarni@campus.edu", 25),

    ("Academic Resources|Book missing or outdated", None, "library.nair@campus.edu", 20),
    ("Academic Resources|Journal or database access", None, "library.nair@campus.edu", 20),
    ("Academic Resources|Broken lab equipment", None, "lab.joshi@campus.edu", 20),

    ("Food & Health|Canteen hygiene", None, "canteen.patil@campus.edu", 20),
    ("Food & Health|Menu or food quality", None, "canteen.patil@campus.edu", 20),
    ("Food & Health|Unsafe drinking water", None, "plumbing.kumar@campus.edu", 20),
    ("Food & Health|Medical room supplies or availability", None, "canteen.patil@campus.edu", 20),

    ("Hostel & Accommodation|Water outage", None, "plumbing.kumar@campus.edu", 20),
    ("Hostel & Accommodation|Electricity outage", None, "facilities.sharma@campus.edu", 20),
    ("Hostel & Accommodation|Pest control", None, "sanitation.rani@campus.edu", 20),
    ("Hostel & Accommodation|Overcrowded room or common area", None, "hostel.kulkarni@campus.edu", 20),
    ("Hostel & Accommodation|Hostel security hazard", None, "hostel.kulkarni@campus.edu", 20),

    ("Safety & Social Environment|Poorly lit or unsafe campus zone", None, "safety.officer@campus.edu", 20),
    ("Safety & Social Environment|Broken safety equipment", None, "safety.officer@campus.edu", 20),

    ("Extracurricular & Engagement|Sports facility damaged", None, "sports.office@campus.edu", 20),
    ("Extracurricular & Engagement|Recreational equipment broken", None, "sports.office@campus.edu", 20),
    ("Extracurricular & Engagement|Event venue or equipment support", None, "sports.office@campus.edu", 20),

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
