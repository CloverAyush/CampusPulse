from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.issue_type import IssueType
from app.models.location import Location
from app.models.routing_rule import RoutingRule
from app.models.enums import UserRole
from app.schemas.issue_type import IssueTypeCreate, IssueTypeUpdate, IssueTypeOut
from app.schemas.location import LocationCreate, LocationUpdate, LocationOut
from app.schemas.routing_rule import RoutingRuleCreate, RoutingRuleUpdate, RoutingRuleOut
from app.schemas.user import UserOut
from app.api.deps import get_current_user, require_roles

router = APIRouter()

# Admin & Authority & General Taxonomy Access

@router.get("/taxonomies")
def get_taxonomies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns available active IssueTypes, Locations, and Handlers for form selectors.
    """
    issue_types = db.query(IssueType).filter(IssueType.is_active.is_(True)).order_by(IssueType.category, IssueType.sub_type).all()
    locations = db.query(Location).filter(Location.is_active.is_(True)).order_by(Location.building, Location.floor, Location.room).all()
    handlers = db.query(User).filter(User.role.in_([UserRole.HANDLER, UserRole.HIGHER_AUTHORITY]), User.is_active.is_(True)).all()

    return {
        "issue_types": [IssueTypeOut.model_validate(it) for it in issue_types],
        "locations": [LocationOut.model_validate(loc) for loc in locations],
        "handlers": [UserOut.model_validate(h) for h in handlers]
    }

# ----------------- Issue Types -----------------

@router.get("/issue-types", response_model=List[IssueTypeOut])
def list_issue_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(IssueType).order_by(IssueType.category, IssueType.sub_type).all()

@router.post("/issue-types", response_model=IssueTypeOut, status_code=status.HTTP_201_CREATED)
def create_issue_type(
    item_in: IssueTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    issue_type = IssueType(**item_in.model_dump())
    db.add(issue_type)
    db.commit()
    db.refresh(issue_type)
    return issue_type

@router.put("/issue-types/{id}", response_model=IssueTypeOut)
def update_issue_type(
    id: int,
    item_in: IssueTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    issue_type = db.query(IssueType).filter(IssueType.id == id).first()
    if not issue_type:
        raise HTTPException(status_code=404, detail="IssueType not found")
    
    update_data = item_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(issue_type, key, value)
    
    db.commit()
    db.refresh(issue_type)
    return issue_type

# ----------------- Locations -----------------

@router.get("/locations", response_model=List[LocationOut])
def list_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Location).order_by(Location.building, Location.floor, Location.room).all()

@router.post("/locations", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
def create_location(
    item_in: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    loc = Location(**item_in.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc

@router.put("/locations/{id}", response_model=LocationOut)
def update_location(
    id: int,
    item_in: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    loc = db.query(Location).filter(Location.id == id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    
    update_data = item_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(loc, key, value)
    
    db.commit()
    db.refresh(loc)
    return loc

# ----------------- Routing Rules -----------------

@router.get("/routing-rules", response_model=List[RoutingRuleOut])
def list_routing_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(RoutingRule).order_by(RoutingRule.priority.desc()).all()

@router.post("/routing-rules", response_model=RoutingRuleOut, status_code=status.HTTP_201_CREATED)
def create_routing_rule(
    item_in: RoutingRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    rule = RoutingRule(**item_in.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.put("/routing-rules/{id}", response_model=RoutingRuleOut)
def update_routing_rule(
    id: int,
    item_in: RoutingRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    rule = db.query(RoutingRule).filter(RoutingRule.id == id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="RoutingRule not found")
    
    update_data = item_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    
    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/routing-rules/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routing_rule(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    rule = db.query(RoutingRule).filter(RoutingRule.id == id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="RoutingRule not found")
    db.delete(rule)
    db.commit()
    return None

# ----------------- Users -----------------

@router.get("/users", response_model=List[UserOut])
def list_users(
    role: Optional[UserRole] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.HIGHER_AUTHORITY]))
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.all()

# ----------------- Seed Data Trigger -----------------

@router.post("/seed-data")
def trigger_seed_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Populates sample college campus dataset for testing.
    """
    from seeds import seed_database
    seed_database(db)
    return {"message": "Database successfully seeded with realistic campus dataset."}

