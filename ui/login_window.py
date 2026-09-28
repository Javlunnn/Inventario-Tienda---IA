import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from models.usuario import Usuario
from services.auth_service import AuthService
from ui.theme import ModernTheme


class LoginWindow(tk.Tk):
    """Ventana de inicio de sesión con validación de roles y hash (RF-2, RF-3, A.4)."""

    def __init__(self, on_login_success: Callable[[Usuario], None]):
        super().__init__()
        self.on_login_success = on_login_success
        self.auth_service = AuthService()

        self.title("Sistema Punto de Venta e Inventario - Iniciar Sesión")
        self.geometry("460x540")
        self.resizable(False, False)
        ModernTheme.aplicar(self)

        # Centrar ventana en pantalla
        self._centrar_ventana(460, 640)

        self._crear_widgets()

    def _centrar_ventana(self, ancho: int, alto: int):
        self.update_idletasks()
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()
        x = (pantalla_ancho // 2) - (ancho // 2)
        y = (pantalla_alto // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _crear_widgets(self):
        # Contenedor central
        container = ttk.Frame(self, padding=30)
        container.pack(fill="both", expand=True)

        # Encabezado con Icono/Título
        lbl_icon = ttk.Label(container, text="🏪", font=("Segoe UI Emoji", 40))
        lbl_icon.pack(pady=(0, 5))

        lbl_titulo = ttk.Label(container, text="Punto de Venta e Inventario", style="Header.TLabel")
        lbl_titulo.pack()

        lbl_sub = ttk.Label(
            container,
            text="Control de Existencias y Mostrador",
            style="Muted.TLabel"
        )
        lbl_sub.pack(pady=(2, 20))

        # Tarjeta de formulario
        card = ttk.Frame(container, style="Card.TFrame", padding=20)
        card.pack(fill="x", pady=10)

        # Campo: Usuario
        lbl_user = ttk.Label(card, text="Nombre de Usuario:", font=("Segoe UI", 10, "bold"), style="Card.TLabel")
        lbl_user.pack(anchor="w", pady=(0, 4))
        self.txt_username = ttk.Entry(card, font=("Segoe UI", 11))
        self.txt_username.pack(fill="x", pady=(0, 15))
        self.txt_username.focus_set()

        # Campo: Contraseña
        lbl_pass = ttk.Label(card, text="Contraseña:", font=("Segoe UI", 10, "bold"), style="Card.TLabel")
        lbl_pass.pack(anchor="w", pady=(0, 4))
        self.txt_password = ttk.Entry(card, show="•", font=("Segoe UI", 11))
        self.txt_password.pack(fill="x", pady=(0, 8))

        # Checkbox para mostrar/ocultar contraseña
        self.mostrar_pass_var = tk.BooleanVar(value=False)
        chk_mostrar = ttk.Checkbutton(
            card,
            text="Mostrar contraseña",
            variable=self.mostrar_pass_var,
            command=self._toggle_ver_password
        )
        chk_mostrar.pack(anchor="w", pady=(0, 15))

        # Botón de Ingresar
        btn_ingresar = ttk.Button(
            card,
            text="Iniciar Sesión",
            style="Primary.TButton",
            command=self._intentar_login
        )
        btn_ingresar.pack(fill="x", pady=5)

        # Enlazar tecla Enter para enviar formulario
        self.bind("<Return>", lambda event: self._intentar_login())

        # Mensaje de error visible en pantalla (RNF-4)
        self.lbl_error = ttk.Label(container, text="", foreground=ModernTheme.DANGER, font=("Segoe UI", 9, "bold"))
        self.lbl_error.pack(pady=5)

        # Panel informativo con usuarios de prueba (A.5)
        info_frame = ttk.Frame(container)
        info_frame.pack(fill="x", pady=(15, 0))
        lbl_demo_title = ttk.Label(info_frame, text="Credenciales de Prueba (A.5):", font=("Segoe UI", 8, "bold"), style="Muted.TLabel")
        lbl_demo_title.pack(anchor="w")
        lbl_demo_1 = ttk.Label(info_frame, text="• Admin: admin  /  admin123  (Acceso total)", style="Muted.TLabel")
        lbl_demo_1.pack(anchor="w")
        lbl_demo_2 = ttk.Label(info_frame, text="• Cajero: cajero  /  cajero123  (Operador de ventas)", style="Muted.TLabel")
        lbl_demo_2.pack(anchor="w")

    def _toggle_ver_password(self):
        if self.mostrar_pass_var.get():
            self.txt_password.configure(show="")
        else:
            self.txt_password.configure(show="•")

    def _intentar_login(self):
        username = self.txt_username.get().strip()
        password = self.txt_password.get()

        self.lbl_error.config(text="")

        try:
            usuario = self.auth_service.autenticar(username, password)
            self.destroy()
            self.on_login_success(usuario)
        except ValueError as err:
            self.lbl_error.config(text=str(err))
            messagebox.showwarning("Atención", str(err), parent=self)
        except Exception as ex:
            self.lbl_error.config(text="Error inesperado durante la autenticación.")
            messagebox.showerror("Error", f"Ocurrió un error inesperado:\n{ex}", parent=self)
