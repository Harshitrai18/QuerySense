
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise SystemExit("GROQ_API_KEY is missing from .env")

client = Groq(api_key=api_key)

try:
    models = client.models.list()
    available = sorted(model.id for model in models.data)

    print("Available models:")
    for model in available:
        print(model)

    target = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    if target in available:
        print(f"\nPASS: {target} is listed.")
    else:
        print(f"\nModel not listed: {target}")
        print("Choose a compatible model from the list above.")

except Exception as error:
    print(f"Model-list request failed: {type(error).__name__}")
    print("Check your API key, network, and account access.")
