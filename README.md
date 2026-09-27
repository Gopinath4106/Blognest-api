# 🪺 AI Blog Nest — AI-Powered Blog Generation and Management System

A web-based blogging platform built with **Flask** and **SQLite** that uses
Artificial Intelligence to help users draft blog posts. Users can register,
log in, enter a topic, generate a structured blog draft with AI, edit it,
and publish it for others to search, read, like, and comment on.

Built as a college project for a **B.Sc Computer Science (Cyber Security)**
program — kept deliberately simple and easy to explain in a viva.

---

## 1. Features

- **Home page** with hero section, latest blogs, search bar, and category browsing
- **User registration & login** with hashed passwords and session-based auth
- **User dashboard** with blog stats (total / published / drafts)
- **AI Blog Generator** — enter a topic, category, tone, and length; get a full
  structured draft (title, introduction, subheadings, conclusion, tags)
- **Demo / Offline AI Mode** — works completely **without any API key**, using a
  built-in local content generator, so the app never breaks
- **Full blog management** — create, edit, delete, publish, save as draft
- **Blog detail page** with author, category, date, tags, likes, and comments
- **Search** by title, content, category, or tags
- **8 categories**: Technology, Artificial Intelligence, Cyber Security,
  Education, Programming, Lifestyle, Travel, General
- **Like system** with duplicate-like prevention (enforced at the database level)
- **Comment system** — logged-in users can comment; owners/admins can delete
  inappropriate comments
- **My Blogs page** with edit/delete/view actions
- **Admin panel** — view users & blogs, delete inappropriate content, view stats
- Clean, responsive, modern UI (not a bare-bones Flask tutorial look)

---

## 2. Technology Used

