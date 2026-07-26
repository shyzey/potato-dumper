"""Главное окно — tkinter, стиль 1:1 из оригинала."""

import threading
import time
import webbrowser
import tkinter as tk
from tkinter import ttk

from config import (
    C_BLACK, C_DARK, C_PRIMARY, C_PRIMARY_DARK, C_PRIMARY_HOVER,
    C_WHITE, FONT, CURRENT_VERSION, APP_NAME,
    LINKS_FILE, SETTINGS_FILE, DEFAULT_SETTINGS, resource_path,
)
from engine import DumpEngine
from utils import atomic_json_write, load_json, write_log_line
from .product_card import ProductCard
from .settings_dialog import SettingsDialog


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_NAME}. v{CURRENT_VERSION}")
        self.root.geometry("850x769")
        self.root.minsize(850, 600)
        self.root.configure(bg=C_PRIMARY)

        # ── Иконка ──
        try:
            self._icon = tk.PhotoImage(file=resource_path("assets/icon.png"))
            self.root.iconphoto(True, self._icon)
        except Exception:
            pass

        # ── Данные ──
        self.settings: dict = {**DEFAULT_SETTINGS, **load_json(SETTINGS_FILE)}
        self.links_data: dict = load_json(LINKS_FILE, {})
        self.cards: dict[str, ProductCard] = {}

        # ── Движок ──
        self.engine = DumpEngine(
            settings=self.settings,
            log_fn=self._log_safe,
            ui_callback=self._engine_event,
        )

        # ── UI ──
        self._build_controls()
        self._build_main()
        self._build_log()

        self._log("Программа готова к работе...")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Автозагрузка товаров при старте
        self.root.after(100, self._manual_refresh)

    # ══════════════════════════════════════════
    # Верхняя панель
    # ══════════════════════════════════════════

    def _build_controls(self):
        controls = tk.Frame(self.root, bg=C_PRIMARY, padx=5, pady=5)
        controls.pack(fill="x")

        # QR
        try:
            self._qr_normal = tk.PhotoImage(file=resource_path("assets/qr-code.png"))
            self._qr_hover = tk.PhotoImage(file=resource_path("assets/qr-code-hover.png"))
            self._qr_normal = self._qr_normal.subsample(40, 40)
            self._qr_hover = self._qr_hover.subsample(40, 40)

            qr_label = tk.Label(controls, image=self._qr_normal, cursor="hand2",
                                bg=C_PRIMARY)
            qr_label.pack(side="left")
            qr_label.bind("<Enter>", lambda e: qr_label.config(image=self._qr_hover))
            qr_label.bind("<Leave>", lambda e: qr_label.config(image=self._qr_normal))
            qr_label.bind("<Button-1>", lambda e: webbrowser.open("https://barabanov.digital/"))
        except Exception:
            pass

        # Старт
        self.btn_start = tk.Button(
            controls, text="старт", bg=C_PRIMARY, fg=C_BLACK,
            relief="flat", bd=0, highlightthickness=0,
            activebackground=C_PRIMARY_HOVER, activeforeground=C_WHITE,
            font=(FONT, 17), padx=10, cursor="hand2",
            command=self._toggle,
        )
        self.btn_start.pack(side="left", padx=(5, 0))
        self.btn_start.bind("<Enter>", lambda e: self.btn_start.config(fg=C_WHITE))
        self.btn_start.bind("<Leave>", lambda e: self.btn_start.config(fg=C_BLACK))

        # Настройки
        btn_settings = tk.Button(
            controls, text="настройки", bg=C_PRIMARY, fg=C_BLACK,
            relief="flat", bd=0, highlightthickness=0,
            activebackground=C_PRIMARY_HOVER, activeforeground=C_WHITE,
            font=(FONT, 17), padx=10, cursor="hand2",
            command=self._open_settings,
        )
        btn_settings.pack(side="left", padx=(5, 0))
        btn_settings.bind("<Enter>", lambda e: btn_settings.config(fg=C_WHITE))
        btn_settings.bind("<Leave>", lambda e: btn_settings.config(fg=C_BLACK))

        # Обновить товары
        btn_refresh = tk.Button(
            controls, text="⭯", bg=C_PRIMARY, fg=C_BLACK,
            relief="flat", bd=0, highlightthickness=0,
            activebackground=C_PRIMARY_HOVER, activeforeground=C_WHITE,
            font=(FONT, 17), padx=10, cursor="hand2",
            command=self._manual_refresh,
        )
        btn_refresh.pack(side="left", padx=(5, 0))
        btn_refresh.bind("<Enter>", lambda e: btn_refresh.config(fg=C_WHITE))
        btn_refresh.bind("<Leave>", lambda e: btn_refresh.config(fg=C_BLACK))

        # Разделители
        tk.Frame(self.root, bg=C_BLACK, height=5).pack(fill="x")
        tk.Frame(self.root, bg=C_PRIMARY, height=5).pack(fill="x")

    # ══════════════════════════════════════════
    # Область товаров (Canvas + Scrollbar)
    # ══════════════════════════════════════════

    def _build_main(self):
        self.main_frame = tk.Frame(self.root, bg=C_PRIMARY, bd=0, highlightthickness=0)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbar style
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Custom.Vertical.TScrollbar",
            troughcolor=C_DARK, background=C_BLACK, bordercolor=C_PRIMARY,
            relief="flat", troughrelief="flat", borderwidth=0, width=12,
        )
        style.layout("Custom.Vertical.TScrollbar", [
            ("Vertical.Scrollbar.trough", {
                "children": [("Vertical.Scrollbar.thumb",
                              {"unit": "1", "sticky": "nswe"})],
                "sticky": "nswe",
            })]
        )
        style.map("Custom.Vertical.TScrollbar", background=[("active", C_BLACK)])

        self.canvas = tk.Canvas(self.main_frame, bg=C_PRIMARY, bd=0,
                                highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical",
                                       command=self.canvas.yview,
                                       style="Custom.Vertical.TScrollbar")
        self.scrollbar.pack(side="right", fill="y")
        self.scrollbar.bind("<Enter>", lambda e: self.scrollbar.config(cursor="hand2"))
        self.scrollbar.bind("<Leave>", lambda e: self.scrollbar.config(cursor=""))

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.container = tk.Frame(self.canvas, bg=C_PRIMARY, padx=5)
        self.window_id = self.canvas.create_window((0, 0), window=self.container,
                                                   anchor="nw")

        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(self.window_id, width=e.width))
        self.container.bind("<Configure>",
                            lambda e: self.canvas.configure(
                                scrollregion=self.canvas.bbox("all")))

        # Mousewheel
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._wheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _wheel(self, event):
        region = self.canvas.bbox("all")
        if not region:
            return
        if region[3] <= self.canvas.winfo_height():
            return
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ══════════════════════════════════════════
    # Лог (консоль)
    # ══════════════════════════════════════════

    def _build_log(self):
        tk.Frame(self.root, bg=C_PRIMARY, height=5).pack(fill="x")

        log_frame = tk.Frame(self.root, bg=C_BLACK, bd=0, highlightthickness=0)
        log_frame.pack(side="bottom", fill="x")

        self.console = tk.Text(
            log_frame, bg=C_BLACK, fg=C_PRIMARY, relief="flat", bd=0,
            highlightthickness=0, insertbackground=C_WHITE,
            selectbackground=C_PRIMARY, selectforeground=C_BLACK,
            font=(FONT, 13), height=7, padx=8, pady=8,
        )
        self.console.pack(side="left", fill="both", expand=True)
        self.console.configure(state="disabled")

        sb = ttk.Scrollbar(log_frame, orient="vertical", command=self.console.yview,
                           style="Custom.Vertical.TScrollbar")
        sb.pack(side="right", fill="y")
        sb.bind("<Enter>", lambda e: sb.config(cursor="hand2"))
        sb.bind("<Leave>", lambda e: sb.config(cursor=""))
        self.console.configure(yscrollcommand=sb.set)

        # Mousewheel для консоли
        self.console.bind("<Enter>",
                          lambda e: self.console.bind_all("<MouseWheel>", self._wheel_console))
        self.console.bind("<Leave>",
                          lambda e: self.console.unbind_all("<MouseWheel>"))

    def _wheel_console(self, event):
        self.console.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ══════════════════════════════════════════
    # Рендер карточек
    # ══════════════════════════════════════════

    def _render_products(self, products: list[dict]):
        for w in self.container.winfo_children():
            w.destroy()
        self.cards.clear()

        for p in products:
            pid = str(p.get("id_goods"))
            stored = self.links_data.get(pid, {})
            if isinstance(stored, str):
                stored = {"url": stored}

            card = ProductCard(self.container, p, stored)
            card.pack(fill="x", pady=(0, 5))
            self.cards[pid] = card

    # ══════════════════════════════════════════
    # Логика
    # ══════════════════════════════════════════

    def _toggle(self):
        if self.engine.running:
            self.engine.stop()
            self.btn_start.config(text="старт", bg=C_PRIMARY)
            self._log("Программа остановлена.")
        else:
            self._save_links()
            self.engine.settings = self.settings
            self.engine.start()
            self.btn_start.config(text="стоп", bg=C_PRIMARY_DARK)
            self._log("Программа запущена.")

    def _manual_refresh(self):
        self._save_links()
        threading.Thread(target=self._do_refresh, daemon=True).start()

    def _do_refresh(self):
        from api.digiseller import DigisellerAPI
        try:
            api = DigisellerAPI(self.engine.session,
                                self.settings["seller_id"],
                                self.settings["api_key"])
            products, _ = api.get_products()
            products = [p for p in products if p.get("in_stock") != 0]
            self.root.after(0, self._render_products, products)
            self._log_safe(f"Загружено товаров: {len(products)}")
        except Exception as e:
            self._log_safe(f"Ошибка загрузки: {e}")

    def _open_settings(self):
        SettingsDialog(self.root, self.settings, self._apply_settings)

    def _apply_settings(self, new: dict):
        self.settings.update(new)
        atomic_json_write(SETTINGS_FILE, self.settings)
        self.engine.settings = self.settings
        self._log(f"Настройки сохранены. Интервал: {new['timeout']}с, потоков: {new['threads']}")

    # ══════════════════════════════════════════
    # Сохранение ссылок
    # ══════════════════════════════════════════

    def _save_links(self):
        if not self.cards:
            return  # нечего сохранять — не трогаем файл
        data = dict(self.links_data)  # начинаем с того что уже есть
        for pid, card in self.cards.items():
            data[pid] = card.get_data()
        atomic_json_write(LINKS_FILE, data)
        self.links_data = data

    # ══════════════════════════════════════════
    # Колбэки движка (поток → main thread)
    # ══════════════════════════════════════════

    def _engine_event(self, event: str, data):
        self.root.after(0, self._handle_event, event, data)

    def _handle_event(self, event: str, data):
        if event == "products_loaded":
            self._render_products(data)

    # ══════════════════════════════════════════
    # Лог
    # ══════════════════════════════════════════

    def _log(self, message: str):
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {message}\n"
        self.console.configure(state="normal")
        self.console.insert(tk.END, line)
        self.console.see(tk.END)
        self.console.configure(state="disabled")
        write_log_line(message)

    def _log_safe(self, message: str):
        self.root.after(0, self._log, message)

    # ══════════════════════════════════════════
    # Закрытие
    # ══════════════════════════════════════════

    def _on_close(self):
        self.engine.shutdown()
        self._save_links()
        self.root.destroy()