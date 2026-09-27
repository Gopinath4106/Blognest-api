"""
Database layer for AI Blog Nest.

Uses plain sqlite3 (no ORM) so the project stays easy to read and explain
in a college viva. Provides:
  - get_db()      : returns a request-scoped sqlite3 connection
  - init_db()     : creates all tables if they do not exist
  - close_db()    : closes the connection at the end of each request
"""

import sqlite3
from flask import g, current_app


def get_db():
    """Return a SQLite connection stored on Flask's application context `g`."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
        # Enforce foreign key constraints (off by default in SQLite)
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'user',   -- 'user' or 'admin'
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS blogs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    category    TEXT NOT NULL DEFAULT 'General',
    tags        TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'draft',    -- 'draft' or 'published'
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    blog_id    INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    comment    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (blog_id) REFERENCES blogs (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS likes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    blog_id    INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (blog_id) REFERENCES blogs (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE (blog_id, user_id)   -- prevents duplicate likes at the DB level
);

CREATE INDEX IF NOT EXISTS idx_blogs_user ON blogs(user_id);
CREATE INDEX IF NOT EXISTS idx_blogs_status ON blogs(status);
CREATE INDEX IF NOT EXISTS idx_comments_blog ON comments(blog_id);
CREATE INDEX IF NOT EXISTS idx_likes_blog ON likes(blog_id);
"""


def init_db(app):
    """Create all tables (if they don't already exist). Safe to call every startup."""
    import os
    os.makedirs(os.path.dirname(app.config["DATABASE_PATH"]), exist_ok=True)

    conn = sqlite3.connect(app.config["DATABASE_PATH"])
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def register_db(app):
    """Wire up database teardown handling for the Flask app."""
    app.teardown_appcontext(close_db)
