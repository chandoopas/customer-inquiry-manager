"""
Customer Inquiry Manager
========================
Day 3: Basic Flask Web Application with Inquiry Submission Form

What this file does:
- Serves the home page with a customer inquiry form
- Handles form submission and displays a confirmation message
- Lays the structure that we will build on in later days (database, AI, notifications)

Run locally:
    python app.py
Then open: http://localhost:5000
"""

from flask import Flask, render_template_string, request, redirect, url_for

# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------

app = Flask(__name__)


# ---------------------------------------------------------------------------
# HTML Templates
# We use render_template_string here so everything stays in one file for now.
# In later days we will move templates to a /templates folder.
# ---------------------------------------------------------------------------

# The main page template with the inquiry form
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Customer Inquiry Manager</title>
    <style>
        /* ---- Reset & Base ---- */
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

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

        /* ---- Card ---- */
        .card {
            background: #1a1d27;
            border: 1px solid #2a2d3a;
            border-radius: 16px;
            padding: 3rem 2.5rem;
            width: 100%;
            max-width: 560px;
            box-shadow: 0 24px 60px rgba(0,0,0,0.4);
        }

        /* ---- Header ---- */
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

        /* ---- Form ---- */
        .form-group {
            margin-bottom: 1.25rem;
        }

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

        textarea {
            resize: vertical;
            min-height: 130px;
            line-height: 1.6;
        }

        /* ---- Submit Button ---- */
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

        /* ---- Flash Message ---- */
        .flash {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            color: #4ade80;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
        }

        /* ---- Footer note ---- */
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

        <!-- Header -->
        <div class="badge">Customer Support</div>
        <h1>How can we help you?</h1>
        <p class="subtitle">
            Fill out the form below and we'll get back to you as soon as possible.
        </p>

        <!-- Success message shown after submission -->
        {% if submitted %}
        <div class="flash">
            ✅ Your inquiry has been received. We'll be in touch shortly.
        </div>
        {% endif %}

        <!-- Inquiry Form -->
        <form method="POST" action="/submit">

            <div class="form-group">
                <label for="name">Full Name</label>
                <input
                    type="text"
                    id="name"
                    name="name"
                    placeholder="Jane Smith"
                    required
                >
            </div>

            <div class="form-group">
                <label for="email">Email Address</label>
                <input
                    type="email"
                    id="email"
                    name="email"
                    placeholder="jane@company.com"
                    required
                >
            </div>

            <div class="form-group">
                <label for="message">Your Message</label>
                <textarea
                    id="message"
                    name="message"
                    placeholder="Describe your inquiry in detail..."
                    required
                ></textarea>
            </div>

            <button type="submit" class="btn">Send Inquiry →</button>

        </form>

        <p class="footer-note">Your message is handled securely and privately.</p>
    </div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    """
    Home page route.
    Renders the inquiry submission form.
    """
    return render_template_string(HOME_TEMPLATE, submitted=False)


@app.route("/submit", methods=["POST"])
def submit():
    """
    Form submission route.

    Right now this just reads the form data and prints it to the terminal.
    In Day 6 we will save this data to the Azure SQL database.
    In Day 9 we will pass the message to Azure OpenAI for categorization.
    In Day 13 we will trigger email notifications based on the AI's category.
    """
    # Read the submitted form data
    name    = request.form.get("name", "").strip()
    email   = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()

    # Basic validation — make sure none of the fields are empty
    if not name or not email or not message:
        # If any field is empty, send them back to the form
        return redirect(url_for("home"))

    # For now: print the submission to the terminal so you can see it
    # This is temporary — Day 6 replaces this with a database insert
    print("\n" + "="*50)
    print("NEW INQUIRY RECEIVED")
    print("="*50)
    print(f"  Name   : {name}")
    print(f"  Email  : {email}")
    print(f"  Message: {message}")
    print("="*50 + "\n")

    # Show the form again with a success message
    return render_template_string(HOME_TEMPLATE, submitted=True)


# ---------------------------------------------------------------------------
# Run the App
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # debug=True means Flask will auto-reload when you save changes to this file
    # IMPORTANT: never use debug=True in production (on the VM with Gunicorn)
    app.run(debug=True, host="0.0.0.0", port=5001)