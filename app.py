"""
Customer Inquiry Manager
========================
Day 22 Update: Security hardening.

Changes:
    - SECRET_KEY added to Flask config (loaded from env)
    - /admin route protected by login page
    - /login and /logout routes added
    - Flask sessions used to track admin authentication
    - No hardcoded secrets anywhere

Routes:
    /                    → Customer inquiry form
    /submit              → Handles form POST
    /admin               → Admin dashboard (login required)
    /login               → Admin login page
    /logout              → Clears session, redirects to login
    /resolve/<id>        → Mark inquiry as resolved (login required)
"""

import os
import logging
from flask import (
    Flask, render_template_string, render_template,
    request, redirect, url_for, session
)
from database import (
    get_or_create_customer,
    insert_inquiry,
    insert_ai_category,
    get_all_inquiries,
    resolve_inquiry
)
from ai_service import categorize_inquiry
from notifications import send_urgent_notification
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s [%(levelname)s] %(message)s",
    handlers = [
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flask App
# ---------------------------------------------------------------------------

app = Flask(__name__)

# SECRET_KEY is required for Flask sessions to work securely
# Never hardcode this — always load from environment variable
app.secret_key = os.getenv("SECRET_KEY")

# Admin credentials — loaded from environment, never hardcoded
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


# ---------------------------------------------------------------------------
# Login Required Decorator
# ---------------------------------------------------------------------------

def login_required(f):
    """
    Decorator that protects routes from unauthenticated access.
    Redirects to /login if the user is not logged in.
    Usage: add @login_required below any route decorator.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            logger.warning(f"Unauthenticated access attempt to {request.path}")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ---------------------------------------------------------------------------
# HTML Template — Customer Form
# ---------------------------------------------------------------------------

HOME_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Customer Inquiry Manager</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'DM Sans', sans-serif;
            background-color: #0f1117;
            color: #e8e8e8;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }

        .card {
            background: #1a1d27;
            border: 1px solid #2a2d3a;
            border-radius: 16px;
            padding: 3rem 2.5rem;
            width: 100%;
            max-width: 560px;
            box-shadow: 0 24px 60px rgba(0,0,0,0.4);
        }

        .badge {
            display: inline-block;
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.3);
            padding: 0.3rem 0.85rem;
            border-radius: 100px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 1.2rem;
        }

        h1 {
            font-family: 'DM Serif Display', serif;
            font-size: 2rem;
            line-height: 1.2;
            color: #ffffff;
            margin-bottom: 0.6rem;
        }

        .subtitle {
            color: #6b7280;
            font-size: 0.95rem;
            margin-bottom: 2.2rem;
            line-height: 1.6;
        }

        .form-group { margin-bottom: 1.25rem; }

        label {
            display: block;
            font-size: 0.82rem;
            font-weight: 600;
            color: #9ca3af;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }

        input[type="text"],
        input[type="email"],
        textarea {
            width: 100%;
            background: #0f1117;
            border: 1px solid #2a2d3a;
            border-radius: 8px;
            color: #e8e8e8;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.95rem;
            padding: 0.75rem 1rem;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        input[type="text"]:focus,
        input[type="email"]:focus,
        textarea:focus {
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
        }

        textarea { resize: vertical; min-height: 130px; line-height: 1.6; }

        .btn {
            width: 100%;
            background: #6366f1;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.95rem;
            font-weight: 600;
            padding: 0.85rem 1rem;
            cursor: pointer;
            transition: background 0.2s, transform 0.1s;
            margin-top: 0.5rem;
        }

        .btn:hover  { background: #4f46e5; }
        .btn:active { transform: scale(0.99); }

        .flash {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            color: #4ade80;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
        }

        .error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #f87171;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
        }

        .footer-note {
            text-align: center;
            color: #374151;
            font-size: 0.8rem;
            margin-top: 1.5rem;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="badge">Customer Support</div>
        <h1>How can we help you?</h1>
        <p class="subtitle">
            Fill out the form below and we'll get back to you as soon as possible.
        </p>

        {% if submitted %}
        <div class="flash">
            ✅ Your inquiry has been received. We'll be in touch shortly.
        </div>
        {% endif %}

        {% if error %}
        <div class="error">
            ❌ Something went wrong. Please try again.
        </div>
        {% endif %}

        <form method="POST" action="/submit">
            <div class="form-group">
                <label for="name">Full Name</label>
                <input type="text" id="name" name="name"
                       placeholder="Jane Smith" required>
            </div>
            <div class="form-group">
                <label for="email">Email Address</label>
                <input type="email" id="email" name="email"
                       placeholder="jane@company.com" required>
            </div>
            <div class="form-group">
                <label for="message">Your Message</label>
                <textarea id="message" name="message"
                          placeholder="Describe your inquiry in detail..."
                          required></textarea>
            </div>
            <button type="submit" class="btn">Send Inquiry →</button>
        </form>

        <p class="footer-note">Your message is handled securely and privately.</p>
    </div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# HTML Template — Admin Login Page
# ---------------------------------------------------------------------------

LOGIN_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login — Customer Inquiry Manager</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'DM Sans', sans-serif;
            background-color: #0f1117;
            color: #e8e8e8;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }

        .card {
            background: #1a1d27;
            border: 1px solid #2a2d3a;
            border-radius: 16px;
            padding: 2.5rem;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 24px 60px rgba(0,0,0,0.4);
        }

        .lock-icon {
            font-size: 2rem;
            margin-bottom: 1rem;
            display: block;
            text-align: center;
        }

        h1 {
            font-family: 'DM Serif Display', serif;
            font-size: 1.6rem;
            color: #ffffff;
            text-align: center;
            margin-bottom: 0.4rem;
        }

        .subtitle {
            color: #6b7280;
            font-size: 0.88rem;
            text-align: center;
            margin-bottom: 2rem;
        }

        .form-group { margin-bottom: 1.2rem; }

        label {
            display: block;
            font-size: 0.82rem;
            font-weight: 600;
            color: #9ca3af;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }

        input[type="text"],
        input[type="password"] {
            width: 100%;
            background: #0f1117;
            border: 1px solid #2a2d3a;
            border-radius: 8px;
            color: #e8e8e8;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.95rem;
            padding: 0.75rem 1rem;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        input:focus {
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
        }

        .btn {
            width: 100%;
            background: #6366f1;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.95rem;
            font-weight: 600;
            padding: 0.85rem 1rem;
            cursor: pointer;
            transition: background 0.2s;
            margin-top: 0.5rem;
        }

        .btn:hover { background: #4f46e5; }

        .error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #f87171;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            font-size: 0.88rem;
            margin-bottom: 1.2rem;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="card">
        <span class="lock-icon">🔐</span>
        <h1>Admin Login</h1>
        <p class="subtitle">Customer Inquiry Manager</p>

        {% if error %}
        <div class="error">❌ {{ error }}</div>
        {% endif %}

        <form method="POST" action="/login">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username"
                       placeholder="admin" required autofocus>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password"
                       placeholder="••••••••" required>
            </div>
            <button type="submit" class="btn">Sign In →</button>
        </form>
    </div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Routes — Public
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    logger.info("Home page visited")
    return render_template_string(HOME_TEMPLATE, submitted=False, error=False)


@app.route("/submit", methods=["POST"])
def submit():
    name    = request.form.get("name",    "").strip()
    email   = request.form.get("email",   "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not message:
        logger.warning("Form submitted with missing fields")
        return redirect(url_for("home"))

    logger.info(f"New inquiry received from {email}")

    try:
        customer_id = get_or_create_customer(name, email)
        logger.info(f"Customer saved/found — ID: {customer_id} | Email: {email}")

        inquiry_id = insert_inquiry(customer_id, message)
        logger.info(f"Inquiry saved — ID: {inquiry_id} | Customer ID: {customer_id}")

        try:
            ai_result = categorize_inquiry(message)
            logger.info(
                f"AI categorized — Inquiry: {inquiry_id} | "
                f"Category: {ai_result['category']} | "
                f"Urgency: {ai_result['urgency']}"
            )
        except Exception as ai_error:
            logger.error(f"AI categorization failed for Inquiry {inquiry_id}: {ai_error}")
            ai_result = {
                "category": "General",
                "urgency":  "Low",
                "summary":  "AI categorization failed — please review manually."
            }

        insert_ai_category(
            inquiry_id    = inquiry_id,
            category      = ai_result["category"],
            urgency_level = ai_result["urgency"],
            ai_summary    = ai_result["summary"]
        )
        logger.info(f"AI category saved — Inquiry: {inquiry_id}")

        if ai_result["category"] in ("Sales", "Billing"):
            send_urgent_notification(
                name     = name,
                email    = email,
                message  = message,
                category = ai_result["category"],
                urgency  = ai_result["urgency"],
                summary  = ai_result["summary"]
            )
            logger.info(f"Urgent notification sent — Category: {ai_result['category']}")
        else:
            logger.info(f"No instant notification — Category: {ai_result['category']}")

        return render_template_string(HOME_TEMPLATE, submitted=True, error=False)

    except Exception as e:
        logger.error(f"Form submission failed for {email}: {e}")
        return render_template_string(HOME_TEMPLATE, submitted=False, error=True)


# ---------------------------------------------------------------------------
# Routes — Auth
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            session["admin_username"]  = username
            logger.info(f"Admin login successful — user: {username}")
            return redirect(url_for("admin"))
        else:
            logger.warning(f"Failed login attempt — username: {username}")
            return render_template_string(
                LOGIN_TEMPLATE,
                error="Incorrect username or password."
            )

    # GET request — show login form
    # If already logged in redirect straight to dashboard
    if session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    return render_template_string(LOGIN_TEMPLATE, error=None)


@app.route("/logout")
def logout():
    username = session.get("admin_username", "unknown")
    session.clear()
    logger.info(f"Admin logged out — user: {username}")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Routes — Admin (login required)
# ---------------------------------------------------------------------------

@app.route("/admin")
@login_required
def admin():
    category_filter = request.args.get("category", "")
    all_inquiries   = get_all_inquiries()

    if category_filter:
        inquiries = [i for i in all_inquiries if i.get("category") == category_filter]
    else:
        inquiries = all_inquiries

    logger.info(
        f"Admin dashboard visited by {session.get('admin_username')} — "
        f"{len(inquiries)} inquiries | Filter: {category_filter or 'All'}"
    )

    return render_template(
        "admin.html",
        inquiries     = inquiries,
        active_filter = category_filter
    )


@app.route("/resolve/<int:inquiry_id>")
@login_required
def resolve(inquiry_id):
    resolve_inquiry(inquiry_id)
    logger.info(
        f"Inquiry {inquiry_id} resolved by {session.get('admin_username')}"
    )
    category = request.args.get("category", "")
    if category:
        return redirect(url_for("admin", category=category))
    return redirect(url_for("admin"))


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Customer Inquiry Manager starting...")
    app.run(debug=True, host="0.0.0.0", port=5001)