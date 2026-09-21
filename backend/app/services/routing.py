import logging
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.location import Location
from app.models.routing_rule import RoutingRule
from app.models.user import User

logger = logging.getLogger(__name__)

MAX_LOCATION_DEPTH = 32


@dataclass(frozen=True)
class RoutingResult:
    handler: Optional[User]
    rule: Optional[RoutingRule]
    match_kind: str

    @property
    def needs_triage(self) -> bool:
        return self.handler is None or self.match_kind in {"catch_all", "unrouted"}


def collect_ancestor_ids(db: Session, location_id: int) -> List[int]:
    """Walk a location up to its building. Guarded against a parent cycle, which a
    mis-entered admin hierarchy can otherwise turn into an infinite loop."""
    ancestors: List[int] = []
    seen = {location_id}
    current = db.query(Location).filter(Location.id == location_id).first()

    while current is not None and current.parent_id is not None:
        if current.parent_id in seen:
            logger.error(
                "Location hierarchy contains a cycle; stopping ancestor walk",
                extra={"location_id": location_id, "repeated_parent_id": current.parent_id},
            )
            break
        if len(ancestors) >= MAX_LOCATION_DEPTH:
            logger.error(
                "Location hierarchy deeper than supported; stopping ancestor walk",
                extra={"location_id": location_id, "max_depth": MAX_LOCATION_DEPTH},
            )
            break
        ancestors.append(current.parent_id)
        seen.add(current.parent_id)
        current = db.query(Location).filter(Location.id == current.parent_id).first()

    return ancestors


def _first_active_rule(db: Session, issue_type_id: Optional[int], location_id: Optional[int]) -> Optional[RoutingRule]:
    query = db.query(RoutingRule).filter(RoutingRule.is_active.is_(True))
    query = (
        query.filter(RoutingRule.issue_type_id == issue_type_id)
        if issue_type_id is not None
        else query.filter(RoutingRule.issue_type_id.is_(None))
    )
    query = (
        query.filter(RoutingRule.location_id == location_id)
        if location_id is not None
        else query.filter(RoutingRule.location_id.is_(None))
    )
    rule = query.order_by(desc(RoutingRule.priority), RoutingRule.id).first()
    if rule and rule.handler and rule.handler.is_active:
        return rule
    return None


def resolve_handler(db: Session, issue_type_id: int, location_id: int) -> RoutingResult:
    """Deterministic handler lookup. Precedence, highest first:

    1. exact       rule for (issue type, exact location)
    2. hierarchy   rule for (issue type, an ancestor location), nearest ancestor first
    3. type        rule for (issue type, any location)
    4. location    rule for (any issue type, exact location)
    5. ancestor    rule for (any issue type, an ancestor location)
    6. catch_all   rule for (any issue type, any location) -- the miscellaneous handler
    7. unrouted    no rule matched; the issue is flagged for admin triage

    No step consults free text, and the same inputs always produce the same handler.
    """
    rule = _first_active_rule(db, issue_type_id, location_id)
    if rule:
        return RoutingResult(rule.handler, rule, "exact")

    ancestor_ids = collect_ancestor_ids(db, location_id)

    for ancestor_id in ancestor_ids:
        rule = _first_active_rule(db, issue_type_id, ancestor_id)
        if rule:
            return RoutingResult(rule.handler, rule, "hierarchy")

    rule = _first_active_rule(db, issue_type_id, None)
    if rule:
        return RoutingResult(rule.handler, rule, "issue_type_default")

    rule = _first_active_rule(db, None, location_id)
    if rule:
        return RoutingResult(rule.handler, rule, "location_default")

    for ancestor_id in ancestor_ids:
        rule = _first_active_rule(db, None, ancestor_id)
        if rule:
            return RoutingResult(rule.handler, rule, "location_ancestor_default")

    rule = _first_active_rule(db, None, None)
    if rule:
        logger.info(
            "Issue routed to the miscellaneous catch-all handler",
            extra={"issue_type_id": issue_type_id, "location_id": location_id, "handler_id": rule.handler_id},
        )
        return RoutingResult(rule.handler, rule, "catch_all")

    logger.error(
        "No routing rule matched and no catch-all handler is configured",
        extra={"issue_type_id": issue_type_id, "location_id": location_id},
    )
    return RoutingResult(None, None, "unrouted")


def find_admins(db: Session) -> List[User]:
    return db.query(User).filter(User.is_active.is_(True), User.role == UserRole.ADMIN).all()
