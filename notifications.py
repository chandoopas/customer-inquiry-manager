"""
notifications.py
================
Day 12: Email notification system using SendGrid.

Handles all outgoing emails for the Customer Inquiry Manager:
    - Urgent alerts for Sales and Billing inquiries (Day 13)
    - Daily summary emails (Day 17)
    - AI follow-up emails (Day 19)

All email sending goes through the send_email() function in this file.
"""

import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Core Email Function
# ---------------------------------------------------------------------------

def send_email(to_email, subject, body):
    """
    Sends an email using SendGrid.

    Args:
        to_email (str): Recipient email address
        subject  (str): Email subject line
        body     (str): Email body — supports plain HTML

    Returns:
        bool: True if sent successfully, False if failed
    """
    try:
        message = Mail(
            from_email = os.getenv("SENDGRID_FROM_EMAIL"),
            to_emails  = to_email,
            subject    = subject,
            html_content = body
        )

        sg       = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)

        logger.info(f"Email sent to {to_email} | Subject: {subject} | Status: {response.status_code}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


# ---------------------------------------------------------------------------
# Test Runner
# Run directly to send yourself a test email:
#   python notifications.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    import logging
    logging.basicConfig(
        level  = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s"
    )

    # Read destination from env
    test_recipient = os.getenv("NOTIFICATION_EMAIL")

    print(f"\nSending test email to: {test_recipient}")
    print("Please wait...\n")

    success = send_email(
        to_email = test_recipient,
        subject  = "✅ Test Email — Customer Inquiry Manager",
        body     = """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">

            <h2 style="color: #6366f1;">Customer Inquiry Manager</h2>
            <p style="color: #374151;">
                This is a test email confirming that your SendGrid notification
                system is working correctly.
            </p>

            <div style="background: #f3f4f6; border-radius: 8px; padding: 16px; margin: 20px 0;">
                <p style="margin: 0; color: #111827;">
                    ✅ <strong>SendGrid connected</strong><br>
                    ✅ <strong>API Key working</strong><br>
                    ✅ <strong>Sender email verified</strong><br>
                    ✅ <strong>Notifications ready</strong>
                </p>
            </div>

            <p style="color: #6b7280; font-size: 14px;">
                Next step: Sales and Billing inquiries will trigger
                instant alerts to this email address.
            </p>

        </div>
        """
    )

    if success:
        print("✅ Test email sent successfully!")
        print("   Check your inbox now.\n")
    else:
        print("❌ Test email failed.")
        print("   Check your SendGrid API key and verified sender email.\n")

# ---------------------------------------------------------------------------
# Urgent Notification Functions
# ---------------------------------------------------------------------------

def send_urgent_notification(name, email, message, category, urgency, summary):
    """
    Sends an instant email alert to the business owner
    when a Sales or Billing inquiry comes in.

    Called from app.py after AI categorization.
    Only triggers for Sales (Very Urgent) and Billing (Urgent).
    """

    # Color and emoji based on category
    if category == "Sales":
        color  = "#dc2626"   # red
        emoji  = "🔴"
        label  = "VERY URGENT — New Sales Inquiry"
    else:
        color  = "#ea580c"   # orange
        emoji  = "🟠"
        label  = "URGENT — New Billing Inquiry"

    subject = f"{emoji} {label}"

    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px;
                margin: 0 auto; padding: 20px;">

        <div style="background: {color}; border-radius: 8px;
                    padding: 16px; margin-bottom: 20px;">
            <h2 style="color: #ffffff; margin: 0;">{emoji} {label}</h2>
        </div>

        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px; background: #f9fafb;
                           font-weight: bold; width: 140px;
                           border-bottom: 1px solid #e5e7eb;">
                    Customer Name
                </td>
                <td style="padding: 10px; background: #f9fafb;
                           border-bottom: 1px solid #e5e7eb;">
                    {name}
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; width: 140px;
                           border-bottom: 1px solid #e5e7eb;">
                    Email
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">
                    <a href="mailto:{email}">{email}</a>
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; background: #f9fafb;
                           font-weight: bold; width: 140px;
                           border-bottom: 1px solid #e5e7eb;">
                    Category
                </td>
                <td style="padding: 10px; background: #f9fafb;
                           border-bottom: 1px solid #e5e7eb;">
                    {category} — {urgency}
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; width: 140px;
                           border-bottom: 1px solid #e5e7eb;">
                    AI Summary
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">
                    {summary}
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; background: #f9fafb;
                           font-weight: bold; vertical-align: top;
                           width: 140px;">
                    Message
                </td>
                <td style="padding: 10px; background: #f9fafb;">
                    {message}
                </td>
            </tr>
        </table>

        <div style="margin-top: 24px; padding: 12px;
                    background: #fef3c7; border-radius: 8px;
                    border-left: 4px solid {color};">
            <p style="margin: 0; font-size: 14px; color: #92400e;">
                ⚡ This inquiry requires immediate attention.
                Please respond to <a href="mailto:{email}">{email}</a> as soon as possible.
            </p>
        </div>

    </div>
    """

    notification_email = os.getenv("NOTIFICATION_EMAIL")
    return send_email(notification_email, subject, body)