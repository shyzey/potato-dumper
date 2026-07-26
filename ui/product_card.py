"""Карточка товара — tkinter, стиль 1:1 из оригинала."""

import tkinter as tk

from config import (
    C_BLACK, C_DARK, C_DIM, C_PLACEHOLDER, C_PRIMARY, C_WHITE,
    FONT, PH_LIMIT, PH_LINK, PH_SALES, PH_STEP,
)


class ProductCard(tk.Frame):
    def __init__(self, master, product: dict, stored: dict, **kw):
        super().__init__(master, bd=1, bg=C_BLACK, relief="solid", padx=10, pady=10, **kw)

        pid = str(product.get("id_goods"))
        name = product.get("name_goods", "")
        price = product.get("price", 0)

        clean = name.split("🥔")[0].strip()

        # ── row1: ID ──
        row1 = tk.Frame(self, bg=C_BLACK)
        row1.pack(fill="x")

        tk.Label(row1, text=f"ID: {pid}", bg=C_BLACK, fg=C_PRIMARY,
                 font=(FONT, 12), anchor="w").pack(side="left")

        # ── row2: имя + параметры + цена ──
        row2 = tk.Frame(self, bg=C_BLACK)
        row2.pack(fill="x", pady=(0, 10))

        max_len = 25
        display = clean[:max_len - 3] + "..." if len(clean) > max_len else clean

        lbl_name = tk.Label(row2, text=display, bg=C_BLACK, fg=C_WHITE,
                            font=(FONT, 17), anchor="w", wraplength=600)
        lbl_name.pack(side="left")

        if len(clean) > max_len:
            self._tooltip(lbl_name, clean)

        # ── правая часть: поля ──
        right = tk.Frame(row2, bg=C_BLACK)
        right.pack(side="right")

        e_style = dict(bg=C_DARK, fg=C_WHITE, relief="flat", bd=0,
                       insertbackground=C_WHITE, selectbackground=C_PRIMARY,
                       selectforeground=C_BLACK, font=(FONT, 14), justify="center")
        l_style = dict(bg=C_BLACK, fg=C_DIM, font=(FONT, 14))

        # шаг
        self.var_step = tk.StringVar(value=str(stored.get("price_step") or ""))
        ent_step = tk.Entry(right, textvariable=self.var_step, width=8, **e_style)
        ent_step.pack(side="right", ipadx=5, ipady=5)
        self._placeholder(ent_step, PH_STEP)
        tk.Label(right, text="с шагом", **l_style).pack(side="right", padx=(4, 4))

        # продажи
        self.var_sales = tk.StringVar(value=str(stored.get("min_sales") or ""))
        ent_sales = tk.Entry(right, textvariable=self.var_sales, width=8, **e_style)
        ent_sales.pack(side="right", ipadx=5, ipady=5)
        self._placeholder(ent_sales, PH_SALES)
        tk.Label(right, text="от", **l_style).pack(side="right", padx=(4, 4))

        # лимит
        self.var_limit = tk.StringVar(value=str(stored.get("min_limit") or ""))
        ent_limit = tk.Entry(right, textvariable=self.var_limit, width=8, **e_style)
        ent_limit.pack(side="right", ipadx=5, ipady=5)
        self._placeholder(ent_limit, PH_LIMIT)
        tk.Label(right, text="до", **l_style).pack(side="right", padx=(0, 4))

        # цена
        price_block = tk.Frame(row2, bg=C_BLACK)
        price_block.pack(side="right", padx=(10, 0))
        tk.Label(price_block, text=f"{price} ₽", bg=C_BLACK, fg=C_WHITE,
                 font=(FONT, 14)).pack(side="right")
        tk.Label(price_block, text="Цена:", bg=C_BLACK, fg=C_DIM,
                 font=(FONT, 14)).pack(side="right")

        # ── row3: ссылка ──
        link_frame = tk.Frame(self, bg=C_BLACK)
        link_frame.pack(fill="x")

        self.var_url = tk.StringVar(value=stored.get("url", ""))
        ent_link = tk.Entry(link_frame, textvariable=self.var_url, width=500,
                            bg=C_DARK, fg=C_DIM, relief="flat", bd=0,
                            highlightthickness=0, insertbackground=C_WHITE,
                            selectbackground=C_PRIMARY, selectforeground=C_BLACK,
                            font=(FONT, 13))
        ent_link.pack(side="left", fill="x", ipadx=5, ipady=5)
        self._placeholder(ent_link, PH_LINK)

    # ── placeholder ──

    def _placeholder(self, entry: tk.Entry, text: str):
        default_fg = entry.cget("fg")

        def on_in(e):
            if entry.get() == text and entry.cget("fg") == C_PLACEHOLDER:
                entry.delete(0, tk.END)
                entry.config(fg=default_fg)

        def on_out(e):
            if not entry.get():
                entry.insert(0, text)
                entry.config(fg=C_PLACEHOLDER)

        entry.bind("<FocusIn>", on_in)
        entry.bind("<FocusOut>", on_out)
        if not entry.get():
            entry.insert(0, text)
            entry.config(fg=C_PLACEHOLDER)

    # ── tooltip ──

    def _tooltip(self, widget, text):
        tip = [None]

        def show(e):
            if tip[0] is None:
                t = tk.Toplevel(widget)
                t.wm_overrideredirect(True)
                t.wm_geometry(f"+{e.x_root + 10}+{e.y_root + 10}")
                tk.Label(t, text=text, bg=C_BLACK, fg=C_PRIMARY, relief="solid",
                         bd=0, font=(FONT, 13), padx=5, pady=5,
                         wraplength=300).pack()
                tip[0] = t

        def hide(e):
            if tip[0]:
                tip[0].destroy()
                tip[0] = None

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    # ── данные для сохранения ──

    def get_data(self) -> dict:
        url = self.var_url.get().strip()
        if url == PH_LINK:
            url = ""

        def s_int(v, d=None):
            try:
                return int(v)
            except (ValueError, TypeError):
                return d

        def s_float(v, d=None):
            try:
                return float(v.replace(",", "."))
            except (ValueError, TypeError, AttributeError):
                return d

        return {
            "url": url,
            "min_limit": s_int(self.var_limit.get().strip()),
            "min_sales": s_int(self.var_sales.get().strip(), 0),
            "price_step": s_float(self.var_step.get().strip(), 1.0),
        }