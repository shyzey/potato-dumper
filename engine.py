import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from api.digiseller import DigisellerAPI
from api.plati import PlatiPriceChecker
from config import LINKS_FILE, MIN_TIMEOUT, PH_LINK
from utils import load_json


def create_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=2, backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=32)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/125.0.0.0 Safari/537.36"),
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.7",
    })
    return s


class DumpEngine:
    def __init__(self, settings: dict, log_fn, ui_callback):
        self.settings = settings
        self.log = log_fn
        self.ui_callback = ui_callback
        self.session = create_session()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def shutdown(self):
        self.stop()
        self.session.close()

    def _loop(self):
        while not self._stop.is_set():
            self._cycle()
            timeout = max(self.settings.get("timeout", MIN_TIMEOUT), MIN_TIMEOUT)
            self._stop.wait(timeout=timeout)

    def _cycle(self):
        api = DigisellerAPI(self.session,
                            self.settings["seller_id"],
                            self.settings["api_key"])

        t0 = time.time()
        try:
            products, seller_name = api.get_products()
        except Exception as e:
            self.log(f"Ошибка получения товаров: {e}")
            return
        self.log(f"Товары получены за {time.time()-t0:.1f}s ({len(products)} шт)")

        products = [p for p in products if p.get("in_stock") != 0]
        if not products:
            self.log("Список товаров пуст.")
            return

        self.ui_callback("products_loaded", products)

        tasks = self._build_tasks(products)
        if not tasks:
            self.log("Нет ссылок для проверки.")
            return

        t0 = time.time()
        checker = PlatiPriceChecker(self.session, seller_name, self.log)
        updates = self._parallel(checker, tasks)
        self.log(f"Проверка цен: {time.time()-t0:.1f}s ({len(tasks)} товаров)")

        if updates:
            t0 = time.time()
            try:
                api.update_prices(updates)
                for u in updates:
                    self.log(f"✓ Товар {u['product_id']} → {u['price']} ₽")
            except Exception as e:
                self.log(f"Ошибка обновления цен: {e}")
            self.log(f"Обновление цен API: {time.time()-t0:.1f}s")

        self.log("Цикл завершён.")

    def _build_tasks(self, products):
        links = load_json(LINKS_FILE, {})
        tasks = []
        for p in products:
            pid = str(p.get("id_goods"))
            st = links.get(pid, {})
            if isinstance(st, str):
                st = {"url": st}
            url = (st.get("url") or "").strip()
            if not url or url == PH_LINK:
                continue
            tasks.append({
                "product_id": p.get("id_goods"),
                "own_price": float(p.get("price") or 0),
                "url": url,
                "limit": st.get("min_limit"),
                "min_sales": int(st.get("min_sales") or 0),
                "step": float(st.get("price_step") or 1.0),
            })
        return tasks

    def _parallel(self, checker, tasks):
        threads = self.settings.get("threads", 5)
        updates = []
        with ThreadPoolExecutor(max_workers=threads) as pool:
            futs = {pool.submit(self._one, checker, t): t for t in tasks}
            for f in as_completed(futs):
                if self._stop.is_set():
                    break
                try:
                    r = f.result()
                    if r:
                        updates.append(r)
                except Exception as e:
                    self.log(f"Поток {futs[f]['product_id']}: {e}")
        return updates

    def _one(self, checker, task):
        pid = task["product_id"]
        min_price, _ = checker.get_min_price(task["url"], task["limit"],
                                            task["min_sales"])

        if min_price is None:
            return None

        own = task["own_price"]
        target = round(float(min_price) - task["step"], 2)
        if task["limit"] is not None and target < task["limit"]:
            target = float(task["limit"])

        if target == own:
            self.log(f" = Без изменений: {pid} | {own} (оптимальна)")
            return None

        arrow = "↑" if target > own else "↓"
        self.log(f" {arrow} {pid}: {own} → {target} (лидер: {min_price})")
        return {"product_id": int(pid), "price": target}