| Layer     | Technology                         |
|-----------|-------------------------------------|
| Frontend  | HTML5, CSS3, vanilla JavaScript     |
| Backend   | Python 3, Flask                     |
| Database  | SQLite (via Python's `sqlite3`)     |
| AI        | OpenAI-compatible Chat Completions API (optional) + built-in offline Demo mode |
| Security  | Werkzeug password hashing, Flask sessions |

---

## 3. Project Structure

```
AI_Blog_Nest/
│
├── app.py                 # Main Flask application (routes, logic)
├── config.py               # Configuration (reads .env)
├── database.py             # SQLite connection + schema (init_db)
├── ai_generator.py         # AI generation logic + offline Demo mode
├── create_admin.py         # Script to create/promote an admin account
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── ai_generator.html
│   ├── create_blog.html
│   ├── edit_blog.html
│   ├── blog.html
│   ├── my_blogs.html
│   ├── search.html
│   ├── admin.html
│   └── errors/
│       ├── 404.html
│       ├── 403.html
│       └── 500.html
│
├── static/
│   ├── css/style.css
│   ├── js/script.js
│   └── images/
│
└── instance/
    └── blog_nest.db        # Created automatically on first run
```

---

## 4. System Requirements

- Python 3.9 or newer
- pip (comes with Python)
- Any modern browser (Chrome, Edge, Firefox)

---

## 5. Installation & Setup (Windows)

Open **Command Prompt** or **PowerShell** in the project folder and run:

```bat
:: 1. Create a virtual environment
python -m venv env

:: 2. Activate it
env\Scripts\activate

:: 3. Install dependencies
pip install -r requirements.txt

:: 4. Copy the example environment file
copy .env.example .env
```

### macOS / Linux (equivalent commands)

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

---

## 6. Environment (`.env`) Setup

Open the newly created `.env` file. You do **not** need to change anything to
run the project — it works out of the box in **Demo AI Mode**.

```env
SECRET_KEY=change-this-to-a-random-secret-key
OPENAI_API_KEY=
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
ADMIN_EMAIL=admin@blognest.com
ADMIN_PASSWORD=Admin@123
ADMIN_NAME=Site Administrator
```

- Leave `OPENAI_API_KEY` **empty** to use offline Demo AI Mode (default).
- To use a real AI API, paste a valid API key into `OPENAI_API_KEY`. The app
  automatically switches to live generation — and automatically falls back to
  Demo Mode if the API call ever fails, so the app never crashes.

---

## 7. Database Initialization

No manual step is needed — the database and all tables (`users`, `blogs`,
`comments`, `likes`) are created **automatically** the first time you run
`app.py` or `create_admin.py`. The SQLite file is created at
`instance/blog_nest.db`.

---

## 8. How to Run

```bat
python app.py
```

Then open your browser and go to:

```
http://127.0.0.1:5000
```

Register a normal account from the **Sign Up** page to start creating blogs.

---

## 9. How to Create an Admin Account

Run the helper script (with your virtual environment activated):

```bat
python create_admin.py
```

This creates an admin using the values in your `.env` file:

- **Email:** `admin@blognest.com`
- **Password:** `Admin@123`

You can also pass custom values directly:

```bat
python create_admin.py --email you@example.com --password YourPass123 --name "Your Name"
```

If a user with that email already exists, the script simply **promotes**
that account to admin instead of creating a duplicate.

Log in with the admin account and open the **Admin** link in the navbar to
access the admin panel.

> ⚠️ Change the default admin password before using this project outside a
> local/demo environment.

---

## 10. How to Use the AI Generator

1. Log in and click **Generate Blog** (navbar or dashboard).
2. Enter a **topic** (e.g. *"Cyber Security Awareness"*), pick a **category**,
   **tone**, and **length**.
3. Click **Generate Blog** — a structured draft appears on the right with a
   title, introduction, subheadings, conclusion, and tags.
4. Edit the title, tags, or content directly in the editable fields.
5. Click **Save as Draft** to keep working on it later, or **Publish Now** to
   make it live immediately.

---

## 11. Demo / Offline AI Mode

If `OPENAI_API_KEY` is not set in `.env` (the default), **AI Blog Nest still
works completely**. The `ai_generator.py` module detects the missing key and
automatically builds a well-structured blog post locally — with a title,
introduction, multiple subheadings based on the topic, a conclusion, and
relevant tags — without ever contacting an external service.

You'll see a **"Demo / Offline Mode"** badge in the footer and on the
generator page whenever this mode is active, so it's always clear which mode
is running (useful to point out during a project review or viva).

---

## 12. Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Activate your virtual environment and run `pip install -r requirements.txt` again. |
| Port 5000 already in use | Close the other program using port 5000, or edit the last line of `app.py` to use a different port, e.g. `app.run(port=5001)`. |
| Database errors / "table not found" | Delete `instance/blog_nest.db` and restart `python app.py` — it will be recreated automatically. |
| Can't log in as admin | Run `python create_admin.py` again — it's safe to re-run and will promote the existing account. |
| AI generation seems "generic" | That's expected in Demo Mode — it's intentionally offline. Add a real `OPENAI_API_KEY` in `.env` for live AI-generated content. |
| Changes to `.env` not taking effect | Restart the Flask server (`Ctrl+C` then `python app.py` again) — `.env` is only read on startup. |

---

## 13. Security Notes (for the Cyber Security project angle)

- Passwords are never stored in plain text — they're hashed with
  Werkzeug's `generate_password_hash` (PBKDF2-based).
- All database queries use **parameterized SQL** (`?` placeholders) to
  prevent SQL injection.
- Sessions are signed using Flask's `SECRET_KEY`.
- Login-required and admin-required decorators protect sensitive routes.
- Duplicate likes are prevented both in application logic and with a
  `UNIQUE(blog_id, user_id)` database constraint.
- API keys are never hard-coded — they're loaded from `.env`, which is
  excluded from version control via `.gitignore`.

---

## 14. License

This project was created for academic purposes as part of a college
curriculum. Feel free to reuse and adapt it for learning.
