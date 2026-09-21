import pytest

from app.models.location import Location
from app.models.routing_rule import RoutingRule
from app.services.routing import MAX_LOCATION_DEPTH, collect_ancestor_ids, resolve_handler


def test_exact_rule_wins_over_ancestor(db, campus):
    db.add(RoutingRule(issue_type_id=campus["fan_type"].id, location_id=campus["room_204"].id,
                       handler_id=campus["it_handler"].id, priority=5))
    db.commit()

    result = resolve_handler(db, campus["fan_type"].id, campus["room_204"].id)

    assert result.match_kind == "exact"
    assert result.handler.id == campus["it_handler"].id


def test_falls_back_to_ancestor_location_rule(db, campus):
    result = resolve_handler(db, campus["fan_type"].id, campus["room_204"].id)

    assert result.match_kind == "hierarchy"
    assert result.handler.id == campus["facilities"].id


def test_issue_type_default_applies_anywhere(db, campus):
    result = resolve_handler(db, campus["wifi_type"].id, campus["canteen"].id)

    assert result.match_kind == "issue_type_default"
    assert result.handler.id == campus["it_handler"].id


def test_unmatched_issue_goes_to_the_catch_all_handler(db, campus):
    result = resolve_handler(db, campus["misc_type"].id, campus["canteen"].id)

    assert result.match_kind == "catch_all"
    assert result.handler.id == campus["estate"].id
    assert result.needs_triage is True


def test_inactive_rule_is_skipped(db, campus):
    db.query(RoutingRule).filter(RoutingRule.issue_type_id == campus["fan_type"].id).update({"is_active": False})
    db.commit()

    result = resolve_handler(db, campus["fan_type"].id, campus["room_204"].id)

    assert result.match_kind == "catch_all"
    assert result.handler.id == campus["estate"].id


def test_rule_pointing_at_a_deactivated_handler_is_skipped(db, campus):
    campus["facilities"].is_active = False
    db.commit()

    result = resolve_handler(db, campus["fan_type"].id, campus["room_204"].id)

    assert result.handler.id == campus["estate"].id


def test_no_rules_at_all_yields_unrouted(db, campus):
    db.query(RoutingRule).delete()
    db.commit()

    result = resolve_handler(db, campus["fan_type"].id, campus["room_204"].id)

    assert result.match_kind == "unrouted"
    assert result.handler is None


def test_routing_is_deterministic_across_repeated_calls(db, campus):
    handlers = {resolve_handler(db, campus["fan_type"].id, campus["room_204"].id).handler.id for _ in range(20)}

    assert len(handlers) == 1


def test_equal_priority_rules_resolve_by_id_not_by_chance(db, campus):
    first = RoutingRule(issue_type_id=campus["bin_type"].id, location_id=None,
                        handler_id=campus["facilities"].id, priority=15)
    second = RoutingRule(issue_type_id=campus["bin_type"].id, location_id=None,
                         handler_id=campus["it_handler"].id, priority=15)
    db.add_all([first, second])
    db.commit()

    results = {resolve_handler(db, campus["bin_type"].id, campus["canteen"].id).rule.id for _ in range(10)}

    assert results == {first.id}


def test_ancestor_walk_survives_a_hierarchy_loop(db, campus):
    """A cycle used to hang the worker thread on every report to that building."""
    campus["block_a"].parent_id = campus["room_204"].id
    db.commit()

    ancestors = collect_ancestor_ids(db, campus["room_204"].id)

    assert len(ancestors) <= MAX_LOCATION_DEPTH
    assert resolve_handler(db, campus["fan_type"].id, campus["room_204"].id).handler is not None


@pytest.mark.parametrize("depth", [MAX_LOCATION_DEPTH + 5])
def test_ancestor_walk_stops_at_the_depth_cap(db, campus, depth):
    parent_id = None
    leaf_id = None
    for index in range(depth):
        location = Location(name=f"Level {index}", code=f"DEEP-{index}",
                            building="Deep", parent_id=parent_id)
        db.add(location)
        db.flush()
        parent_id = location.id
        leaf_id = location.id

    assert len(collect_ancestor_ids(db, leaf_id)) <= MAX_LOCATION_DEPTH
