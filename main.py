"""Точка входа."""

import ctypes
import os
import sys
import tkinter as tk

# Иконка таскбара
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "potatocorp.potatodumper")
except Exception:
    pass

from config import resource_path  # noqa: E402


def load_font():
    try:
        path = resource_path("assets/Oswald-VariableFont_wght.ttf")
        if os.path.exists(path):
            FR_PRIVATE = 0x10
            FR_NOT_ENUM = 0x20
            buf = ctypes.create_unicode_buffer(path)
            ctypes.windll.gdi32.AddFontResourceExW(buf, FR_PRIVATE | FR_NOT_ENUM, 0)
    except Exception:
        pass


def show_splash(root: tk.Tk):
    splash = tk.Toplevel(root)
    splash.title("Загрузка...")
    splash.geometry("300x100")
    splash.resizable(False, False)
    splash.configure(bg="#adb40c")
    splash.overrideredirect(True)
    splash.update_idletasks()
    x = (splash.winfo_screenwidth() - 300) // 2
    y = (splash.winfo_screenheight() - 100) // 2
    splash.geometry(f"+{x}+{y}")
    tk.Label(splash, text="Запуск программы...", bg="#adb40c", fg="black",
            font=("Oswald", 14)).pack(expand=True)
    return splash


def main():
    load_font()

    root = tk.Tk()
    root.withdraw()

    splash = show_splash(root)
    root.update()

    from ui.app import App  # noqa: E402
    app = App(root)

    splash.destroy()
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()