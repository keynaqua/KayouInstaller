import ctypes
import ctypes.wintypes
import tkinter as tk


def _window_handle(window: tk.Misc) -> int:
    window.update_idletasks()
    return ctypes.windll.user32.GetParent(window.winfo_id())


def round_window(window: tk.Misc, radius: int = 24) -> None:
    """Clip a borderless Windows window to a real rounded rectangle."""
    if not hasattr(ctypes, "windll"):
        return
    hwnd = _window_handle(window)
    bounds = ctypes.wintypes.RECT()
    if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(bounds)):
        return
    width = bounds.right - bounds.left
    height = bounds.bottom - bounds.top
    region = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, width + 1, height + 1, radius, radius)
    if region:
        # After a successful SetWindowRgn call, Windows owns the region handle.
        if not ctypes.windll.user32.SetWindowRgn(hwnd, region, True):
            ctypes.windll.gdi32.DeleteObject(region)


def clear_window_rounding(window: tk.Misc) -> None:
    if hasattr(ctypes, "windll"):
        ctypes.windll.user32.SetWindowRgn(_window_handle(window), 0, True)


def style_window(window: tk.Toplevel):
    if not hasattr(ctypes, "windll"):
        return
    hwnd = _window_handle(window)
    for attribute, setting in ((20, 1), (33, 3)):
        value = ctypes.c_int(setting)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value))


def center_window(window: tk.Toplevel, parent: tk.Misc, width: int, height: int):
    x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    window.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")
    style_window(window)
