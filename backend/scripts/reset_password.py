"""Set a new password for an existing account.

    python -m scripts.reset_password --email facilities.sharma@campus.edu
    python -m scripts.reset_password --email facilities.sharma@campus.edu --generate

By default the new password is prompted for, never passed on the command line
where it would land in shell history. With --generate a random one is created and
printed once. Existing sessions stay valid until their tokens expire; rotate
SECRET_KEY if you need to sign everyone out immediately.
"""

import argparse
import getpass
import sys
from typing import List, Optional

from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserRegister
from app.services.auth import get_password_hash
from scripts.seed import generate_password


def reset_password(db: Session, email: str, new_password: str) -> bool:
    """Returns False if no account has that email. Raises ValueError if the
    password breaks the same policy registration enforces."""
    try:
        UserRegister(email=email, full_name="Placeholder", password=new_password)
    except PydanticValidationError as exc:
        raise ValueError("; ".join(error["msg"] for error in exc.errors())) from exc

    user = db.query(User).filter(User.email == email.lower()).first()
    if user is None:
        return False

    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Reset a CampusPulse account password.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--generate", action="store_true", help="Create and print a random password.")
    args = parser.parse_args(argv)

    if args.generate:
        password = generate_password()
    else:
        password = getpass.getpass("New password: ")
        if password != getpass.getpass("Confirm new password: "):
            print("Passwords did not match.", file=sys.stderr)
            return 1

    db = SessionLocal()
    try:
        try:
            found = reset_password(db, args.email, password)
        except ValueError as exc:
            print(f"Password rejected: {exc}", file=sys.stderr)
            return 1
    finally:
        db.close()

    if not found:
        print(f"No account found for {args.email}.", file=sys.stderr)
        return 1

    if args.generate:
        print(f"New password for {args.email}: {password}")
        print("Shown once. Store it somewhere safe.")
    else:
        print(f"Password updated for {args.email}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
