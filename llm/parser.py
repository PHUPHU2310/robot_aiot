import json
from typing import Dict, Optional
from urllib import error, request

from config import (
    OLLAMA_BASE_URL,
    OLLAMA_ENABLED,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
)

OBJECT_ALIASES = {
    "chai_nuoc": ["chai nước", "chai", "water bottle", "bottle"],
    "coc": ["cốc", "ly", "cup"],
    "but": ["bút", "cây bút", "pen"],
    "dien_thoai": ["điện thoại", "phone"],
    "hop": ["hộp", "box"],
}

ACTION_ALIASES = {
    "pick_place": ["gắp", "lấy", "nhặt", "đưa", "thả", "pick", "place"],
}


def parse_command_rule_based(text: str) -> Dict:
    """Parser dự phòng để hệ thống vẫn chạy khi Ollama chưa sẵn sàng."""
    normalized = text.lower().strip()

    action = None
    for action_name, words in ACTION_ALIASES.items():
        if any(word in normalized for word in words):
            action = action_name
            break

    target_object: Optional[str] = None
    for object_name, aliases in OBJECT_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            target_object = object_name
            break

    return {
        "raw_command": text,
        "action": action,
        "target_object": target_object,
        "parser": "rule_based_v1",
    }


def parse_command_ollama(text: str) -> Dict:
    """Dùng Ollama local API và ép kết quả theo JSON Schema."""
    schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": ["string", "null"],
                "enum": ["pick_place", None],
            },
            "target_object": {
                "type": ["string", "null"],
                "enum": [*OBJECT_ALIASES.keys(), None],
            },
        },
        "required": ["action", "target_object"],
        "additionalProperties": False,
    }
    prompt = (
        "Bạn là bộ phân tích lệnh cho robot gắp và thả. "
        "Chỉ nhận diện action=pick_place khi người dùng muốn gắp/lấy/nhặt/đưa/thả vật. "
        "Các vật hợp lệ: chai_nuoc (chai nước), coc (cốc/ly), but (bút), "
        "dien_thoai (điện thoại), hop (hộp). "
        "Nếu không nhận diện được, trả null cho trường tương ứng.\n"
        f"Lệnh người dùng: {text}"
    )
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "format": schema,
        "stream": False,
        "think": False,
        "options": {"temperature": 0},
        "keep_alive": "5m",
    }
    http_request = request.Request(
        f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with request.urlopen(http_request, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
        api_result = json.loads(response.read().decode("utf-8"))

    parsed = json.loads(api_result["response"])
    action = parsed.get("action")
    target = parsed.get("target_object")
    if action not in {None, "pick_place"}:
        action = None
    if target not in OBJECT_ALIASES:
        target = None

    return {
        "raw_command": text,
        "action": action,
        "target_object": target,
        "parser": f"ollama:{OLLAMA_MODEL}",
    }


def parse_command(text: str) -> Dict:
    if not OLLAMA_ENABLED:
        return parse_command_rule_based(text)

    try:
        return parse_command_ollama(text)
    except (error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError) as exc:
        fallback = parse_command_rule_based(text)
        fallback["parser"] = "rule_based_fallback"
        fallback["parser_warning"] = f"Ollama chưa sẵn sàng: {type(exc).__name__}"
        return fallback
