import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
from models.usuario import Usuario
from ui.theme import ModernTheme
from ui.punto_venta_view import PuntoVentaView
from ui.productos_view import ProductosView
from ui.categorias_view import CategoriasView
from ui.ventas_historial_view import VentasHistorialView
from ui.reportes_view import ReportesView
from ui.usuarios_view import UsuariosView


class MainWindow(tk.Tk):
    """
    Ventana Principal de la Aplicación (A.4, RNF-3).
    Integra menú superior, control de acceso basado en roles (RF-2) y las vistas modulares.
    """

    def __init__(self, usuario_actual: Usuario, on_logout: Callable[[], None]):
        super().__init__()
        self.usuario_actual = usuario_actual
        self.on_logout = on_logout

        self.title(f"Sistema POS e Inventario - [{self.usuario_actual.username.upper()} / {self.usuario_actual.rol.upper()}]")
        self.geometry("1180x760")
        self.minsize(980, 640)

        ModernTheme.aplicar(self)
        self._centrar_ventana(1180, 760)

        self._crear_menu_superior()
        self._crear_encabezado_usuario()
        self._crear_notebook_principal()
        self._crear_barra_estado()

    def _centrar_ventana(self, ancho: int, alto: int):
        self.update_idletasks()
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()
        x = max(0, (pantalla_ancho // 2) - (ancho // 2))
        y = max(0, (pantalla_alto // 2) - (alto // 2) - 30)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _crear_menu_superior(self):
        menubar = tk.Menu(self)

        # Menú Archivo / Sesión
        menu_archivo = tk.Menu(menubar, tearoff=0)
        menu_archivo.add_command(label="Cerrar Sesión", command=self._confirmar_cerrar_sesion, accelerator="Ctrl+Q")
        menu_archivo.add_separator()
        menu_archivo.add_command(label="Salir de la Aplicación", command=self._salir_aplicacion, accelerator="Alt+F4")
        menubar.add_cascade(label="Archivo", menu=menu_archivo)

        # Menú Módulos (Con atajos Ctrl+1 a Ctrl+6)
        menu_modulos = tk.Menu(menubar, tearoff=0)
        menu_modulos.add_command(label="1. Punto de Venta", command=lambda: self.seleccionar_modulo(0), accelerator="Ctrl+1")
        menu_modulos.add_command(label="2. Catálogo de Productos", command=lambda: self.seleccionar_modulo(1), accelerator="Ctrl+2")
        menu_modulos.add_command(label="3. Catálogo de Categorías", command=lambda: self.seleccionar_modulo(2), accelerator="Ctrl+3")
        menu_modulos.add_command(label="4. Movimientos / Ventas (JOIN)", command=lambda: self.seleccionar_modulo(3), accelerator="Ctrl+4")
        menu_modulos.add_command(label="5. Reportes (Stock Bajo)", command=lambda: self.seleccionar_modulo(4), accelerator="Ctrl+5")
        if self.usuario_actual.es_administrador:
            menu_modulos.add_command(label="6. Personal y Auditoría", command=lambda: self.seleccionar_modulo(5), accelerator="Ctrl+6")
        menubar.add_cascade(label="Módulos", menu=menu_modulos)

        # Menú Ayuda
        menu_ayuda = tk.Menu(menubar, tearoff=0)
        menu_ayuda.add_command(label="Acerca de...", command=self._mostrar_acerca_de)
        menubar.add_cascade(label="Ayuda", menu=menu_ayuda)

        self.config(menu=menubar)
        self.bind("<Control-q>", lambda e: self._confirmar_cerrar_sesion())

        # Atajos de teclado para cambio instantáneo de pestañas
        self.bind("<Control-Key-1>", lambda e: self.seleccionar_modulo(0))
        self.bind("<Control-Key-2>", lambda e: self.seleccionar_modulo(1))
        self.bind("<Control-Key-3>", lambda e: self.seleccionar_modulo(2))
        self.bind("<Control-Key-4>", lambda e: self.seleccionar_modulo(3))
        self.bind("<Control-Key-5>", lambda e: self.seleccionar_modulo(4))
        if self.usuario_actual.es_administrador:
            self.bind("<Control-Key-6>", lambda e: self.seleccionar_modulo(5))

    def _crear_encabezado_usuario(self):
        header = ttk.Frame(self, style="Card.TFrame", padding=(15, 10))
        header.pack(fill="x")

        # Logo y Título
        titulo_box = ttk.Frame(header, style="Card.TFrame")
        titulo_box.pack(side="left")

        lbl_app = ttk.Label(
            titulo_box,
            text="🏪 Mini Punto de Venta e Inventario",
            font=("Segoe UI", 13, "bold"),
            foreground=ModernTheme.PRIMARY,
            style="Card.TLabel"
        )
        lbl_app.pack(anchor="w")

        lbl_sub = ttk.Label(
            titulo_box,
            text="Tópicos Avanzados de Programación - Unidad 1",
            font=("Segoe UI", 8),
            style="Muted.TLabel"
        )
        lbl_sub.pack(anchor="w")

        # Información del usuario en sesión
        user_box = ttk.Frame(header, style="Card.TFrame")
        user_box.pack(side="right")

        badge_color = ModernTheme.PRIMARY if self.usuario_actual.es_administrador else ModernTheme.SECONDARY
        rol_texto = "ADMINISTRADOR" if self.usuario_actual.es_administrador else "OPERADOR / CAJERO"

        lbl_user = ttk.Label(
            user_box,
            text=f"👤 Usuario: {self.usuario_actual.username}  |  Rol: {rol_texto}",
            font=("Segoe UI", 10, "bold"),
            foreground=badge_color,
            style="Card.TLabel"
        )
        lbl_user.pack(side="left", padx=(0, 15))

        btn_logout = ttk.Button(
            user_box,
            text="🚪 Cerrar Sesión",
            style="Secondary.TButton",
            command=self._confirmar_cerrar_sesion
        )
        btn_logout.pack(side="right")

    def _crear_notebook_principal(self):
        # Barra de Botones de Navegación Rápida Directa
        nav_bar = ttk.Frame(self, padding=(10, 6, 10, 4))
        nav_bar.pack(fill="x")

        btn_nav1 = ttk.Button(nav_bar, text="🛒 1. Punto de Venta", style="Secondary.TButton", command=lambda: self.seleccionar_modulo(0))
        btn_nav1.pack(side="left", padx=2)

        btn_nav2 = ttk.Button(nav_bar, text="📦 2. Productos", style="Secondary.TButton", command=lambda: self.seleccionar_modulo(1))
        btn_nav2.pack(side="left", padx=2)

        btn_nav3 = ttk.Button(nav_bar, text="📂 3. Categorías", style="Secondary.TButton", command=lambda: self.seleccionar_modulo(2))
        btn_nav3.pack(side="left", padx=2)

        btn_nav4 = ttk.Button(nav_bar, text="🧾 4. Movimientos (JOIN)", style="Secondary.TButton", command=lambda: self.seleccionar_modulo(3))
        btn_nav4.pack(side="left", padx=2)

        btn_nav5 = ttk.Button(nav_bar, text="🚨 5. Reportes (Stock Bajo)", style="Secondary.TButton", command=lambda: self.seleccionar_modulo(4))
        btn_nav5.pack(side="left", padx=2)

        if self.usuario_actual.es_administrador:
            btn_nav6 = ttk.Button(nav_bar, text="👥 6. Personal (Admin)", style="Secondary.TButton", command=lambda: self.seleccionar_modulo(5))
            btn_nav6.pack(side="left", padx=2)

        # Contenedor Notebook con Pestañas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(2, 4))

        # 1. Punto de Venta
        self.tab_pos = PuntoVentaView(self.notebook, self.usuario_actual, on_venta_realizada=self._on_venta_registrada)
        self.notebook.add(self.tab_pos, text=" 🛒 Punto de Venta ")

        # 2. Productos
        self.tab_productos = ProductosView(self.notebook, self.usuario_actual)
        self.notebook.add(self.tab_productos, text=" 📦 Productos ")

        # 3. Categorías
        self.tab_categorias = CategoriasView(self.notebook, self.usuario_actual)
        self.notebook.add(self.tab_categorias, text=" 📂 Categorías ")

        # 4. Historial de Ventas (JOIN)
        self.tab_ventas = VentasHistorialView(self.notebook, self.usuario_actual)
        self.notebook.add(self.tab_ventas, text=" 🧾 Movimientos (JOIN) ")

        # 5. Reportes Analíticos (Stock Bajo)
        self.tab_reportes = ReportesView(self.notebook, self.usuario_actual)
        self.notebook.add(self.tab_reportes, text=" 🚨 Reportes (Stock Bajo) ")

        # 6. Gestión de Usuarios y Auditoría (RF-2: Solo para administradores)
        if self.usuario_actual.es_administrador:
            self.tab_usuarios = UsuariosView(self.notebook, self.usuario_actual)
            self.notebook.add(self.tab_usuarios, text=" 👥 Personal y Auditoría ")

        # Evento al cambiar de pestaña para recargar datos frescos
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def seleccionar_modulo(self, indice: int):
        """Selecciona una pestaña programáticamente por índice de forma segura."""
        tabs = self.notebook.tabs()
        if 0 <= indice < len(tabs):
            self.notebook.select(indice)

    def _crear_barra_estado(self):
        status_bar = ttk.Frame(self, relief="sunken", padding=(10, 4))
        status_bar.pack(fill="x", side="bottom")

        lbl_db = ttk.Label(status_bar, text="🟢 Base de Datos SQLite Conectada (PRAGMA foreign_keys = ON)", font=("Segoe UI", 8))
        lbl_db.pack(side="left")

        lbl_version = ttk.Label(
            status_bar,
            text="Versión 1.0.0 | Opción 2: Inventario / Mini POS",
            font=("Segoe UI", 8),
            style="Muted.TLabel"
        )
        lbl_version.pack(side="right")

    def _on_tab_changed(self, event):
        """Refresca automáticamente las vistas al cambiar de pestaña."""
        pestana_actual = self.notebook.nametowidget(self.notebook.select())
        if hasattr(pestana_actual, "cargar_datos"):
            pestana_actual.cargar_datos()
        elif hasattr(pestana_actual, "recargar_catalogo"):
            pestana_actual.recargar_catalogo()
        elif hasattr(pestana_actual, "actualizar_todo"):
            pestana_actual.actualizar_todo()

    def _on_venta_registrada(self):
        """Callback invocado cuando una venta descuenta inventario."""
        if hasattr(self.tab_productos, "cargar_datos"):
            self.tab_productos.cargar_datos()
        if hasattr(self.tab_ventas, "cargar_datos"):
            self.tab_ventas.cargar_datos()
        if hasattr(self.tab_reportes, "actualizar_todo"):
            self.tab_reportes.actualizar_todo()

    def _confirmar_cerrar_sesion(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Está seguro de que desea cerrar la sesión actual?", parent=self):
            self.destroy()
            self.on_logout()

    def _salir_aplicacion(self):
        if messagebox.askyesno("Salir", "¿Desea cerrar el sistema por completo?", parent=self):
            self.destroy()

    def _mostrar_acerca_de(self):
        info = (
            "🏪 Mini Punto de Venta e Inventario\n"
            "Materia: Tópicos Avanzados de Programación - Unidad 1\n"
            "Opción 2: Inventario / Mini Punto de Venta\n\n"
            "Stack Tecnológico:\n"
            "• Python 3.10+ / Tkinter & ttk\n"
            "• SQLite 3 con Integridad Referencial Activa\n"
            "• Arquitectura en Capas: UI, Modelos, Repositorios, Servicios\n"
            "• Seguridad: Criptografía SHA-256 para contraseñas\n"
            "• Extras: Exportación a CSV, Bitácora de Auditoría y Ejecutable .EXE\n\n"
            "Desarrollado para fines académicos."
        )
        messagebox.showinfo("Acerca del Sistema", info, parent=self)
