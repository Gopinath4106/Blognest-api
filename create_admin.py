"""
Utility script to create (or promote) an admin account.

Usage:
    python create_admin.py
    python create_admin.py --email admin@blognest.com --password Admin@123 --name "Site Admin"

If no arguments are given, it uses the defaults from config.py / .env
(ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME), or sensible built-in defaults.
If a user with that email already exists, it is promoted to admin and its
password is left unchanged (unless --password is explicitly given).
"""

import argparse
import sqlite3
from werkzeug.security import generate_password_hash

from config import Config
from database import init_db
from app import create_app


def main():
    parser = argparse.ArgumentParser(description="Create or promote an admin user for AI Blog Nest.")
    parser.add_argument("--email", default=Config.DEFAULT_ADMIN_EMAIL)
    parser.add_argument("--password", default=Config.DEFAULT_ADMIN_PASSWORD)
    parser.add_argument("--name", default=Config.DEFAULT_ADMIN_NAME)
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        init_db(app)
        conn = sqlite3.connect(app.config["DATABASE_PATH"])
        conn.row_factory = sqlite3.Row
        existing = conn.execute("SELECT * FROM users WHERE email = ?", (args.email,)).fetchone()

        if existing:
            conn.execute("UPDATE users SET role = 'admin' WHERE id = ?", (existing["id"],))
            conn.commit()
            print(f"Existing user '{args.email}' has been promoted to admin.")
        else:
            password_hash = generate_password_hash(args.password)
            conn.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
                (args.name, args.email, password_hash),
            )
            conn.commit()
            print("Admin account created successfully!")
            print(f"  Email:    {args.email}")
            print(f"  Password: {args.password}")
            print("  Please log in and change this password if this is a shared/deployed environment.")

        conn.close()


if __name__ == "__main__":
    main()
