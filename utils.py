import json
import os
import tempfile
import time

from config import LOG_FILE


def atomic_json_write(filepath: str, data) -> None:
    d = os.path.dirname(filepath) or "."
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, filepath)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_json(filepath: str, default=None):
    if default is None:
        default = {}
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def write_log_line(message: str) -> None:
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {message}\n"
    try:
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 2_000_000:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write(f"[{ts}] Лог очищен (превышен 2 МБ)\n")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass