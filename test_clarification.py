
from clarification import detect_clarification, apply_clarification


test_questions = [
    "Who are my best customers?",
    "Show me our most successful products",
    "Which cities perform best?",
]


for question in test_questions:
    print("\n" + "=" * 50)
    print("QUESTION:", question)

    result = detect_clarification(question)

    if result is None:
        print("No clarification detected.")
        continue

    print("CLARIFICATION:", result["clarification"])

    for key, label in result["options"].items():
        print(f"  {key}: {label}")

    # Test one valid option for each category.
    choice = next(iter(result["options"]))
    clarified = apply_clarification(question, choice)

    print("TEST SELECTION:", choice)
    print("CLARIFIED QUESTION:", clarified)
