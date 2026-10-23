
from clarification import (
    detect_clarification,
    apply_clarification,
)


passed = 0
failed = 0


def check(name, test_function):
    """Run one test and report its result."""

    global passed, failed

    try:
        test_function()
        print(f"PASS: {name}")
        passed += 1
    except Exception as error:
        print(f"FAIL: {name} — {error}")
        failed += 1


# --------------------------------------------------
# Basic input tests
# --------------------------------------------------

def test_empty_question():
    assert detect_clarification("") is None
    assert detect_clarification("   ") is None
    assert detect_clarification(None) is None


def test_case_insensitive_matching():
    result = detect_clarification(
        "SHOW ME THE BEST CUSTOMERS"
    )

    assert result is not None
    assert result["category"] == "customers"


def test_specific_question_needs_no_clarification():
    assert detect_clarification(
        "Show me customers in Delhi"
    ) is None


def test_all_categories_are_detected():
    cases = [
        ("Show me the best customers", "customers"),
        ("Show me the top products", "products"),
        ("Which are the best cities?", "cities"),
        ("Show me the top orders", "orders"),
    ]

    for question, expected_category in cases:
        result = detect_clarification(question)

        assert result is not None, (
            f"No clarification detected for: {question}"
        )

        assert result["category"] == expected_category


# --------------------------------------------------
# Clarification metadata tests
# --------------------------------------------------

def test_options_are_present():
    result = detect_clarification(
        "Show me the best customers"
    )

    assert result is not None

    assert set(result["options"]) == {
        "spending",
        "orders",
        "recent",
    }


def test_original_question_is_preserved():
    question = "Show me the best customers"

    result = detect_clarification(question)

    assert result is not None
    assert result["original_question"] == question


# --------------------------------------------------
# New natural-language detection tests
# --------------------------------------------------

def test_natural_ambiguous_questions():
    cases = [
        ("Who spends the most?", "customers"),
        ("Which products sell the most?", "products"),
        ("Which city performs best?", "cities"),
        ("What are my most valuable orders?", "orders"),
    ]

    for question, expected_category in cases:
        result = detect_clarification(question)

        assert result is not None, (
            f"Expected clarification for: {question}"
        )

        assert result["category"] == expected_category, (
            f"Expected {expected_category}, "
            f"got {result['category']}"
        )


def test_additional_customer_phrasings():
    questions = [
        "Who spent the most?",
        "Which customer spends the most?",
        "Which clients buy the most?",
    ]

    for question in questions:
        assert detect_clarification(question) is not None, (
            f"Expected customer clarification for: {question}"
        )


def test_additional_product_phrasings():
    questions = [
        "Which product sells the most?",
        "Which products are most popular?",
        "What products sell the most?",
    ]

    for question in questions:
        result = detect_clarification(question)

        assert result is not None, (
            f"Expected product clarification for: {question}"
        )

        assert result["category"] == "products"


def test_additional_city_phrasings():
    questions = [
        "Compare city performance",
        "Which cities perform the best?",
    ]

    for question in questions:
        result = detect_clarification(question)

        assert result is not None, (
            f"Expected city clarification for: {question}"
        )

        assert result["category"] == "cities"


def test_additional_order_phrasings():
    questions = [
        "Which orders have the highest value?",
        "Show orders with the highest value",
    ]

    for question in questions:
        result = detect_clarification(question)

        assert result is not None, (
            f"Expected order clarification for: {question}"
        )

        assert result["category"] == "orders"


# --------------------------------------------------
# Apply clarification tests
# --------------------------------------------------

def test_customer_spending_clarification():
    result = apply_clarification(
        "Show me the best customers",
        "spending",
    )

    assert "total spending" in result.lower()
    assert "completed orders" in result.lower()


def test_customer_order_clarification():
    result = apply_clarification(
        "Show me the best customers",
        "orders",
    )

    assert "order counts" in result.lower()


def test_product_quantity_clarification():
    result = apply_clarification(
        "Show me the best products",
        "quantity",
    )

    assert "units sold" in result.lower()


def test_city_customer_clarification():
    result = apply_clarification(
        "Show me the best cities",
        "customers",
    )

    assert "number of customers" in result.lower()


def test_order_value_clarification():
    result = apply_clarification(
        "Show me the top orders",
        "value",
    )

    assert "order value" in result.lower()


# --------------------------------------------------
# Invalid input tests
# --------------------------------------------------

def test_invalid_choice_is_rejected():
    try:
        apply_clarification(
            "Show me the best customers",
            "invalid_choice",
        )
    except ValueError:
        return

    raise AssertionError(
        "Invalid choice was accepted."
    )


def test_empty_choice_is_rejected():
    for choice in ("", "   ", None):
        try:
            apply_clarification(
                "Show me the best customers",
                choice,
            )
        except ValueError:
            continue

        raise AssertionError(
            f"Invalid empty choice was accepted: {choice!r}"
        )


def test_unsupported_question_rejects_clarification():
    try:
        apply_clarification(
            "Show me customers in Delhi",
            "spending",
        )
    except ValueError:
        return

    raise AssertionError(
        "Clarification was applied to an unsupported question."
    )


def test_empty_question_rejects_clarification():
    try:
        apply_clarification("", "spending")
    except ValueError:
        return

    raise AssertionError(
        "An empty question was accepted."
    )


# --------------------------------------------------
# Register and run tests
# --------------------------------------------------

tests = [
    ("Empty and invalid question input", test_empty_question),
    ("Case-insensitive matching", test_case_insensitive_matching),
    (
        "Specific question needs no clarification",
        test_specific_question_needs_no_clarification,
    ),
    ("All four categories detected", test_all_categories_are_detected),
    ("Clarification options present", test_options_are_present),
    ("Original question preserved", test_original_question_is_preserved),
    ("Natural ambiguous questions", test_natural_ambiguous_questions),
    ("Additional customer phrasings", test_additional_customer_phrasings),
    ("Additional product phrasings", test_additional_product_phrasings),
    ("Additional city phrasings", test_additional_city_phrasings),
    ("Additional order phrasings", test_additional_order_phrasings),
    ("Customer spending interpretation", test_customer_spending_clarification),
    ("Customer order interpretation", test_customer_order_clarification),
    ("Product quantity interpretation", test_product_quantity_clarification),
    ("City customer interpretation", test_city_customer_clarification),
    ("Order value interpretation", test_order_value_clarification),
    ("Invalid choice rejected", test_invalid_choice_is_rejected),
    ("Empty choices rejected", test_empty_choice_is_rejected),
    (
        "Unsupported question rejected",
        test_unsupported_question_rejects_clarification,
    ),
    ("Empty question rejected during clarification", test_empty_question_rejects_clarification),
]


print("\nQueryPilot Clarification Tests")
print("=" * 50)

for name, test_function in tests:
    check(name, test_function)

print("=" * 50)
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Total:  {passed + failed}")

if failed:
    raise SystemExit(1)

print("\nAll clarification tests passed!")
