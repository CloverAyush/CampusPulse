import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, parse_pagination, require_admin, require_staff
from app.database import get_db
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.enums import IssueStatus, UserRole
from app.models.issue import Issue
from app.models.issue_type import IssueType
from app.models.location import Location
from app.models.routing_rule import RoutingRule
from app.models.user import User
from app.schemas.issue import Page
from app.schemas.issue_type import IssueTypeCreate, IssueTypeOut, IssueTypeUpdate
from app.schemas.location import LocationCreate, LocationOut, LocationUpdate
from app.schemas.routing_rule import (
    RoutingPreview,
    RoutingPreviewOut,
    RoutingRuleCreate,
    RoutingRuleOut,
    RoutingRuleUpdate,
)
from app.schemas.user import UserCreateByAdmin, UserOut, UserPublic, UserUpdateByAdmin
from app.services.auth import get_password_hash
from app.services.routing import MAX_LOCATION_DEPTH, resolve_handler

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/taxonomies")
def get_taxonomies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Drives the student report form. Returns only what the form needs; handler
    contact details are not part of that."""
    issue_types = (
        db.query(IssueType)
        .filter(IssueType.is_active.is_(True))
        .order_by(IssueType.category, IssueType.sub_type)
        .all()
    )
    locations = (
        db.query(Location)
        .filter(Location.is_active.is_(True))
        .order_by(Location.building, Location.floor, Location.room)
        .all()
    )

    return {
        "issue_types": [IssueTypeOut.model_validate(item) for item in issue_types],
        "locations": [LocationOut.model_validate(item) for item in locations],
    }


@router.get("/issue-types", response_model=List[IssueTypeOut])
def list_issue_types(
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    query = db.query(IssueType)
    if not include_inactive:
        query = query.filter(IssueType.is_active.is_(True))
    return query.order_by(IssueType.category, IssueType.sub_type).all()


@router.post("/issue-types", response_model=IssueTypeOut, status_code=status.HTTP_201_CREATED)
def create_issue_type(
    payload: IssueTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    issue_type = IssueType(**payload.model_dump())
    db.add(issue_type)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("That category and sub-type already exist")

    db.refresh(issue_type)
    logger.info("Issue type created", extra={"issue_type_id": issue_type.id, "actor_id": current_user.id})
    return issue_type


@router.put("/issue-types/{issue_type_id}", response_model=IssueTypeOut)
def update_issue_type(
    issue_type_id: int,
    payload: IssueTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    issue_type = db.query(IssueType).filter(IssueType.id == issue_type_id).first()
    if not issue_type:
        raise NotFoundError("Issue type not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(issue_type, key, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("That category and sub-type already exist")

    db.refresh(issue_type)
    logger.info("Issue type updated", extra={"issue_type_id": issue_type.id, "actor_id": current_user.id})
    return issue_type


def _validate_location_parent(db: Session, parent_id: Optional[int], location_id: Optional[int] = None) -> None:
    """A parent cycle would make routing walk in circles, so it is rejected at the
    point of entry rather than defended against on every lookup."""
    if parent_id is None:
        return

    if location_id is not None and parent_id == location_id:
        raise ValidationError("A location cannot be its own parent")

    parent = db.query(Location).filter(Location.id == parent_id).first()
    if not parent:
        raise NotFoundError("Parent location not found")

    seen = {location_id} if location_id is not None else set()
    current = parent
    depth = 0
    while current is not None:
        if current.id in seen:
            raise ValidationError("That parent would create a loop in the location hierarchy")
        seen.add(current.id)
        depth += 1
        if depth > MAX_LOCATION_DEPTH:
            raise ValidationError(f"Location hierarchy may not be deeper than {MAX_LOCATION_DEPTH} levels")
        current = db.query(Location).filter(Location.id == current.parent_id).first() if current.parent_id else None


@router.get("/locations", response_model=List[LocationOut])
def list_locations(
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    query = db.query(Location)
    if not include_inactive:
        query = query.filter(Location.is_active.is_(True))
    return query.order_by(Location.building, Location.floor, Location.room).all()


@router.post("/locations", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
def create_location(
    payload: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    _validate_location_parent(db, payload.parent_id)

    location = Location(**payload.model_dump())
    db.add(location)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("A location with that code already exists")

    db.refresh(location)
    logger.info("Location created", extra={"location_id": location.id, "actor_id": current_user.id})
    return location


@router.put("/locations/{location_id}", response_model=LocationOut)
def update_location(
    location_id: int,
    payload: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise NotFoundError("Location not found")

    updates = payload.model_dump(exclude_unset=True)
    if "parent_id" in updates:
        _validate_location_parent(db, updates["parent_id"], location_id)

    for key, value in updates.items():
        setattr(location, key, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("A location with that code already exists")

    db.refresh(location)
    logger.info("Location updated", extra={"location_id": location.id, "actor_id": current_user.id})
    return location


def _validate_rule_targets(db: Session, issue_type_id: Optional[int], location_id: Optional[int], handler_id: Optional[int]) -> None:
    if issue_type_id is not None and not db.query(IssueType.id).filter(IssueType.id == issue_type_id).first():
        raise NotFoundError("Issue type not found")
    if location_id is not None and not db.query(Location.id).filter(Location.id == location_id).first():
        raise NotFoundError("Location not found")
    if handler_id is not None:
        handler = db.query(User).filter(
            User.id == handler_id,
            User.is_active.is_(True),
            User.role.in_([UserRole.HANDLER, UserRole.HIGHER_AUTHORITY, UserRole.ADMIN]),
        ).first()
        if not handler:
            raise ValidationError("Routing rules can only target an active handler, authority or admin")


@router.get("/routing-rules", response_model=List[RoutingRuleOut])
def list_routing_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    return (
        db.query(RoutingRule)
        .options(
            joinedload(RoutingRule.handler),
            joinedload(RoutingRule.issue_type),
            joinedload(RoutingRule.location),
        )
        .order_by(RoutingRule.priority.desc(), RoutingRule.id)
        .all()
    )


@router.post("/routing-rules", response_model=RoutingRuleOut, status_code=status.HTTP_201_CREATED)
def create_routing_rule(
    payload: RoutingRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    _validate_rule_targets(db, payload.issue_type_id, payload.location_id, payload.handler_id)

    rule = RoutingRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    logger.info("Routing rule created", extra={"rule_id": rule.id, "actor_id": current_user.id})
    return rule


@router.put("/routing-rules/{rule_id}", response_model=RoutingRuleOut)
def update_routing_rule(
    rule_id: int,
    payload: RoutingRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    rule = db.query(RoutingRule).filter(RoutingRule.id == rule_id).first()
    if not rule:
        raise NotFoundError("Routing rule not found")

    updates = payload.model_dump(exclude_unset=True)
    _validate_rule_targets(
        db,
        updates.get("issue_type_id", rule.issue_type_id),
        updates.get("location_id", rule.location_id),
        updates.get("handler_id", rule.handler_id),
    )

    for key, value in updates.items():
        setattr(rule, key, value)

    db.commit()
    db.refresh(rule)
    logger.info("Routing rule updated", extra={"rule_id": rule.id, "actor_id": current_user.id})
    return rule


@router.delete("/routing-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routing_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    rule = db.query(RoutingRule).filter(RoutingRule.id == rule_id).first()
    if not rule:
        raise NotFoundError("Routing rule not found")

    is_catch_all = rule.issue_type_id is None and rule.location_id is None
    if is_catch_all:
        remaining = (
            db.query(RoutingRule)
            .filter(
                RoutingRule.issue_type_id.is_(None),
                RoutingRule.location_id.is_(None),
                RoutingRule.is_active.is_(True),
                RoutingRule.id != rule.id,
            )
            .count()
        )
        if remaining == 0:
            raise ConflictError(
                "This is the catch-all rule for miscellaneous issues. Configure a "
                "replacement before deleting it, or reports with no matching rule will "
                "have nowhere to go."
            )

    db.delete(rule)
    db.commit()
    logger.info("Routing rule deleted", extra={"rule_id": rule_id, "actor_id": current_user.id})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/routing-rules/preview", response_model=RoutingPreviewOut)
def preview_routing(
    payload: RoutingPreview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Lets an admin see which handler a given type and location resolves to before
    a student finds out the hard way."""
    result = resolve_handler(db, payload.issue_type_id, payload.location_id)
    return RoutingPreviewOut(
        handler=UserPublic.model_validate(result.handler) if result.handler else None,
        matched_rule_id=result.rule.id if result.rule else None,
        match_kind=result.match_kind,
    )


