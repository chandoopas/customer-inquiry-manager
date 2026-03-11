"""
ai_service.py
=============
Day 11 Update: Replaced print statements with proper logging.

This file handles all communication with Azure OpenAI.
It reads customer inquiry messages and classifies them into:

    Category      | Urgency Level
    --------------|---------------
    Sales         | Very Urgent
    Billing       | Urgent
    Support       | Medium
    General       | Low

All responses are returned as structured JSON so they are
easy to parse and save to the AICategories table in the database.
"""

import os
import json
import logging
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use the same logger as app.py so all logs go to the same file
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Azure OpenAI Client
# ---------------------------------------------------------------------------

client = AzureOpenAI(
    api_key        = os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version    = "2024-02-01"
)

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are a customer service AI assistant for a business.
Your job is to read a customer inquiry message and classify it.

You must classify every message into exactly ONE of these categories:

1. Sales    — Customer wants to buy, get pricing, request a quote,
               discuss bulk orders, partnerships, or enterprise deals.
               Urgency: Very Urgent

2. Billing  — Customer has a payment issue, invoice problem,
               refund request, double charge, or subscription concern.
               Urgency: Urgent

3. Support  — Customer has a technical problem, login issue,
               password reset issue, bug report, or needs help
               using a product/service.
               Urgency: Medium

4. General  — Everything else. Questions about hours, contact info,
               general feedback, compliments, or unclear inquiries.
               Urgency: Low

You must respond with ONLY a valid JSON object. No extra text, no explanation,
no markdown code blocks. Just the raw JSON.

Your response must follow this exact format:
{
    "category": "Sales",
    "urgency": "Very Urgent",
    "summary": "One sentence summarizing the inquiry in plain English."
}

Rules:
- category must be exactly one of: Sales, Billing, Support, General
- urgency must match the category exactly as shown above
- summary must be a single clear sentence under 20 words
- Never add extra fields or change the JSON structure
"""

# ---------------------------------------------------------------------------
# Main Function
# ---------------------------------------------------------------------------

def categorize_inquiry(message):
    """
    Sends a customer message to Azure OpenAI and returns
    the category, urgency level, and a one-line summary.

    Args:
        message (str): The raw customer inquiry message

    Returns:
        dict: {
            "category": "Sales" | "Billing" | "Support" | "General",
            "urgency":  "Very Urgent" | "Urgent" | "Medium" | "Low",
            "summary":  "One sentence summary of the inquiry"
        }

    Returns a safe fallback dict if anything goes wrong,
    so the app never crashes due to an AI failure.
    """
    raw_response = None

    try:
        response = client.chat.completions.create(
            model    = DEPLOYMENT_NAME,
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Customer message: {message}"}
            ],
            temperature = 0.1,
            max_tokens  = 150
        )

        # Extract the raw text response
        raw_response = response.choices[0].message.content.strip()

        # Parse JSON response
        result = json.loads(raw_response)

        # Validate all expected keys are present
        required_keys = {"category", "urgency", "summary"}
        if not required_keys.issubset(result.keys()):
            raise ValueError(f"Missing keys in AI response: {result}")

        # Validate category is one of the 4 expected values
        valid_categories = {"Sales", "Billing", "Support", "General"}
        if result["category"] not in valid_categories:
            raise ValueError(f"Unexpected category: {result['category']}")

        return result

    except json.JSONDecodeError as e:
        logger.error(f"AI returned invalid JSON: {e} | Raw response: {raw_response}")
        return _fallback_response()

    except Exception as e:
        logger.error(f"AI categorization failed: {e}")
        return _fallback_response()


def _fallback_response():
    """
    Returns a safe default response when AI categorization fails.
    The inquiry is still saved to the database — nothing is lost.
    Admin dashboard will show these as General/Low for manual review.
    """
    return {
        "category": "General",
        "urgency":  "Low",
        "summary":  "AI categorization failed — please review manually."
    }


# ---------------------------------------------------------------------------
# Test Runner
# Run directly to test all 10 sample messages:
#   python ai_service.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # Set up basic logging for standalone test run
    logging.basicConfig(
        level  = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s"
    )

    test_messages = [
        {"id": 1, "expected": "Sales",
         "message": "Hi, we are a company of 50 employees and we are interested in purchasing your product. Can you send us a quote and pricing details?"},
        {"id": 2, "expected": "Billing",
         "message": "I was charged twice on my credit card this month for my subscription. Invoice number 1042. Please refund the duplicate charge."},
        {"id": 3, "expected": "Support",
         "message": "I cannot log into my account. I tried resetting my password but I am not receiving the reset email. Please help."},
        {"id": 4, "expected": "General",
         "message": "What are your office hours and do you have a phone number I can call to speak with someone directly?"},
        {"id": 5, "expected": "Sales",
         "message": "URGENT: We need 200 units delivered by end of this week for a major product launch. Please contact me immediately with pricing."},
        {"id": 6, "expected": "Billing",
         "message": "My payment was declined but the money was taken from my account. I need this resolved immediately."},
        {"id": 7, "expected": "Support",
         "message": "The app keeps crashing every time I try to upload a file. I am using iPhone 15 and the latest version of your app."},
        {"id": 8, "expected": "General",
         "message": "Just wanted to say your customer service team was amazing last week. Really impressed with the response time!"},
        {"id": 9, "expected": "Sales",
         "message": "We are interested in an enterprise partnership. Can we schedule a call to discuss bulk licensing options for our organization?"},
        {"id": 10, "expected": "Support",
         "message": "How do I reset my password? I have tried the forgot password link but nothing is working."},
    ]

    print("\n" + "="*70)
    print("TESTING AI CATEGORIZATION — 10 SAMPLE MESSAGES")
    print("="*70)

    passed = 0
    failed = 0

    for test in test_messages:
        result    = categorize_inquiry(test["message"])
        is_correct = result["category"] == test["expected"]
        status     = "✅ PASS" if is_correct else "❌ FAIL"

        if is_correct:
            passed += 1
        else:
            failed += 1

        print(f"\nTest {test['id']:02d} {status}")
        print(f"  Message  : {test['message'][:70]}...")
        print(f"  Expected : {test['expected']}")
        print(f"  Got      : {result['category']} ({result['urgency']})")
        print(f"  Summary  : {result['summary']}")

    print("\n" + "="*70)
    print(f"RESULTS: {passed}/10 passed | {failed}/10 failed")
    print("="*70 + "\n")

    if failed == 0:
        print("🎉 All tests passed!\n")
    else:
        print("⚠️  Some tests failed. Review and adjust SYSTEM_PROMPT.\n")