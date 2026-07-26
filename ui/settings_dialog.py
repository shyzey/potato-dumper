"""Диалог настроек — tkinter, стиль 1:1."""

import tkinter as tk
from tkinter import messagebox

from config import (
    C_BLACK, C_DARK, C_PRIMARY, C_PRIMARY_HOVER, C_WHITE,
    FONT, MAX_THREADS, MIN_THREADS, MIN_TIMEOUT,
)


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings: dict, on_save):
        super().__init__(parent)
        self.title("настройки")
        self.configure(bg=C_PRIMARY)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_save = on_save
        self._vars: dict[str, tk.StringVar] = {}

        w, h = 400, 420
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(x, 0)}+{max(y, 0)}")

        self._build(settings)

    def _build(self, settings):
        fields = [
            ("id продавца", "seller_id"),
            ("api ключ", "api_key"),
            ("время обновления (в сек.)", "timeout"),
            ("количество потоков (5-32)", "threads"),
        ]

        for label_text, key in fields:
            frame = tk.Frame(self, bg=C_PRIMARY, pady=5)
            frame.pack(fill="x", padx=20)

            tk.Label(frame, text=label_text, bg=C_PRIMARY, fg=C_BLACK,
                     font=(FONT, 13)).pack(fill="x")

            var = tk.StringVar(value=str(settings.get(key, "")))
            self._vars[key] = var

            tk.Entry(frame, textvariable=var, width=80, bg=C_DARK, fg=C_WHITE,
                     relief="flat", bd=0, highlightthickness=0,
                     insertbackground=C_WHITE, selectbackground=C_PRIMARY,
                     selectforeground=C_BLACK, font=(FONT, 12)).pack(fill="x",
                                                                     ipadx=5, ipady=5)

        btn = tk.Button(self, text="сохранить", bg=C_PRIMARY, fg=C_BLACK,
                        relief="flat", bd=0, highlightthickness=0,
                        activebackground=C_PRIMARY_HOVER, activeforeground=C_WHITE,
                        font=(FONT, 17), padx=10, cursor="hand2",
                        command=self._save)
        btn.pack(pady=20)
        btn.bind("<Enter>", lambda e: btn.config(fg=C_WHITE))
        btn.bind("<Leave>", lambda e: btn.config(fg=C_BLACK))

    def _save(self):
        try:
            seller_id = int(self._vars["seller_id"].get())
            api_key = self._vars["api_key"].get().strip()
            timeout = int(self._vars["timeout"].get())
            threads = int(self._vars["threads"].get())

            if timeout < MIN_TIMEOUT:
                messagebox.showwarning("Ограничение",
                                       f"Минимальное время — {MIN_TIMEOUT} сек.")
                self._vars["timeout"].set(str(MIN_TIMEOUT))
                return

            if not (MIN_THREADS <= threads <= MAX_THREADS):
                messagebox.showwarning("Ограничение",
                                       f"Потоки: от {MIN_THREADS} до {MAX_THREADS}.")
                self._vars["threads"].set(str(MIN_THREADS))
                return

            self.on_save({
                "seller_id": seller_id,
                "api_key": api_key,
                "timeout": timeout,
                "threads": threads,
            })
            self.destroy()

        except ValueError:
            messagebox.showerror("Ошибка",
                                 "ID, время и потоки должны быть числами.")