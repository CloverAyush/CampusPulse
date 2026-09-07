from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.routing_rule import RoutingRule
from app.models.location import Location
from app.models.user import User
from app.models.enums import UserRole

def resolve_handler_deterministically(
    db: Session,
    issue_type_id: int,
    location_id: int
) -> Optional[User]:
    """
    Deterministically resolves the assigned handler for an issue based on
    IssueType and Location hierarchy using the RoutingRule configuration table.
    
    Resolution precedence:
    1. Exact Match: Rule for (issue_type_id, exact location_id)
    2. Hierarchy Match: Rule for (issue_type_id, ancestor location_id)
    3. Issue Type Default: Rule for (issue_type_id, location_id = NULL)
    4. Location Default: Rule for (issue_type_id = NULL, exact location_id or ancestor)
    5. Global Fallback: Rule for (issue_type_id = NULL, location_id = NULL)
    6. System Fallback: First active HANDLER / ADMIN user
    """
    # 1. Exact Match (issue_type_id + location_id)
    exact_rule = (
        db.query(RoutingRule)
        .filter(
            RoutingRule.is_active.is_(True),
            RoutingRule.issue_type_id == issue_type_id,
            RoutingRule.location_id == location_id
        )
        .order_by(desc(RoutingRule.priority))
        .first()
    )
    if exact_rule and exact_rule.handler and exact_rule.handler.is_active:
        return exact_rule.handler

    # 2. Hierarchy Match: walk up location ancestor chain for issue_type_id
    current_loc = db.query(Location).filter(Location.id == location_id).first()
    ancestor_ids = []
    while current_loc and current_loc.parent_id:
        ancestor_ids.append(current_loc.parent_id)
        current_loc = db.query(Location).filter(Location.id == current_loc.parent_id).first()

    for anc_id in ancestor_ids:
        anc_rule = (
            db.query(RoutingRule)
            .filter(
                RoutingRule.is_active.is_(True),
                RoutingRule.issue_type_id == issue_type_id,
                RoutingRule.location_id == anc_id
            )
            .order_by(desc(RoutingRule.priority))
            .first()
        )
        if anc_rule and anc_rule.handler and anc_rule.handler.is_active:
            return anc_rule.handler

    # 3. Issue Type Default (no location constraint)
    type_rule = (
        db.query(RoutingRule)
        .filter(
            RoutingRule.is_active.is_(True),
            RoutingRule.issue_type_id == issue_type_id,
            RoutingRule.location_id.is_(None)
        )
        .order_by(desc(RoutingRule.priority))
        .first()
    )
    if type_rule and type_rule.handler and type_rule.handler.is_active:
        return type_rule.handler

    # 4. Location Default (any issue type for this location or its ancestors)
    loc_rule = (
        db.query(RoutingRule)
        .filter(
            RoutingRule.is_active.is_(True),
            RoutingRule.issue_type_id.is_(None),
            RoutingRule.location_id == location_id
        )
        .order_by(desc(RoutingRule.priority))
        .first()
    )
    if loc_rule and loc_rule.handler and loc_rule.handler.is_active:
        return loc_rule.handler

    for anc_id in ancestor_ids:
        anc_loc_rule = (
            db.query(RoutingRule)
            .filter(
                RoutingRule.is_active.is_(True),
                RoutingRule.issue_type_id.is_(None),
                RoutingRule.location_id == anc_id
            )
            .order_by(desc(RoutingRule.priority))
            .first()
        )
        if anc_loc_rule and anc_loc_rule.handler and anc_loc_rule.handler.is_active:
            return anc_loc_rule.handler

    # 5. Global Fallback Rule
    global_rule = (
        db.query(RoutingRule)
        .filter(
            RoutingRule.is_active.is_(True),
            RoutingRule.issue_type_id.is_(None),
            RoutingRule.location_id.is_(None)
        )
        .order_by(desc(RoutingRule.priority))
        .first()
    )
    if global_rule and global_rule.handler and global_rule.handler.is_active:
        return global_rule.handler

    # 6. System Fallback: Any active handler or admin
    fallback_user = (
        db.query(User)
        .filter(
            User.is_active.is_(True),
            User.role.in_([UserRole.HANDLER, UserRole.ADMIN])
        )
        .first()
    )
    return fallback_user

