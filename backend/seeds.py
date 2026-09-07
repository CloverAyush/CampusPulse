import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.models.enums import UserRole
from app.models.user import User
from app.models.issue_type import IssueType
from app.models.location import Location
from app.models.routing_rule import RoutingRule
from app.services.auth import get_password_hash

def seed_database(db: Session = None):
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    # 1. Seed Users
    users_data = [
        # Students
        {"email": "student.aarav@campus.edu", "full_name": "Aarav Sharma (Student)", "role": UserRole.STUDENT, "department": "Computer Science"},
        {"email": "student.priya@campus.edu", "full_name": "Priya Patel (Student)", "role": UserRole.STUDENT, "department": "Electronics"},
        {"email": "student.rohit@campus.edu", "full_name": "Rohit Verma (Student)", "role": UserRole.STUDENT, "department": "Mechanical"},
        # Handlers
        {"email": "facilities.sharma@campus.edu", "full_name": "Rajesh Sharma (Facilities Handler)", "role": UserRole.HANDLER, "department": "Facilities & Electrical"},
        {"email": "it.rajesh@campus.edu", "full_name": "Amit Deshmukh (IT & Network Handler)", "role": UserRole.HANDLER, "department": "Campus IT Center"},
        {"email": "plumbing.kumar@campus.edu", "full_name": "Suresh Kumar (Plumbing Handler)", "role": UserRole.HANDLER, "department": "Civil & Maintenance"},
        {"email": "cleanliness.rani@campus.edu", "full_name": "Anita Rani (Sanitation Handler)", "role": UserRole.HANDLER, "department": "Housekeeping"},
        # Higher Authority
        {"email": "dean.verma@campus.edu", "full_name": "Dr. K. Verma (Dean of Infrastructure)", "role": UserRole.HIGHER_AUTHORITY, "department": "Deanery"},
        # Admin
        {"email": "admin@campus.edu", "full_name": "CampusPulse Administrator", "role": UserRole.ADMIN, "department": "Administration"},
    ]

    users_map = {}
    default_pw_hash = get_password_hash("demo12345")
    for u in users_data:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            user = User(
                email=u["email"],
                full_name=u["full_name"],
                role=u["role"],
                department=u.get("department"),
                hashed_password=default_pw_hash,
                is_active=True
            )
            db.add(user)
            db.flush()
            users_map[u["email"]] = user
        else:
            users_map[u["email"]] = existing

    # 2. Seed Issue Types
    issue_types_data = [
        {"category": "Electrical", "sub_type": "Ceiling Fan", "description": "Noisy, broken regulator, or stopped spinning", "requires_verification": True},
        {"category": "Electrical", "sub_type": "Tube Light / Bulb", "description": "Flickering or fused lighting", "requires_verification": True},
        {"category": "Electrical", "sub_type": "Switchboard / Plug Socket", "description": "Loose socket, sparks, or dead outlet", "requires_verification": True},
        {"category": "Plumbing", "sub_type": "Tap Leakage / Washbasin", "description": "Continuous water drip or clogged drain", "requires_verification": True},
        {"category": "Plumbing", "sub_type": "Washroom Flush / Drainage", "description": "Clogged line or broken flush handle", "requires_verification": True},
        {"category": "Wi-Fi & Network", "sub_type": "Access Point / Weak Signal", "description": "Cannot connect to campus Wi-Fi or slow speed", "requires_verification": True},
        {"category": "Wi-Fi & Network", "sub_type": "Lab Ethernet Port", "description": "LAN port has no link light", "requires_verification": True},
        {"category": "Cleanliness", "sub_type": "Classroom Dustbin Full", "description": "Overflowing waste in instructional area", "requires_verification": False},
        {"category": "Cleanliness", "sub_type": "Washroom Sanitation", "description": "Floor unmopped or soap dispenser empty", "requires_verification": False},
        {"category": "Water Supply", "sub_type": "Water Cooler Warm / Empty", "description": "Cooling unit stopped or no water output", "requires_verification": True},
        {"category": "Water Supply", "sub_type": "RO Purifier Alert", "description": "Filter beeping or slow dispensing", "requires_verification": True},
        {"category": "Library Facilities", "sub_type": "Reading Hall AC", "description": "Insufficient cooling or excessive noise", "requires_verification": True},
        {"category": "Library Facilities", "sub_type": "Furniture / Bookshelf Damaged", "description": "Broken chair, table, or book stack", "requires_verification": False},
        {"category": "Transport & Parking", "sub_type": "Bicycle Stand Shed", "description": "Leaking shed or damaged rack", "requires_verification": False},
    ]

    issue_types_map = {}
    for it in issue_types_data:
        existing = db.query(IssueType).filter(
            IssueType.category == it["category"],
            IssueType.sub_type == it["sub_type"]
        ).first()
        if not existing:
            item = IssueType(
                category=it["category"],
                sub_type=it["sub_type"],
                description=it.get("description"),
                requires_verification=it["requires_verification"],
                is_active=True
            )
            db.add(item)
            db.flush()
            issue_types_map[f"{it['category']}-{it['sub_type']}"] = item
        else:
            issue_types_map[f"{it['category']}-{it['sub_type']}"] = existing

    # 3. Seed Structured Hierarchical Locations
    # Hierarchy: Building -> Floor -> Room
    locations_data = [
        # Block A (Main Academic Wing)
        {"name": "Block A (Main Academic Wing)", "code": "BLK-A", "building": "Block A", "floor": None, "room": None, "parent_code": None},
        {"name": "Block A - Ground Floor", "code": "BLK-A-FL-0", "building": "Block A", "floor": "Ground Floor", "room": None, "parent_code": "BLK-A"},
        {"name": "Room 101 (Lecture Hall)", "code": "BLK-A-RM-101", "building": "Block A", "floor": "Ground Floor", "room": "Room 101", "parent_code": "BLK-A-FL-0"},
        {"name": "Computer Lab 1", "code": "BLK-A-LAB-1", "building": "Block A", "floor": "Ground Floor", "room": "Lab 1", "parent_code": "BLK-A-FL-0"},
        {"name": "Block A - 2nd Floor", "code": "BLK-A-FL-2", "building": "Block A", "floor": "2nd Floor", "room": None, "parent_code": "BLK-A"},
        {"name": "Room 204 (Classroom)", "code": "BLK-A-RM-204", "building": "Block A", "floor": "2nd Floor", "room": "Room 204", "parent_code": "BLK-A-FL-2"},
        {"name": "Room 205 (Tutorial Room)", "code": "BLK-A-RM-205", "building": "Block A", "floor": "2nd Floor", "room": "Room 205", "parent_code": "BLK-A-FL-2"},

        # Block B (Science Wing)
        {"name": "Block B (Science Wing)", "code": "BLK-B", "building": "Block B", "floor": None, "room": None, "parent_code": None},
        {"name": "Block B - 1st Floor", "code": "BLK-B-FL-1", "building": "Block B", "floor": "1st Floor", "room": None, "parent_code": "BLK-B"},
        {"name": "Physics Lab", "code": "BLK-B-PHY-LAB", "building": "Block B", "floor": "1st Floor", "room": "Physics Lab", "parent_code": "BLK-B-FL-1"},
        {"name": "Chemistry Lab", "code": "BLK-B-CHEM-LAB", "building": "Block B", "floor": "1st Floor", "room": "Chemistry Lab", "parent_code": "BLK-B-FL-1"},

        # Central Library
        {"name": "Central Library", "code": "LIB", "building": "Library", "floor": None, "room": None, "parent_code": None},
        {"name": "Reading Hall (1st Floor)", "code": "LIB-READ-HALL", "building": "Library", "floor": "1st Floor", "room": "Reading Hall", "parent_code": "LIB"},
        {"name": "Circulation Section", "code": "LIB-CIRC", "building": "Library", "floor": "Ground Floor", "room": "Circulation Desk", "parent_code": "LIB"},

        # Hostels & Canteen
        {"name": "Hostel Block 1 (Boys)", "code": "HST-1", "building": "Hostel 1", "floor": None, "room": None, "parent_code": None},
        {"name": "Hostel 1 - Room 112", "code": "HST-1-RM-112", "building": "Hostel 1", "floor": "1st Floor", "room": "Room 112", "parent_code": "HST-1"},
        {"name": "Student Canteen", "code": "CANTEEN", "building": "Amenities", "floor": "Ground Floor", "room": "Main Dining Area", "parent_code": None},
    ]

    locations_map = {}
    for loc in locations_data:
        existing = db.query(Location).filter(Location.code == loc["code"]).first()
        if not existing:
            parent_id = locations_map[loc["parent_code"]].id if loc["parent_code"] and loc["parent_code"] in locations_map else None
            item = Location(
                name=loc["name"],
                code=loc["code"],
                building=loc["building"],
                floor=loc.get("floor"),
                room=loc.get("room"),
                parent_id=parent_id,
                is_active=True
            )
            db.add(item)
            db.flush()
            locations_map[loc["code"]] = item
        else:
            locations_map[loc["code"]] = existing

    # 4. Seed Deterministic Routing Rules
    # Map (issue_type [+ location]) -> responsible handler
    rules_data = [
        # Electrical in Block A -> Rajesh Sharma (high priority)
        {"issue_type_key": "Electrical-Ceiling Fan", "location_code": "BLK-A", "handler_email": "facilities.sharma@campus.edu", "priority": 25},
        {"issue_type_key": "Electrical-Tube Light / Bulb", "location_code": "BLK-A", "handler_email": "facilities.sharma@campus.edu", "priority": 25},
        {"issue_type_key": "Electrical-Switchboard / Plug Socket", "location_code": "BLK-A", "handler_email": "facilities.sharma@campus.edu", "priority": 25},

        # General Electrical for entire campus -> Rajesh Sharma
        {"issue_type_key": "Electrical-Ceiling Fan", "location_code": None, "handler_email": "facilities.sharma@campus.edu", "priority": 10},
        {"issue_type_key": "Electrical-Tube Light / Bulb", "location_code": None, "handler_email": "facilities.sharma@campus.edu", "priority": 10},
        {"issue_type_key": "Electrical-Switchboard / Plug Socket", "location_code": None, "handler_email": "facilities.sharma@campus.edu", "priority": 10},

        # Wi-Fi & Network -> Amit Deshmukh
        {"issue_type_key": "Wi-Fi & Network-Access Point / Weak Signal", "location_code": None, "handler_email": "it.rajesh@campus.edu", "priority": 20},
        {"issue_type_key": "Wi-Fi & Network-Lab Ethernet Port", "location_code": None, "handler_email": "it.rajesh@campus.edu", "priority": 20},

        # Plumbing & Water -> Suresh Kumar
        {"issue_type_key": "Plumbing-Tap Leakage / Washbasin", "location_code": None, "handler_email": "plumbing.kumar@campus.edu", "priority": 20},
        {"issue_type_key": "Plumbing-Washroom Flush / Drainage", "location_code": None, "handler_email": "plumbing.kumar@campus.edu", "priority": 20},
        {"issue_type_key": "Water Supply-Water Cooler Warm / Empty", "location_code": None, "handler_email": "plumbing.kumar@campus.edu", "priority": 20},
        {"issue_type_key": "Water Supply-RO Purifier Alert", "location_code": None, "handler_email": "plumbing.kumar@campus.edu", "priority": 20},

        # Cleanliness & Sanitation -> Anita Rani
        {"issue_type_key": "Cleanliness-Classroom Dustbin Full", "location_code": None, "handler_email": "cleanliness.rani@campus.edu", "priority": 20},
        {"issue_type_key": "Cleanliness-Washroom Sanitation", "location_code": None, "handler_email": "cleanliness.rani@campus.edu", "priority": 20},

        # Library AC -> Rajesh Sharma
        {"issue_type_key": "Library Facilities-Reading Hall AC", "location_code": "LIB", "handler_email": "facilities.sharma@campus.edu", "priority": 25},
        {"issue_type_key": "Library Facilities-Furniture / Bookshelf Damaged", "location_code": "LIB", "handler_email": "facilities.sharma@campus.edu", "priority": 25},

        # Global Fallback -> Rajesh Sharma
        {"issue_type_key": None, "location_code": None, "handler_email": "facilities.sharma@campus.edu", "priority": 1},
    ]

    for r in rules_data:
        it_id = issue_types_map[r["issue_type_key"]].id if r["issue_type_key"] and r["issue_type_key"] in issue_types_map else None
        loc_id = locations_map[r["location_code"]].id if r["location_code"] and r["location_code"] in locations_map else None
        handler = users_map.get(r["handler_email"])

        if handler:
            existing = db.query(RoutingRule).filter(
                RoutingRule.issue_type_id == it_id,
                RoutingRule.location_id == loc_id,
                RoutingRule.handler_id == handler.id
            ).first()

            if not existing:
                rule = RoutingRule(
                    issue_type_id=it_id,
                    location_id=loc_id,
                    handler_id=handler.id,
                    priority=r["priority"],
                    is_active=True
                )
                db.add(rule)

    db.commit()
    if should_close:
        db.close()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_database()