@router.get("/users", response_model=Page[UserOut])
def list_users(
    role: Optional[UserRole] = Query(default=None),
    include_inactive: bool = Query(default=False),
    limit: Optional[int] = Query(default=None),
    offset: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    resolved_limit, resolved_offset = parse_pagination(limit, offset)

    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if not include_inactive:
        query = query.filter(User.is_active.is_(True))

    total = query.count()
    users = query.order_by(User.full_name, User.id).limit(resolved_limit).offset(resolved_offset).all()

    return Page[UserOut](
        items=[UserOut.model_validate(user) for user in users],
        total=total,
        limit=resolved_limit,
        offset=resolved_offset,
    )


@router.get("/handlers", response_model=List[UserPublic])
def list_handlers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    """Names and roles only, for reassignment and routing-rule dropdowns."""
    return (
        db.query(User)
        .filter(
            User.is_active.is_(True),
            User.role.in_([UserRole.HANDLER, UserRole.HIGHER_AUTHORITY, UserRole.ADMIN]),
        )
        .order_by(User.full_name)
        .all()
    )


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_staff_user(
    payload: UserCreateByAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = User(
        email=payload.email.lower(),
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name.strip(),
        role=payload.role,
        department=payload.department,
        phone=payload.phone,
        is_active=payload.is_active,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("An account with this email already exists")

    db.refresh(user)
    logger.info("Account created by admin",
                extra={"new_user_id": user.id, "new_user_role": user.role.value, "actor_id": current_user.id})
    return user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdateByAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User not found")

    updates = payload.model_dump(exclude_unset=True)

    if user.id == current_user.id:
        if updates.get("is_active") is False:
            raise ValidationError("You cannot deactivate your own account")
        if "role" in updates and updates["role"] != UserRole.ADMIN:
            raise ValidationError("You cannot remove your own admin role")

    if updates.get("is_active") is False:
        open_issues = (
            db.query(Issue)
            .filter(Issue.current_handler_id == user.id, Issue.status != IssueStatus.VERIFIED_CLOSED)
            .count()
        )
        if open_issues:
            raise ConflictError(
                f"{user.full_name} still has {open_issues} open issue(s). Reassign them first."
            )

    for key, value in updates.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    logger.info("Account updated by admin", extra={"updated_user_id": user.id, "actor_id": current_user.id})
    return user
