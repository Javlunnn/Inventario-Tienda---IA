import tkinter as tk
from tkinter import ttk


class ModernTheme:
    """Configuración de estilos, paleta de colores y fuentes para la interfaz."""

    # Paleta de colores profesional
    PRIMARY = "#1e3a8a"       # Azul marino corporativo
    PRIMARY_DARK = "#172554"  # Azul muy oscuro
    PRIMARY_LIGHT = "#3b82f6" # Azul vibrante
    SECONDARY = "#0f766e"     # Verde azulado elegante
    ACCENT = "#f59e0b"        # Ámbar / Dorado
    SUCCESS = "#10b981"       # Verde esmeralda
    DANGER = "#ef4444"        # Rojo alerta
    WARNING = "#f97316"       # Naranja
    BG_LIGHT = "#f8fafc"      # Fondo claro suave
    BG_CARD = "#ffffff"       # Blanco tarjeta
    TEXT_MAIN = "#0f172a"     # Slate casi negro
    TEXT_MUTED = "#64748b"    # Gris texto secundario
    BORDER = "#cbd5e1"        # Borde sutil

    @classmethod
    def aplicar(cls, root: tk.Tk):
        """Aplica estilos globales de ttk."""
        style = ttk.Style(root)

        # Seleccionar tema base disponible (clam suele ser el más personalizable)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        # Configuración general
        root.configure(bg=cls.BG_LIGHT)

        # Fuentes
        font_base = ("Segoe UI", 10)
        font_bold = ("Segoe UI", 10, "bold")
        font_header = ("Segoe UI", 14, "bold")
        font_title = ("Segoe UI", 18, "bold")

        # Estilo para Frames
        style.configure("TFrame", background=cls.BG_LIGHT)
        style.configure("Card.TFrame", background=cls.BG_CARD, relief="ridge", borderwidth=1)

        # Estilo para Labels
        style.configure("TLabel", background=cls.BG_LIGHT, foreground=cls.TEXT_MAIN, font=font_base)
        style.configure("Card.TLabel", background=cls.BG_CARD, foreground=cls.TEXT_MAIN, font=font_base)
        style.configure("Header.TLabel", font=font_header, foreground=cls.PRIMARY, background=cls.BG_LIGHT)
        style.configure("Title.TLabel", font=font_title, foreground=cls.PRIMARY_DARK, background=cls.BG_LIGHT)
        style.configure("Muted.TLabel", foreground=cls.TEXT_MUTED, font=("Segoe UI", 9))

        # Estilo para Botones
        style.configure(
            "Primary.TButton",
            font=font_bold,
            background=cls.PRIMARY,
            foreground="#ffffff",
            borderwidth=0,
            padding=(12, 6)
        )
        style.map(
            "Primary.TButton",
            background=[("active", cls.PRIMARY_LIGHT), ("disabled", cls.BORDER)],
            foreground=[("disabled", cls.TEXT_MUTED)]
        )

        style.configure(
            "Success.TButton",
            font=font_bold,
            background=cls.SUCCESS,
            foreground="#ffffff",
            borderwidth=0,
            padding=(12, 6)
        )
        style.map("Success.TButton", background=[("active", "#059669")])

        style.configure(
            "Danger.TButton",
            font=font_bold,
            background=cls.DANGER,
            foreground="#ffffff",
            borderwidth=0,
            padding=(10, 5)
        )
        style.map("Danger.TButton", background=[("active", "#dc2626")])

        style.configure(
            "Secondary.TButton",
            font=font_base,
            background="#e2e8f0",
            foreground=cls.TEXT_MAIN,
            borderwidth=1,
            padding=(10, 5)
        )
        style.map("Secondary.TButton", background=[("active", "#cbd5e1")])

        # Estilos para Treeview
        style.configure(
            "Treeview",
            background="#ffffff",
            foreground=cls.TEXT_MAIN,
            rowheight=28,
            fieldbackground="#ffffff",
            font=font_base
        )
        style.configure(
            "Treeview.Heading",
            font=font_bold,
            background="#e2e8f0",
            foreground=cls.PRIMARY_DARK,
            relief="flat",
            padding=(6, 6)
        )
        style.map("Treeview.Heading", background=[("active", "#cbd5e1")])
        style.map("Treeview", background=[("selected", cls.PRIMARY_LIGHT)], foreground=[("selected", "#ffffff")])

        # Estilos para Entry y Combobox
        style.configure("TEntry", padding=5, font=font_base)
        style.configure("TCombobox", padding=5, font=font_base)

        # Estilos para Notebook (Pestañas)
        style.configure("TNotebook", background=cls.BG_LIGHT, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            font=font_bold,
            padding=(18, 10),
            background="#e2e8f0",
            foreground=cls.TEXT_MAIN
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", cls.PRIMARY), ("active", "#cbd5e1")],
            foreground=[("selected", "#ffffff"), ("active", cls.PRIMARY_DARK)]
        )
