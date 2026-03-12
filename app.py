"""
Customer Inquiry Manager
========================
Day 16 Update: Resolve functionality added to admin dashboard.

Routes:
    /                    → Customer inquiry submission form
    /submit              → Handles form POST and saves to database
    /admin               → Admin dashboard showing all inquiries
    /resolve/<id>        → Marks an inquiry as Resolved  ← NEW Day 16
"""

import logging
from flask import Flask, render_template_string, render_template, request, redirect, url_for
from database import (
    get_or_create_customer,
    insert_inquiry,
    insert_ai_category,
    get_all_inquiries,
    resolve_inquiry
)
from ai_service import categorize_inquiry
from notifications import send_urgent_notification

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

app = Flask(__name__)


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
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    logger.info("Home page visited")
    return render_template_string(HOME_TEMPLATE, submitted=False, error=False)


@app.route("/submit", methods=["POST"])
def submit():
    """
    Full pipeline:
    1. Validate form data
    2. Save customer to DB
    3. Save inquiry to DB
    4. AI categorizes message
    5. Save AI result to DB
    6. Send instant notification if Sales or Billing
    7. Show success to customer
    """
    name    = request.form.get("name",    "").strip()
    email   = request.form.get("email",   "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not message:
        logger.warning("Form submitted with missing fields")
        return redirect(url_for("home"))

    logger.info(f"New inquiry received from {email}")

    try:
        # Save customer
        customer_id = get_or_create_customer(name, email)
        logger.info(f"Customer saved/found — ID: {customer_id} | Email: {email}")

        # Save inquiry
        inquiry_id = insert_inquiry(customer_id, message)
        logger.info(f"Inquiry saved — ID: {inquiry_id} | Customer ID: {customer_id}")

        # AI categorization
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

        # Save AI result
        insert_ai_category(
            inquiry_id    = inquiry_id,
            category      = ai_result["category"],
            urgency_level = ai_result["urgency"],
            ai_summary    = ai_result["summary"]
        )
        logger.info(f"AI category saved — Inquiry: {inquiry_id} | Category: {ai_result['category']}")

        # Send urgent notification if Sales or Billing
        if ai_result["category"] in ("Sales", "Billing"):
            send_urgent_notification(
                name     = name,
                email    = email,
                message  = message,
                category = ai_result["category"],
                urgency  = ai_result["urgency"],
                summary  = ai_result["summary"]
            )
            logger.info(f"Urgent notification sent — Category: {ai_result['category']} | Customer: {email}")
        else:
            logger.info(f"No instant notification — Category: {ai_result['category']} (queued for daily summary)")

        return render_template_string(HOME_TEMPLATE, submitted=True, error=False)

    except Exception as e:
        logger.error(f"Form submission failed for {email}: {e}")
        return render_template_string(HOME_TEMPLATE, submitted=False, error=True)


@app.route("/admin")
def admin():
    """
    Admin dashboard — shows all inquiries with AI categories.

    Supports category filtering via URL query parameter:
        /admin                  → shows all inquiries
        /admin?category=Sales   → shows only Sales
        /admin?category=Billing → shows only Billing
        etc.
    """
    category_filter = request.args.get("category", "")
    all_inquiries   = get_all_inquiries()

    if category_filter:
        inquiries = [i for i in all_inquiries if i.get("category") == category_filter]
    else:
        inquiries = all_inquiries

    logger.info(
        f"Admin dashboard visited — "
        f"{len(inquiries)} inquiries shown | "
        f"Filter: {category_filter or 'All'}"
    )

    return render_template(
        "admin.html",
        inquiries     = inquiries,
        active_filter = category_filter
    )


@app.route("/resolve/<int:inquiry_id>")
def resolve(inquiry_id):
    """
    Marks an inquiry as Resolved and redirects back to the dashboard.
    Preserves the active category filter if one was set.

    Args:
        inquiry_id (int): ID of the inquiry to resolve (from URL)
    """
    resolve_inquiry(inquiry_id)
    logger.info(f"Inquiry {inquiry_id} marked as Resolved")

    # Preserve active filter when redirecting back
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