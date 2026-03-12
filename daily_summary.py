"""
daily_summary.py
================
Day 17: Daily summary email sent every morning at 8am.

Queries all unresolved inquiries from the last 24 hours,
groups them by category, and sends a formatted summary
email to the business owner via SendGrid.

Run manually:
    python daily_summary.py

Run automatically via cron (set up on VM):
    0 8 * * * /home/azureuser/customer-inquiry-manager/.venv/bin/python \
              /home/azureuser/customer-inquiry-manager/daily_summary.py
"""

import os
import logging
from datetime import datetime, timedelta
from database import get_connection
from notifications import send_email
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Logging — writes to same app.log as the main app
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
# Query — Unresolved Inquiries from Last 24 Hours
# ---------------------------------------------------------------------------

def get_recent_unresolved():
    """
    Fetches all unresolved inquiries created in the last 24 hours.
    Joins with Customers and AICategories for full details.

    Returns:
        list of dicts with keys:
            inquiry_id, customer_name, customer_email,
            message, category, urgency, summary, received_at
    """
    conn   = get_connection()
    cursor = conn.cursor()

    since = datetime.utcnow() - timedelta(hours=24)

    cursor.execute("""
        SELECT
            i.id            AS inquiry_id,
            c.name          AS customer_name,
            c.email         AS customer_email,
            i.message       AS message,
            i.status        AS status,
            i.created_at    AS received_at,
            a.category      AS category,
            a.urgency_level AS urgency,
            a.ai_summary    AS summary
        FROM Inquiries i
        JOIN Customers     c ON i.customer_id = c.id
        LEFT JOIN AICategories a ON a.inquiry_id = i.id
        WHERE i.status != 'Resolved'
          AND i.created_at >= ?
        ORDER BY
            CASE a.urgency_level
                WHEN 'Very Urgent' THEN 1
                WHEN 'Urgent'      THEN 2
                WHEN 'Medium'      THEN 3
                WHEN 'Low'         THEN 4
                ELSE 5
            END,
            i.created_at DESC
    """, (since,))

    columns = [col[0] for col in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    conn.close()
    return results


# ---------------------------------------------------------------------------
# Group Inquiries by Category
# ---------------------------------------------------------------------------

def group_by_category(inquiries):
    """
    Groups a list of inquiry dicts by their category.

    Returns:
        dict with keys Sales, Billing, Support, General
        each containing a list of inquiries in that category
    """
    groups = {
        "Sales":   [],
        "Billing": [],
        "Support": [],
        "General": []
    }

    for inq in inquiries:
        cat = inq.get("category") or "General"
        if cat in groups:
            groups[cat].append(inq)
        else:
            groups["General"].append(inq)

    return groups


# ---------------------------------------------------------------------------
# Build Email HTML
# ---------------------------------------------------------------------------

def build_summary_email(inquiries, groups, date_str):
    """
    Builds the HTML body for the daily summary email.

    Args:
        inquiries (list): All unresolved inquiries from last 24h
        groups    (dict): Inquiries grouped by category
        date_str  (str):  Formatted date string for the subject/header

    Returns:
        tuple: (subject str, html body str)
    """

    total   = len(inquiries)
    subject = f"📊 Daily Inquiry Summary — {date_str} ({total} open)"

    if total == 0:
        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px;
                    margin: 0 auto; padding: 20px;">
            <h2 style="color: #6366f1;">Daily Inquiry Summary</h2>
            <p style="color: #6b7280;">{date_str}</p>
            <div style="background: #f0fdf4; border: 1px solid #bbf7d0;
                        border-radius: 8px; padding: 20px; margin-top: 20px;
                        text-align: center;">
                <p style="color: #15803d; font-size: 1.1rem;">
                    ✅ No open inquiries from the last 24 hours.
                    All clear!
                </p>
            </div>
        </div>
        """
        return subject, body

    # ---- Category config ----
    category_config = {
        "Sales":   {"emoji": "🔴", "color": "#dc2626", "light": "#fef2f2"},
        "Billing": {"emoji": "🟠", "color": "#ea580c", "light": "#fff7ed"},
        "Support": {"emoji": "🟡", "color": "#ca8a04", "light": "#fefce8"},
        "General": {"emoji": "⚪", "color": "#6b7280", "light": "#f9fafb"},
    }

    # ---- Stats row ----
    stats_html = ""
    for cat, cfg in category_config.items():
        count = len(groups.get(cat, []))
        stats_html += f"""
        <td style="text-align: center; padding: 12px;">
            <div style="font-size: 1.6rem; font-weight: 700;
                        color: {cfg['color']};">{count}</div>
            <div style="font-size: 0.75rem; color: #6b7280;
                        text-transform: uppercase; letter-spacing: 0.05em;">
                {cfg['emoji']} {cat}
            </div>
        </td>
        """

    # ---- Inquiry rows per category ----
    categories_html = ""
    for cat, cfg in category_config.items():
        cat_inquiries = groups.get(cat, [])
        if not cat_inquiries:
            continue

        rows_html = ""
        for inq in cat_inquiries:
            received = inq["received_at"]
            if hasattr(received, "strftime"):
                time_str = received.strftime("%b %d %H:%M")
            else:
                time_str = str(received)[:16]

            rows_html += f"""
            <tr style="border-bottom: 1px solid #e5e7eb;">
                <td style="padding: 10px 12px; font-weight: 600;
                           color: #111827; font-size: 0.88rem;">
                    {inq['customer_name']}
                    <div style="font-size: 0.75rem; color: #9ca3af;
                                font-weight: 400;">
                        {inq['customer_email']}
                    </div>
                </td>
                <td style="padding: 10px 12px; color: #4b5563;
                           font-size: 0.83rem; max-width: 240px;">
                    {inq['message'][:80]}{'...' if len(inq['message']) > 80 else ''}
                    <div style="font-size: 0.75rem; color: #9ca3af;
                                font-style: italic; margin-top: 2px;">
                        {inq.get('summary') or ''}
                    </div>
                </td>
                <td style="padding: 10px 12px; font-size: 0.78rem;
                           color: #6b7280; white-space: nowrap;">
                    {inq.get('urgency') or '—'}
                    <div style="color: #9ca3af;">{time_str}</div>
                </td>
            </tr>
            """

        categories_html += f"""
        <div style="margin-bottom: 24px;">
            <h3 style="font-size: 0.9rem; font-weight: 700; color: {cfg['color']};
                       text-transform: uppercase; letter-spacing: 0.06em;
                       margin-bottom: 8px; padding: 8px 12px;
                       background: {cfg['light']}; border-radius: 6px;
                       border-left: 4px solid {cfg['color']};">
                {cfg['emoji']} {cat} — {len(cat_inquiries)} inquiry{'s' if len(cat_inquiries) != 1 else ''}
            </h3>
            <table style="width: 100%; border-collapse: collapse;
                          border: 1px solid #e5e7eb; border-radius: 8px;
                          overflow: hidden;">
                <thead>
                    <tr style="background: #f9fafb;">
                        <th style="padding: 8px 12px; text-align: left;
                                   font-size: 0.72rem; color: #6b7280;
                                   text-transform: uppercase; letter-spacing: 0.05em;
                                   border-bottom: 1px solid #e5e7eb;">
                            Customer
                        </th>
                        <th style="padding: 8px 12px; text-align: left;
                                   font-size: 0.72rem; color: #6b7280;
                                   text-transform: uppercase; letter-spacing: 0.05em;
                                   border-bottom: 1px solid #e5e7eb;">
                            Message
                        </th>
                        <th style="padding: 8px 12px; text-align: left;
                                   font-size: 0.72rem; color: #6b7280;
                                   text-transform: uppercase; letter-spacing: 0.05em;
                                   border-bottom: 1px solid #e5e7eb;">
                            Urgency
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """

    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 640px;
                margin: 0 auto; padding: 20px;">

        <!-- Header -->
        <div style="background: #6366f1; border-radius: 10px;
                    padding: 20px 24px; margin-bottom: 24px;">
            <h2 style="color: #ffffff; margin: 0; font-size: 1.2rem;">
                📊 Daily Inquiry Summary
            </h2>
            <p style="color: rgba(255,255,255,0.75); margin: 4px 0 0;
                      font-size: 0.88rem;">
                {date_str} — {total} unresolved {'inquiry' if total == 1 else 'inquiries'} from the last 24 hours
            </p>
        </div>

        <!-- Stats -->
        <table style="width: 100%; border-collapse: collapse;
                      background: #f9fafb; border: 1px solid #e5e7eb;
                      border-radius: 10px; overflow: hidden;
                      margin-bottom: 24px;">
            <tr>
                {stats_html}
            </tr>
        </table>

        <!-- Categories -->
        {categories_html}

        <!-- Footer -->
        <p style="font-size: 0.75rem; color: #9ca3af; text-align: center;
                  margin-top: 24px; border-top: 1px solid #e5e7eb;
                  padding-top: 16px;">
            Customer Inquiry Manager — Automated Daily Summary<br>
            Sent every morning at 8:00 AM
        </p>

    </div>
    """

    return subject, body


# ---------------------------------------------------------------------------
# Main — Send the Summary
# ---------------------------------------------------------------------------

def send_daily_summary():
    """
    Main function — queries the DB, builds the email, and sends it.
    This is what the cron job calls every morning at 8am.
    """
    date_str = datetime.now().strftime("%A, %B %d %Y")
    logger.info(f"Daily summary job started — {date_str}")

    try:
        # Query unresolved inquiries from last 24 hours
        inquiries = get_recent_unresolved()
        logger.info(f"Found {len(inquiries)} unresolved inquiries in last 24 hours")

        # Group by category
        groups = group_by_category(inquiries)

        # Build email
        subject, body = build_summary_email(inquiries, groups, date_str)

        # Send
        recipient = os.getenv("NOTIFICATION_EMAIL")
        success   = send_email(recipient, subject, body)

        if success:
            logger.info(f"Daily summary sent to {recipient} — {len(inquiries)} inquiries")
        else:
            logger.error("Daily summary failed to send")

    except Exception as e:
        logger.error(f"Daily summary job failed: {e}")


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    send_daily_summary()