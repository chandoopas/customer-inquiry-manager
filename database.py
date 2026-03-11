"""
database.py
===========
Handles all database connections and queries.
All interaction with Azure SQL goes through this file.

Day 6  : insert_customer, insert_inquiry, get_all_inquiries
Day 10 : insert_ai_category added
"""

import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_connection():
    """
    Creates and returns a connection to Azure SQL Database.
    Reads credentials from environment variables — never hardcoded.
    """
    connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USERNAME')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
    )
    return pyodbc.connect(connection_string)


# ---------------------------------------------------------------------------
# Customer Functions
# ---------------------------------------------------------------------------

def get_or_create_customer(name, email):
    """
    Checks if a customer with this email already exists.
    If yes  → returns their existing id.
    If no   → creates a new customer row and returns the new id.

    This prevents duplicate customers if the same person
    submits multiple inquiries.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    # Check if customer already exists
    cursor.execute(
        "SELECT id FROM Customers WHERE email = ?",
        (email,)
    )
    row = cursor.fetchone()

    if row:
        # Customer exists — return their id
        customer_id = row[0]
    else:
        # Customer is new — insert them and get the new id
        cursor.execute(
            "INSERT INTO Customers (name, email) VALUES (?, ?)",
            (name, email)
        )
        conn.commit()

        # Fetch the id that was just created
        cursor.execute(
            "SELECT id FROM Customers WHERE email = ?",
            (email,)
        )
        customer_id = cursor.fetchone()[0]

    conn.close()
    return customer_id


# ---------------------------------------------------------------------------
# Inquiry Functions
# ---------------------------------------------------------------------------

def insert_inquiry(customer_id, message):
    """
    Saves a new inquiry to the Inquiries table.
    Status defaults to 'Open' automatically (set in the table schema).
    Returns the new inquiry's id — needed to link AICategories later.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO Inquiries (customer_id, message) VALUES (?, ?)",
        (customer_id, message)
    )
    conn.commit()

    # Get the id of the row we just inserted
    cursor.execute(
        "SELECT TOP 1 id FROM Inquiries ORDER BY id DESC"
    )
    inquiry_id = cursor.fetchone()[0]

    conn.close()
    return inquiry_id


def get_all_inquiries():
    """
    Fetches all inquiries joined with customer details and AI categories.
    This is the query the admin dashboard will use in Week 3.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.name          AS customer_name,
            c.email         AS customer_email,
            i.id            AS inquiry_id,
            i.message       AS message,
            i.status        AS status,
            i.created_at    AS received_at,
            a.category      AS category,
            a.urgency_level AS urgency,
            a.ai_summary    AS summary
        FROM Inquiries i
        JOIN Customers     c ON i.customer_id = c.id
        LEFT JOIN AICategories a ON a.inquiry_id = i.id
        ORDER BY i.created_at DESC
    """)

    # Convert results into a list of dictionaries — easier to work with in Flask
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    conn.close()
    return results


# ---------------------------------------------------------------------------
# AI Category Functions
# ---------------------------------------------------------------------------

def insert_ai_category(inquiry_id, category, urgency_level, ai_summary):
    """
    Saves the AI categorization result to the AICategories table.
    Called immediately after categorize_inquiry() returns a result.

    Args:
        inquiry_id    (int): The ID of the inquiry this category belongs to
        category      (str): Sales | Billing | Support | General
        urgency_level (str): Very Urgent | Urgent | Medium | Low
        ai_summary    (str): One line AI generated summary
    """
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO AICategories (inquiry_id, category, urgency_level, ai_summary)
        VALUES (?, ?, ?, ?)
    """, (inquiry_id, category, urgency_level, ai_summary))

    conn.commit()
    conn.close()