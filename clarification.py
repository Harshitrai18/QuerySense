
import re


CLARIFICATION_RULES = [
    {
        "category": "customers",
        "patterns": [
            r"\bwho\s+spends?\s+the\s+most\b",
            r"\bwho\s+spent\s+the\s+most\b",
            r"\bwhich\s+customers?\s+spends?\s+the\s+most\b",
            r"\bwhich\s+customers?\s+spent\s+the\s+most\b",
            r"\bwhich\s+clients?\s+buy\s+the\s+most\b",
            r"\bwho\s+buys?\s+the\s+most\b",
            r"\bbest\s+customers?\b",
            r"\btop\s+customers?\b",
            r"\bmost\s+valuable\s+customers?\b",
            r"\bcustomer\s+performance\b",
            r"\bwhich\s+customers?\s+are\s+doing\s+well\b",
            r"\bwhich\s+customers?\s+perform\s+best\b",
            r"\bwho\s+are\s+my\s+best\s+customers\b",
        ],
    },
    {
        "category": "products",
        "patterns": [
            r"\bwhich\s+products?\s+sell\s+the\s+most\b",
            r"\bwhich\s+products?\s+sells?\s+the\s+most\b",
            r"\bwhat\s+products?\s+sell\s+the\s+most\b",
            r"\bwhich\s+products?\s+are\s+most\s+popular\b",
            r"\bwhat\s+products?\s+are\s+most\s+popular\b",
            r"\bbest[\s-]+selling\s+products?\b",
            r"\bbest\s+products?\b",
            r"\btop\s+products?\b",
            r"\bmost\s+popular\s+products?\b",
            r"\bproduct\s+performance\b",
        ],
    },
    {
        "category": "cities",
        "patterns": [
            r"\bwhich\s+city\s+performs?\s+(?:the\s+)?best\b",
            r"\bwhich\s+cities\s+perform\s+(?:the\s+)?best\b",
            r"\bwhich\s+are\s+the\s+best\s+cities\b",
            r"\bcompare\s+city\s+performance\b",
            r"\bcompare\s+cities\b",
            r"\bbest\s+cities\b",
            r"\btop\s+cities\b",
            r"\bcity\s+performance\b",
            r"\bbest[\s-]+performing\s+cities\b",
        ],
    },
    {
        "category": "orders",
        "patterns": [
            r"\bwhat\s+are\s+my\s+most\s+valuable\s+orders\b",
            r"\bwhich\s+orders?\s+have\s+the\s+highest\s+value\b",
            r"\bshow\s+orders?\s+with\s+the\s+highest\s+value\b",
            r"\btop\s+orders?\b",
            r"\bmost\s+valuable\s+orders?\b",
            r"\border\s+performance\b",
        ],
    },
]


COMPILED_RULES = [
    {
        "category": rule["category"],
        "patterns": [
            re.compile(pattern, re.IGNORECASE)
            for pattern in rule["patterns"]
        ],
    }
    for rule in CLARIFICATION_RULES
]


CLARIFIED_QUESTIONS = {
    "customers": {
        "spending": (
            "Show customers ranked by total spending from completed orders. "
            "Calculate total spending using quantity multiplied by unit_price "
            "for order items belonging to completed orders."
        ),
        "orders": (
            "Show customers ranked by order counts, counting their orders."
        ),
        "recent": (
            "Show customers ranked by the date of their most recent order."
        ),
    },
    "products": {
        "revenue": (
            "Show products ranked by total sales revenue, calculated using "
            "quantity multiplied by unit_price."
        ),
        "quantity": (
            "Show products ranked by total units sold."
        ),
        "price": (
            "Show products ranked by listed price, from highest to lowest."
        ),
    },
    "cities": {
        "revenue": (
            "Show cities ranked by total sales revenue from their customers."
        ),
        "customers": (
            "Show cities ranked by the number of customers in each city."
        ),
        "orders": (
            "Show cities ranked by the number of orders placed by customers "
            "in each city."
        ),
    },
    "orders": {
        "value": (
            "Show orders ranked by total order value, calculated by summing "
            "quantity multiplied by unit_price for each order."
        ),
        "recent": (
            "Show orders sorted by order_date, newest first."
        ),
        "quantity": (
            "Show orders ranked by the total number of units in each order."
        ),
    },
}


CLARIFICATION_QUESTIONS = {
    "customers": "What should customer performance be based on?",
    "products": "What should product performance be based on?",
    "cities": "What should city performance be based on?",
    "orders": "What should order performance be based on?",
}


def detect_clarification(question):
    """Detect common ambiguous questions using predefined patterns."""

    if not isinstance(question, str) or not question.strip():
        return None

    for rule in COMPILED_RULES:
        if any(
            pattern.search(question)
            for pattern in rule["patterns"]
        ):
            category = rule["category"]

            return {
                "category": category,
                "original_question": question,
                "clarification": CLARIFICATION_QUESTIONS[category],
                "options": CLARIFIED_QUESTIONS[category].copy(),
            }

    return None


def apply_clarification(question, choice, category=None):
    """
    Convert a clarification choice into a specific database question.

    Supports rule-based detection and AI-detected clarifications.
    """

    if not isinstance(question, str) or not question.strip():
        raise ValueError("The original question must not be empty.")

    if not isinstance(choice, str) or not choice.strip():
        raise ValueError("Please select a valid clarification option.")

    if category is None:
        clarification = detect_clarification(question)

        if clarification is None:
            raise ValueError(
                "No supported clarification was detected."
            )

        category = clarification["category"]

    if category not in CLARIFIED_QUESTIONS:
        raise ValueError("Unsupported clarification category.")

    category_options = CLARIFIED_QUESTIONS[category]

    if choice not in category_options:
        raise ValueError("Invalid clarification choice.")

    return category_options[choice]
