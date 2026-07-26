import re
import threading
import time
import random
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup


class PlatiPriceChecker:
    SEARCH_API = "https://api.digiseller.com/api/cataloguer/front/products"
    CATEGORY_EP = "https://plati.market/asp/block_goods_category_2.asp"

    def __init__(self, session: requests.Session, seller_name: str, log_fn):
        self.session = session
        self.seller_name = seller_name
        self.log = log_fn
        self._lock = threading.Lock()
        self._last = 0.0
        self._gap = 0.05

    def _throttle(self):
        with self._lock:
            wait = self._gap - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait + random.uniform(0, 0.1))
            self._last = time.time()

    def get_min_price(self, url: str, limit: int | None = None,
                    min_sales: int = 0) -> tuple[int | None, int | None]:
        if not url:
            return None, None

        if "/search/" in url:
            q = self._search_query(url)
            if q:
                return self._search_api(q, limit, min_sales)
            return None, None

        id_cb, id_c = self._cat_ids(url)
        if id_cb and id_c:
            return self._cat_endpoint(id_cb, id_c, limit, min_sales)

        self.log(f"Fallback-парсинг: {url[:60]}...")
        return self._page(url, limit, min_sales)

    # ── search ──

    def _search_query(self, url: str) -> str | None:
        try:
            parts = url.split("/search/")
            if len(parts) >= 2:
                return unquote(parts[1].split("?")[0].split("#")[0])
        except Exception:
            pass
        return None

    def _search_api(self, query, limit, min_sales):
        prices: list[int] = []
        for page in range(1, 11):
            self._throttle()
            try:
                resp = self.session.get(self.SEARCH_API, params={
                    "productName": query, "ownerId": "plati",
                    "currency": "RUB", "page": page, "count": 30,
                    "sortBy": "popular", "fuzzy": "false", "lang": "ru-RU",
                    "individual": "false", "video": "false", "image": "false",
                }, timeout=15)
                if resp.status_code == 429:
                    time.sleep(4 + random.uniform(0, 2))
                    continue
                resp.raise_for_status()
                data = resp.json()
                if data.get("retval") != 0:
                    break
                content = data.get("content", {})
                items = content.get("items", [])
                if not items:
                    break
                for it in items:
                    if it.get("seller_name") == self.seller_name:
                        continue
                    p = it.get("price")
                    if p is None:
                        continue
                    s = int(it.get("total_sales") or it.get("month_sales") or 0)
                    if s >= min_sales:
                        prices.append(int(float(p)))
                if not content.get("has_next_page", False):
                    break
            except requests.RequestException as e:
                self.log(f"Search API (p{page}): {e}")
                break
        return self._pick(prices, limit)

    # ── category ──

    def _cat_ids(self, url):
        try:
            m1 = re.search(r"/games/[^/]+/(\d+)/", url)
            m2 = re.search(r"id_c=(\d+)", url)
            if m1 and m2:
                return m1.group(1), m2.group(1)
        except Exception:
            pass
        return None, None

    def _cat_endpoint(self, id_cb, id_c, limit, min_sales):
        self._throttle()
        try:
            resp = self.session.get(self.CATEGORY_EP, params={
                "id_cb": id_cb, "id_c": id_c, "sort": "price",
                "page": 1, "rows": 1000, "curr": "RUB", "lang": "ru",
            }, headers={"Referer": "https://plati.market/"}, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            self.log(f"Category EP: {e}")
            return None, None
        return self._html(resp.text, limit, min_sales)

    # ── fallback page ──

    def _page(self, url, limit, min_sales):
        self._throttle()
        try:
            resp = self.session.get(url, headers={"Referer": "https://plati.market/"},
                                    timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            self.log(f"Page parse: {e}")
            return None, None
        return self._html(resp.text, limit, min_sales)

    # ── html ──

    def _html(self, text, limit, min_sales):
        soup = BeautifulSoup(text, "lxml")
        prices: list[int] = []
        items = soup.find_all("li", class_="section-list__item")
        if not items:
            items = soup.find_all("a", class_="card")

        for item in items:
            try:
                st = item.find("span",
                               class_="caption-semibold color-text-secondary text-truncate")
                if st and st.get_text(strip=True) == self.seller_name:
                    continue
                pt = item.find("span", class_="title-bold color-text-title")
                if not pt:
                    continue
                d = re.sub(r"\D", "", pt.get_text(strip=True))
                if not d:
                    continue
                price = int(d)
                sales = 0
                for sp in item.find_all("span"):
                    t = sp.get_text(strip=True)
                    if "Продано" in t:
                        nums = re.findall(r"\d+", t)
                        if nums:
                            sales = int(nums[-1])
                        break
                if sales >= min_sales:
                    prices.append(price)
            except Exception:
                continue
        return self._pick(prices, limit)

    @staticmethod
    def _pick(prices, limit):
        if not prices:
            return None, None
        prices.sort()
        if limit is not None:
            prices = [p for p in prices if p >= limit]
            if not prices:
                return None, None
        return prices[0], (prices[1] if len(prices) > 1 else None)