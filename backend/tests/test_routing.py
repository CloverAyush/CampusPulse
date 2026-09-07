from app.services.routing import resolve_handler_deterministically
from app.models.routing_rule import RoutingRule

def test_hierarchy_routing_ancestor_match(db, seed_data):
    """
    Test that an issue created at Room 204 (child of Block A) matches
    the routing rule defined at the ancestor level (Block A).
    """
    handler = resolve_handler_deterministically(
        db=db,
        issue_type_id=seed_data["fan_type"].id,
        location_id=seed_data["room_204"].id
    )
    assert handler is not None
    assert handler.id == seed_data["facilities_handler"].id
    assert handler.email == "facilities@campus.edu"

def test_global_type_routing(db, seed_data):
    """
    Test that an issue type with a global rule (location_id=None) matches correctly.
    """
    handler = resolve_handler_deterministically(
        db=db,
        issue_type_id=seed_data["wifi_type"].id,
        location_id=seed_data["room_204"].id
    )
    assert handler is not None
    assert handler.id == seed_data["it_handler"].id
    assert handler.email == "it@campus.edu"

def test_global_fallback_routing(db, seed_data):
    """
    Test that an issue with no specific type or location rule resolves to global fallback.
    """
    handler = resolve_handler_deterministically(
        db=db,
        issue_type_id=seed_data["cleanliness_type"].id,
        location_id=seed_data["room_204"].id
    )
    assert handler is not None
    assert handler.id == seed_data["facilities_handler"].id

def test_specific_override_takes_precedence(db, seed_data):
    """
    Test that adding a high-priority specific rule for Room 204 overrides general rules.
    """
    specific_rule = RoutingRule(
        issue_type_id=seed_data["wifi_type"].id,
        location_id=seed_data["room_204"].id,
        handler_id=seed_data["facilities_handler"].id,
        priority=50,
        is_active=True
    )
    db.add(specific_rule)
    db.commit()

    handler = resolve_handler_deterministically(
        db=db,
        issue_type_id=seed_data["wifi_type"].id,
        location_id=seed_data["room_204"].id
    )
    assert handler is not None
    assert handler.id == seed_data["facilities_handler"].id

