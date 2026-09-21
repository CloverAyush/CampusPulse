"""Create the first administrator account.

    python -m scripts.create_admin --email you@campus.edu --name "Your Name"

The password is prompted for, never passed on the command line where it would land
in shell history, and never defaulted.
"""

import argparse
import getpass
import sys
from typing import List, Optional

from pydantic import ValidationError as PydanticValidationError

from app.database import SessionLocal
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreateByAdmin
from app.services.auth import get_password_hash


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Create a CampusPulse administrator.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args(argv)

    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Confirm password: "):
        print("Passwords did not match.", file=sys.stderr)
        return 1

    try:
        payload = UserCreateByAdmin(
            email=args.email,
            full_name=args.name,
            password=password,
            role=UserRole.ADMIN,
        )
    except PydanticValidationError as exc:
        for error in exc.errors():
            print(f"{'.'.join(str(p) for p in error['loc'])}: {error['msg']}", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == payload.email.lower()).first():
            print(f"An account already exists for {payload.email}.", file=sys.stderr)
            return 1

        db.add(
            User(
                email=payload.email.lower(),
                full_name=payload.full_name,
                role=UserRole.ADMIN,
                hashed_password=get_password_hash(password),
                is_active=True,
            )
        )
        db.commit()
    finally:
        db.close()

    print(f"Administrator created: {payload.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
