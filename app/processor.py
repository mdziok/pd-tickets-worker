import json
from datetime import datetime, timezone
from typing import Any


def process_message(body: bytes) -> bytes:
    """
    Przykładowe reguły:
    - wiadomość musi być poprawnym JSON-em będącym obiektem,
    - pole 'event_type' jest wymagane i musi być niepustym tekstem,
    - dodajemy metadane przetwarzania.

    Dostosuj tę funkcję do własnych reguł biznesowych.
    """
    try:
        data: Any = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Niepoprawny JSON/UTF-8: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Wiadomość musi być obiektem JSON (nie tablicą ani skalarem)")

    # TODO - zmienić na faktyczny schemat payloadu income i result
    event_type = data.get("event_type")
    if not isinstance(event_type, str) or not event_type.strip():
        raise ValueError("Brak wymaganego pola 'event_type' typu tekstowego")

    result = {
        "event_type": event_type,
        "data": data,
        "processing": {
            "status": "processed",
            "fields_count": len(data),
            "processed_at": datetime.now(timezone.utc).isoformat(),
        },
    }

    # TODO - przypisywanie kategorii

    return json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
