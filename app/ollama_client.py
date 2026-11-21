import json
import os
import urllib.request

from categories import CATEGORIES

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://ollama:11434/api/generate"
)

MODEL = "qwen3:1.7b"

def analyze_ticket(message: str) -> str:
    categories_description = "\n".join(
        f"- {name}: {description}"
        for name, description in CATEGORIES.items()
    )

    prompt = f"""
        Jesteś klasyfikatorem zgłoszeń IT.

        Wybierz dokładnie jedną kategorię na podstawie jej opisu:

        {categories_description}

        Zgłoszenie:
        {message}

        Wybierz kategorię najlepiej opisującą główny problem.
        Kategorii OTHER używaj tylko wtedy, gdy żadna inna nie pasuje.

        Odpowiedz wyłącznie nazwą kategorii.
        """

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "format": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": list(CATEGORIES.keys())
                }
            },
            "required": ["category"],
            "additionalProperties": False
        },
        "options": {
            "temperature": 0,
            "num_predict": 40,
            "num_ctx": 2048
        }
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.load(response)

    analysis = json.loads(result["response"])
    category = analysis["category"]

    if category not in CATEGORIES:
        raise RuntimeError(
            f"Nieprawidłowa kategoria zwrócona przez AI: {category!r}"
        )

    return category