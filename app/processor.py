import json
from datetime import datetime, timezone


def process_message(body: bytes) -> bytes:
    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Niepoprawny JSON/UTF-8: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Wiadomość musi być obiektem JSON (nie tablicą ani skalarem)")

    # TODO - przypisywanie kategorii

    result = {
        "message": data["message"],
        "user": data["user"],
        "send_time": data["send_time"],
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "category": "EXAMPLE",
    }

    return json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
