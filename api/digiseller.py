import hashlib
import time
import requests


class DigisellerAPI:
    AUTH_URL = "https://api.digiseller.ru/api/apilogin"
    PRODUCTS_URL = "https://api.digiseller.com/api/seller-goods"
    PRICES_URL = "https://api.digiseller.ru/api/product/edit/prices"
    TOKEN_TTL = 1200

    def __init__(self, session: requests.Session, seller_id: int, api_key: str):
        self.session = session
        self.seller_id = seller_id
        self.api_key = api_key
        self._token: str | None = None
        self._token_ts: float = 0.0

    @property
    def token(self) -> str:
        if self._token and (time.time() - self._token_ts) < self.TOKEN_TTL:
            return self._token
        self._token = self._auth()
        self._token_ts = time.time()
        return self._token

    def _auth(self) -> str:
        ts = int(time.time())
        sign = hashlib.sha256(f"{self.api_key}{ts}".encode()).hexdigest()
        resp = self.session.post(self.AUTH_URL, json={
            "seller_id": self.seller_id,
            "timestamp": ts,
            "sign": sign,
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("retval") != 0:
            raise RuntimeError(f"Ошибка авторизации: {data}")
        return data["token"]

    def get_products(self) -> tuple[list[dict], str]:
        resp = self.session.post(
            f"{self.PRODUCTS_URL}?token={self.token}",
            json={
                "id_seller": self.seller_id,
                "page": 1,
                "rows": 100,
                "currency": "RUR",
                "lang": "ru-RU",
                "show_hidden": 1,
                "order_col": "name",
                "order_dir": "asc",
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        seller_name = data.get("name_seller", "")
        products = data.get("rows") or data.get("products") or data.get("goods") or []
        return products, seller_name

    def update_prices(self, updates: list[dict]) -> None:
        if not updates:
            return
        payload = [
            {"ProductId": u["product_id"], "product_id": u["product_id"],
             "price": round(u["price"], 2)}
            for u in updates
        ]
        resp = self.session.post(
            f"{self.PRICES_URL}?token={self.token}",
            json=payload, timeout=20,
        )
        if not resp.ok:
            raise RuntimeError(f"API {resp.status_code}: {resp.text[:200]}")
        resp.raise_for_status()