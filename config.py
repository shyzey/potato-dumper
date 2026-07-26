import os
import sys

APP_NAME = "potato dumper"
CURRENT_VERSION = "2.0"

APPDATA_DIR = os.path.join(os.getenv("APPDATA", "."), APP_NAME)
os.makedirs(APPDATA_DIR, exist_ok=True)

LINKS_FILE = os.path.join(APPDATA_DIR, "plati_links.json")
SETTINGS_FILE = os.path.join(APPDATA_DIR, "settings.json")
LOG_FILE = os.path.join(APPDATA_DIR, "log.txt")

# ── Цвета (1:1 из оригинала) ──
C_PRIMARY = "#adb40c"
C_PRIMARY_HOVER = "#a8b40c"
C_PRIMARY_DARK = "#8b940c"
C_BLACK = "black"
C_DARK = "#141414"
C_WHITE = "white"
C_DIM = "#757575"
C_PLACEHOLDER = "#3B3B3B"

# ── Шрифт ──
FONT = "Oswald"

# ── Плейсхолдеры ──
PH_LINK = "Введите ссылку на категорию товара"
PH_LIMIT = "Мин. цена"
PH_SALES = "Продажи"
PH_STEP = "Изм. в руб."

# ── Настройки по умолчанию ──
DEFAULT_SETTINGS = {
    "seller_id": 1234567,
    "api_key": "API_KEY",
    "timeout": 600,
    "threads": 5,
}

MIN_TIMEOUT = 600
MIN_THREADS = 5
MAX_THREADS = 32


def resource_path(relative: str) -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)