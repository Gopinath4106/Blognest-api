"""
AI Blog Nest - main Flask application.

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

import os
import re
import functools
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, g, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from database import get_db, init_db, register_db
import ai_generator

CATEGORIES = [
    "Technology", "Artificial Intelligence", "Cyber Security",
    "Education", "Programming", "Lifestyle", "Travel", "General",
]

TONES = ["Professional", "Casual", "Friendly", "Formal", "Enthusiastic"]
LENGTHS = ["Short", "Medium", "Long"]


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    register_db(app)
    with app.app_context():
        init_db(app)

    register_routes(app)
    register_error_handlers(app)
    register_template_helpers(app)

    return app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        if g.user["role"] != "admin":
            flash("You do not have permission to access that page.", "error")
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapped


def is_valid_email(email):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or "") is not None


def blog_to_dict(row, db):
    """Attach author name, like count, and comment count to a blog row."""
    d = dict(row)
    author = db.execute("SELECT name FROM users WHERE id = ?", (d["user_id"],)).fetchone()
    d["author_name"] = author["name"] if author else "Unknown"
    like_count = db.execute(
        "SELECT COUNT(*) AS c FROM likes WHERE blog_id = ?", (d["id"],)
    ).fetchone()["c"]
    comment_count = db.execute(
        "SELECT COUNT(*) AS c FROM comments WHERE blog_id = ?", (d["id"],)
    ).fetchone()["c"]
    d["like_count"] = like_count
    d["comment_count"] = comment_count
    return d


def register_template_helpers(app):
    @app.template_filter("excerpt")
    def excerpt_filter(html, length=160):
        text = re.sub(r"<[^>]+>", " ", html or "")
        text = re.sub(r"\s+", " ", text).strip()
        return (text[:length] + "...") if len(text) > length else text

    @app.template_filter("dateformat")
    def dateformat_filter(value, fmt="%d %b %Y"):
        if not value:
            return ""
        try:
            dt = datetime.strptime(value.split(".")[0], "%Y-%m-%d %H:%M:%S")
            return dt.strftime(fmt)
        except Exception:
            return value

    @app.context_processor
    def inject_globals():
        return {
            "categories": CATEGORIES,
            "current_user": g.get("user"),
            "ai_enabled": Config.AI_ENABLED,
        }


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
def register_routes(app):

    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        g.user = None
        if user_id is not None:
            db = get_db()
            g.user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    # --------------------------- Home -------------------------------------
    @app.route("/")
    def index():
        db = get_db()
        q = request.args.get("q", "").strip()
        category = request.args.get("category", "").strip()

        query = "SELECT * FROM blogs WHERE status = 'published'"
        params = []
        if q:
            query += " AND (title LIKE ? OR content LIKE ? OR category LIKE ? OR tags LIKE ?)"
            like = f"%{q}%"
            params += [like, like, like, like]
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY created_at DESC LIMIT 12"

        rows = db.execute(query, params).fetchall()
        blogs = [blog_to_dict(r, db) for r in rows]
        return render_template("index.html", blogs=blogs, q=q, selected_category=category)

    # --------------------------- Search -------------------------------------
    @app.route("/search")
    def search():
        db = get_db()
        q = request.args.get("q", "").strip()
        category = request.args.get("category", "").strip()

        query = "SELECT * FROM blogs WHERE status = 'published'"
        params = []
        if q:
            query += " AND (title LIKE ? OR content LIKE ? OR category LIKE ? OR tags LIKE ?)"
            like = f"%{q}%"
            params += [like, like, like, like]
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY created_at DESC"

        rows = db.execute(query, params).fetchall()
        blogs = [blog_to_dict(r, db) for r in rows]
        return render_template("search.html", blogs=blogs, q=q, selected_category=category)

    # --------------------------- Register -----------------------------------
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if g.user:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")

            errors = []
            if not name:
                errors.append("Name is required.")
            if not is_valid_email(email):
                errors.append("A valid email address is required.")
            if len(password) < 6:
                errors.append("Password must be at least 6 characters long.")
            if password != confirm:
                errors.append("Passwords do not match.")

            db = get_db()
            if not errors and db.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone():
                errors.append("An account with that email already exists.")

            if errors:
                for e in errors:
                    flash(e, "error")
                return render_template("register.html", name=name, email=email)

            password_hash = generate_password_hash(password)
            db.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'user')",
                (name, email, password_hash),
            )
            db.commit()
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    # --------------------------- Login / Logout ------------------------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.user:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            db = get_db()
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

            if user is None or not check_password_hash(user["password_hash"], password):
                flash("Invalid email or password.", "error")
                return render_template("login.html", email=email)

            session.clear()
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user['name']}!", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard"))

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("index"))

    # --------------------------- Dashboard ------------------------------------
    @app.route("/dashboard")
    @login_required
    def dashboard():
        db = get_db()
        rows = db.execute(
            "SELECT * FROM blogs WHERE user_id = ? ORDER BY created_at DESC", (g.user["id"],)
        ).fetchall()
        blogs = [blog_to_dict(r, db) for r in rows]
        total = len(blogs)
        published = len([b for b in blogs if b["status"] == "published"])
        drafts = total - published
        recent = blogs[:5]
        return render_template(
            "dashboard.html", total=total, published=published, drafts=drafts, recent=recent
        )

    # --------------------------- AI Generator ---------------------------------
    @app.route("/generate", methods=["GET", "POST"])
    @login_required
    def generate():
        if request.method == "POST":
            topic = request.form.get("topic", "").strip()
            category = request.form.get("category", "General")
            tone = request.form.get("tone", "Professional")
            length = request.form.get("length", "Medium")

            if not topic:
                flash("Please enter a blog topic.", "error")
                return render_template(
                    "ai_generator.html", categories=CATEGORIES, tones=TONES, lengths=LENGTHS
                )

            generated = ai_generator.generate_blog(topic, category, tone, length)
            full_html = ai_generator.assemble_full_content(generated)

            return render_template(
                "ai_generator.html",
                categories=CATEGORIES, tones=TONES, lengths=LENGTHS,
                generated=generated, full_html=full_html,
                topic=topic, category=category, tone=tone, length=length,
            )

        return render_template("ai_generator.html", categories=CATEGORIES, tones=TONES, lengths=LENGTHS)

    # --------------------------- Create Blog (also receives AI draft) --------
    @app.route("/blog/new", methods=["GET", "POST"])
    @login_required
    def create_blog():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            content = request.form.get("content", "").strip()
            category = request.form.get("category", "General")
            tags = request.form.get("tags", "").strip()
            action = request.form.get("action", "draft")  # 'draft' or 'publish'

            if not title or not content:
                flash("Title and content are required.", "error")
                return render_template(
                    "create_blog.html", categories=CATEGORIES,
                    title=title, content=content, category=category, tags=tags
                )

            status = "published" if action == "publish" else "draft"
            db = get_db()
            db.execute(
                """INSERT INTO blogs (user_id, title, content, category, tags, status)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (g.user["id"], title, content, category, tags, status),
            )
            db.commit()
            flash(
                "Blog published successfully!" if status == "published" else "Draft saved.",
                "success",
            )
            return redirect(url_for("my_blogs"))

        # Pre-fill from AI generator if provided via query string handoff
        prefill = {
            "title": request.args.get("title", ""),
            "content": request.args.get("content", ""),
            "category": request.args.get("category", "General"),
            "tags": request.args.get("tags", ""),
        }
        return render_template("create_blog.html", categories=CATEGORIES, **prefill)

    # --------------------------- Edit Blog -------------------------------------
    @app.route("/blog/<int:blog_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_blog(blog_id):
        db = get_db()
        blog = db.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,)).fetchone()
        if blog is None:
            abort(404)
        if blog["user_id"] != g.user["id"] and g.user["role"] != "admin":
            abort(403)

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            content = request.form.get("content", "").strip()
            category = request.form.get("category", "General")
            tags = request.form.get("tags", "").strip()
            action = request.form.get("action", "draft")

            if not title or not content:
                flash("Title and content are required.", "error")
                return render_template("edit_blog.html", blog=blog, categories=CATEGORIES)

            status = "published" if action == "publish" else ("draft" if action == "draft_save" else blog["status"])
            db.execute(
                """UPDATE blogs SET title = ?, content = ?, category = ?, tags = ?,
                   status = ?, updated_at = datetime('now') WHERE id = ?""",
                (title, content, category, tags, status, blog_id),
            )
            db.commit()
            flash("Blog updated successfully.", "success")
            return redirect(url_for("my_blogs"))

        return render_template("edit_blog.html", blog=blog, categories=CATEGORIES)

    # --------------------------- Delete Blog -------------------------------------
    @app.route("/blog/<int:blog_id>/delete", methods=["POST"])
    @login_required
    def delete_blog(blog_id):
        db = get_db()
        blog = db.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,)).fetchone()
        if blog is None:
            abort(404)
        if blog["user_id"] != g.user["id"] and g.user["role"] != "admin":
            abort(403)

        db.execute("DELETE FROM blogs WHERE id = ?", (blog_id,))
        db.commit()
        flash("Blog deleted.", "success")
        return redirect(request.referrer or url_for("my_blogs"))

    # --------------------------- Publish toggle -----------------------------
    @app.route("/blog/<int:blog_id>/publish", methods=["POST"])
    @login_required
    def publish_blog(blog_id):
        db = get_db()
        blog = db.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,)).fetchone()
        if blog is None:
            abort(404)
        if blog["user_id"] != g.user["id"] and g.user["role"] != "admin":
            abort(403)
        db.execute(
            "UPDATE blogs SET status = 'published', updated_at = datetime('now') WHERE id = ?",
            (blog_id,),
        )
        db.commit()
        flash("Blog published.", "success")
        return redirect(url_for("my_blogs"))

    # --------------------------- My Blogs -------------------------------------
    @app.route("/my-blogs")
    @login_required
    def my_blogs():
        db = get_db()
        rows = db.execute(
            "SELECT * FROM blogs WHERE user_id = ? ORDER BY created_at DESC", (g.user["id"],)
        ).fetchall()
        blogs = [blog_to_dict(r, db) for r in rows]
        return render_template("my_blogs.html", blogs=blogs)

    # --------------------------- Blog Detail -----------------------------------
    @app.route("/blog/<int:blog_id>")
    def view_blog(blog_id):
        db = get_db()
        row = db.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,)).fetchone()
        if row is None:
            abort(404)

        is_owner = g.user is not None and g.user["id"] == row["user_id"]
        is_admin = g.user is not None and g.user["role"] == "admin"
        if row["status"] != "published" and not (is_owner or is_admin):
            abort(404)

        blog = blog_to_dict(row, db)
        comments_rows = db.execute(
            """SELECT comments.*, users.name AS author_name
               FROM comments JOIN users ON comments.user_id = users.id
               WHERE blog_id = ? ORDER BY comments.created_at DESC""",
            (blog_id,),
        ).fetchall()

        user_has_liked = False
        if g.user:
            liked = db.execute(
                "SELECT id FROM likes WHERE blog_id = ? AND user_id = ?",
                (blog_id, g.user["id"]),
            ).fetchone()
            user_has_liked = liked is not None

        tag_list = [t.strip() for t in (blog["tags"] or "").split(",") if t.strip()]

        return render_template(
            "blog.html", blog=blog, comments=comments_rows,
            user_has_liked=user_has_liked, tag_list=tag_list,
            is_owner=is_owner, is_admin=is_admin,
        )

    # --------------------------- Like / Unlike -----------------------------
    @app.route("/blog/<int:blog_id>/like", methods=["POST"])
    @login_required
    def like_blog(blog_id):
        db = get_db()
        blog = db.execute("SELECT id FROM blogs WHERE id = ?", (blog_id,)).fetchone()
        if blog is None:
            abort(404)

        existing = db.execute(
            "SELECT id FROM likes WHERE blog_id = ? AND user_id = ?",
            (blog_id, g.user["id"]),
        ).fetchone()

        if existing:
            db.execute("DELETE FROM likes WHERE id = ?", (existing["id"],))
        else:
            # INSERT OR IGNORE + the UNIQUE(blog_id, user_id) constraint
            # guarantees no duplicate likes even under a race condition.
            db.execute(
                "INSERT OR IGNORE INTO likes (blog_id, user_id) VALUES (?, ?)",
                (blog_id, g.user["id"]),
            )
        db.commit()
        return redirect(url_for("view_blog", blog_id=blog_id))

    # --------------------------- Comments -----------------------------------
    @app.route("/blog/<int:blog_id>/comment", methods=["POST"])
    @login_required
    def add_comment(blog_id):
        db = get_db()
        blog = db.execute("SELECT id FROM blogs WHERE id = ?", (blog_id,)).fetchone()
        if blog is None:
            abort(404)

        text = request.form.get("comment", "").strip()
        if not text:
            flash("Comment cannot be empty.", "error")
        else:
            db.execute(
                "INSERT INTO comments (blog_id, user_id, comment) VALUES (?, ?, ?)",
                (blog_id, g.user["id"], text),
            )
            db.commit()
            flash("Comment added.", "success")
        return redirect(url_for("view_blog", blog_id=blog_id))

    @app.route("/comment/<int:comment_id>/delete", methods=["POST"])
    @login_required
    def delete_comment(comment_id):
        db = get_db()
        comment = db.execute("SELECT * FROM comments WHERE id = ?", (comment_id,)).fetchone()
        if comment is None:
            abort(404)

        blog = db.execute("SELECT * FROM blogs WHERE id = ?", (comment["blog_id"],)).fetchone()
        can_delete = (
            g.user["role"] == "admin"
            or comment["user_id"] == g.user["id"]
            or (blog and blog["user_id"] == g.user["id"])
        )
        if not can_delete:
            abort(403)

        db.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        db.commit()
        flash("Comment deleted.", "success")
        return redirect(url_for("view_blog", blog_id=comment["blog_id"]))

    # --------------------------- Admin -----------------------------------------
    @app.route("/admin")
    @admin_required
    def admin_dashboard():
        db = get_db()
        stats = {
            "total_users": db.execute("SELECT COUNT(*) c FROM users").fetchone()["c"],
            "total_blogs": db.execute("SELECT COUNT(*) c FROM blogs").fetchone()["c"],
            "published_blogs": db.execute(
                "SELECT COUNT(*) c FROM blogs WHERE status='published'"
            ).fetchone()["c"],
            "total_comments": db.execute("SELECT COUNT(*) c FROM comments").fetchone()["c"],
            "total_likes": db.execute("SELECT COUNT(*) c FROM likes").fetchone()["c"],
        }
        users = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        blog_rows = db.execute("SELECT * FROM blogs ORDER BY created_at DESC").fetchall()
        blogs = [blog_to_dict(r, db) for r in blog_rows]
        return render_template("admin.html", stats=stats, users=users, blogs=blogs)

    @app.route("/admin/blog/<int:blog_id>/delete", methods=["POST"])
    @admin_required
    def admin_delete_blog(blog_id):
        db = get_db()
        db.execute("DELETE FROM blogs WHERE id = ?", (blog_id,))
        db.commit()
        flash("Blog removed by admin.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
    @admin_required
    def admin_delete_user(user_id):
        if user_id == g.user["id"]:
            flash("You cannot delete your own admin account.", "error")
            return redirect(url_for("admin_dashboard"))
        db = get_db()
        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()
        flash("User removed by admin.", "success")
        return redirect(url_for("admin_dashboard"))


app = create_app()

if __name__ == "__main__":
    # Debug mode is convenient for a college project / viva demo.
    # Turn this off (debug=False) before any real deployment.
    app.run(host="127.0.0.1", port=5000, debug=True)
