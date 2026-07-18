"""
Bootstrap script to create the initial administrator account.

Usage:
    python -m scripts.create_admin --name "Admin Name" --email admin@example.com --password "securepassword"

Or use environment variables:
    ADMIN_NAME, ADMIN_EMAIL, ADMIN_PASSWORD

Example:
    python -m scripts.create_admin --name "System Admin" --email admin@xdmra.local --password "ChangeMe123!"
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import User, UserRole
from app.core.security import hash_password


def create_admin(name: str, email: str, password: str) -> User:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"Error: User with email '{email}' already exists.")
            sys.exit(1)

        if len(password) < 8:
            print("Error: Password must be at least 8 characters long.")
            sys.exit(1)

        admin = User(
            full_name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.admin,
            is_active=1,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"Administrator account created successfully:")
        print(f"  Name:  {admin.full_name}")
        print(f"  Email: {admin.email}")
        print(f"  Role:  {admin.role.value}")
        print(f"  ID:    {admin.id}")

        return admin

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Create initial administrator account")
    parser.add_argument("--name", required=False, help="Full name of the administrator")
    parser.add_argument("--email", required=False, help="Email address of the administrator")
    parser.add_argument("--password", required=False, help="Password for the administrator")

    args = parser.parse_args()

    name = args.name or os.getenv("ADMIN_NAME")
    email = args.email or os.getenv("ADMIN_EMAIL")
    password = args.password or os.getenv("ADMIN_PASSWORD")

    if not all([name, email, password]):
        print("Error: Name, email, and password are required.")
        print("Provide them via command line arguments or environment variables (ADMIN_NAME, ADMIN_EMAIL, ADMIN_PASSWORD)")
        parser.print_help()
        sys.exit(1)

    create_admin(name, email, password)


if __name__ == "__main__":
    main()