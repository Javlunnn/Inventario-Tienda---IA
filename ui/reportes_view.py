import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List
from models.usuario import Usuario
from services.reporte_service import ReporteService
from ui.theme import ModernTheme


class ReportesView(ttk.Frame):
    """
    Vista de Reportes Analíticos del Dominio.
    Cumple con RF-8 (Caso Problemático: Stock Bajo) y Extra A.6 (Exportar a CSV).
    """

    def __init__(self, parent, usuario_actual: Usuario):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.service = ReporteService()

        self._crear_interfaz()
        self.actualizar_todo()

    def _crear_interfaz(self):
        # 1. Panel de Tarjetas KPI Superiores
        kpi_frame = ttk.Frame(self, padding=(10, 10, 10, 5))
        kpi_frame.pack(fill="x")

        # Tarjeta 1: Total Almacén
        card1 = ttk.Frame(kpi_frame, style="Card.TFrame", padding=12)
        card1.pack(side="left", fill="both", expand=True, padx=4)
        ttk.Label(card1, text="📦 Catálogo Activo", style="Card.TLabel", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.lbl_kpi_prods = ttk.Label(card1, text="0 productos", font=("Segoe UI", 13, "bold"), foreground=ModernTheme.PRIMARY, style="Card.TLabel")
        self.lbl_kpi_prods.pack(anchor="w", pady=(2, 0))

        # Tarjeta 2: Valor Inventario
        card2 = ttk.Frame(kpi_frame, style="Card.TFrame", padding=12)
        card2.pack(side="left", fill="both", expand=True, padx=4)
        ttk.Label(card2, text="💰 Valor de Almacén", style="Card.TLabel", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.lbl_kpi_valor = ttk.Label(card2, text="$0.00", font=("Segoe UI", 13, "bold"), foreground=ModernTheme.PRIMARY_DARK, style="Card.TLabel")
        self.lbl_kpi_valor.pack(anchor="w", pady=(2, 0))

        # Tarjeta 3: CASO PROBLEMÁTICO (Stock Crítico)
        card3 = ttk.Frame(kpi_frame, style="Card.TFrame", padding=12)
        card3.pack(side="left", fill="both", expand=True, padx=4)
        ttk.Label(card3, text="⚠️ Stock Crítico (≤ 5)", style="Card.TLabel", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.lbl_kpi_bajos = ttk.Label(card3, text="0 alertas", font=("Segoe UI", 13, "bold"), foreground=ModernTheme.DANGER, style="Card.TLabel")
        self.lbl_kpi_bajos.pack(anchor="w", pady=(2, 0))

        # Tarjeta 4: Ventas Totales
        card4 = ttk.Frame(kpi_frame, style="Card.TFrame", padding=12)
        card4.pack(side="left", fill="both", expand=True, padx=4)
        ttk.Label(card4, text="📈 Ventas Acumuladas", style="Card.TLabel", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.lbl_kpi_ventas = ttk.Label(card4, text="$0.00", font=("Segoe UI", 13, "bold"), foreground=ModernTheme.SUCCESS, style="Card.TLabel")
        self.lbl_kpi_ventas.pack(anchor="w", pady=(2, 0))

        # 2. Pestañas de Reportes Detallados
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: REPORTE DE STOCK BAJO (RF-8)
        tab_stock = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(tab_stock, text="🚨 Reporte de Stock Bajo (Caso Problemático RF-8)")
        self._crear_tab_stock_bajo(tab_stock)

        # Tab 2: REPORTE DE MÁS VENDIDOS
        tab_top = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(tab_top, text="🏆 Productos Más Vendidos")
        self._crear_tab_mas_vendidos(tab_top)

    def _crear_tab_stock_bajo(self, parent):
        # Barra de control de umbral y botón exportar
        ctrl_frame = ttk.Frame(parent)
        ctrl_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(ctrl_frame, text="Umbral de Stock Máximo:").pack(side="left", padx=(0, 5))
        self.spin_umbral = ttk.Spinbox(ctrl_frame, from_=1, to=50, width=6, font=("Segoe UI", 10))
        self.spin_umbral.set(5)
        self.spin_umbral.pack(side="left", padx=5)

        btn_actualizar = ttk.Button(ctrl_frame, text="🔄 Filtrar", style="Secondary.TButton", command=self.cargar_reporte_stock_bajo)
        btn_actualizar.pack(side="left", padx=5)

        btn_csv_stock = ttk.Button(
            ctrl_frame,
            text="📥 Exportar Stock Bajo a CSV",
            style="Primary.TButton",
            command=self._exportar_stock_bajo_csv
        )
        btn_csv_stock.pack(side="right")

        # Treeview de Stock Bajo
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)

        cols = ("codigo", "nombre", "categoria", "precio", "stock", "alerta")
        self.tree_stock = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        self.tree_stock.heading("codigo", text="Código")
        self.tree_stock.heading("nombre", text="Producto")
        self.tree_stock.heading("categoria", text="Categoría")
        self.tree_stock.heading("precio", text="Precio Venta")
        self.tree_stock.heading("stock", text="Stock Disponible")
        self.tree_stock.heading("alerta", text="Nivel de Alerta")

        self.tree_stock.column("codigo", width=100, anchor="center")
        self.tree_stock.column("nombre", width=280, anchor="w")
        self.tree_stock.column("categoria", width=180, anchor="w")
        self.tree_stock.column("precio", width=100, anchor="e")
        self.tree_stock.column("stock", width=110, anchor="center")
        self.tree_stock.column("alerta", width=160, anchor="center")

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_stock.yview)
        self.tree_stock.configure(yscrollcommand=scroll.set)

        self.tree_stock.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.tree_stock.tag_configure("agotado", background="#fee2e2", foreground="#991b1b") # Rojo
        self.tree_stock.tag_configure("bajo", background="#fef3c7", foreground="#92400e")     # Amarillo/Ámbar

    def _crear_tab_mas_vendidos(self, parent):
        ctrl_frame = ttk.Frame(parent)
        ctrl_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(ctrl_frame, text="Productos con mayor rotación y volumen de ventas histórico.").pack(side="left")

        btn_csv_top = ttk.Button(
            ctrl_frame,
            text="📥 Exportar Más Vendidos a CSV",
            style="Primary.TButton",
            command=self._exportar_mas_vendidos_csv
        )
        btn_csv_top.pack(side="right")

        # Treeview de Más Vendidos
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)

        cols = ("ranking", "codigo", "nombre", "categoria", "unidades", "monto")
        self.tree_top = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        self.tree_top.heading("ranking", text="Lugar")
        self.tree_top.heading("codigo", text="Código")
        self.tree_top.heading("nombre", text="Producto")
        self.tree_top.heading("categoria", text="Categoría")
        self.tree_top.heading("unidades", text="Piezas Vendidas")
        self.tree_top.heading("monto", text="Monto Acumulado ($)")

        self.tree_top.column("ranking", width=60, anchor="center")
        self.tree_top.column("codigo", width=110, anchor="center")
        self.tree_top.column("nombre", width=280, anchor="w")
        self.tree_top.column("categoria", width=180, anchor="w")
        self.tree_top.column("unidades", width=120, anchor="center")
        self.tree_top.column("monto", width=140, anchor="e")

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_top.yview)
        self.tree_top.configure(yscrollcommand=scroll.set)

        self.tree_top.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def actualizar_todo(self):
        """Actualiza KPIs y todas las pestañas de reportes."""
        self._cargar_kpis()
        self.cargar_reporte_stock_bajo()
        self.cargar_reporte_mas_vendidos()

    def _cargar_kpis(self):
        kpis = self.service.obtener_resumen_kpi()
        self.lbl_kpi_prods.config(text=f"{kpis['total_productos']} prods. ({kpis['total_unidades']} pz)")
        self.lbl_kpi_valor.config(text=f"${kpis['valor_almacen']:,.2f}")
        self.lbl_kpi_bajos.config(text=f"{kpis['stock_bajo_count']} en alerta")
        self.lbl_kpi_ventas.config(text=f"${kpis['recaudacion_total']:,.2f} ({kpis['total_ventas']} tickets)")

    def cargar_reporte_stock_bajo(self):
        try:
            umbral = int(self.spin_umbral.get())
        except ValueError:
            umbral = 5

        for item in self.tree_stock.get_children():
            self.tree_stock.delete(item)

        items = self.service.reporte_stock_bajo(umbral=umbral)
        for it in items:
            tag = "agotado" if it["stock"] == 0 else "bajo"
            self.tree_stock.insert(
                "",
                "end",
                values=(it["codigo"], it["nombre"], it["categoria"], it["precio"], it["stock"], it["alerta"]),
                tags=(tag,)
            )

    def cargar_reporte_mas_vendidos(self):
        for item in self.tree_top.get_children():
            self.tree_top.delete(item)

        items = self.service.reporte_mas_vendidos(limite=20)
        for idx, it in enumerate(items, start=1):
            self.tree_top.insert(
                "",
                "end",
                values=(
                    f"#{idx}",
                    it["codigo"],
                    it["nombre"],
                    it["categoria_nombre"],
                    f"{it['total_unidades']} pz",
                    f"${it['monto_generado']:.2f}"
                )
            )

    def _exportar_stock_bajo_csv(self):
        try:
            umbral = int(self.spin_umbral.get())
        except ValueError:
            umbral = 5

        items = self.service.reporte_stock_bajo(umbral=umbral)
        if not items:
            messagebox.showinfo("Exportar", "No hay registros de stock bajo en este momento.", parent=self)
            return

        archivo = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar Reporte de Stock Bajo en CSV",
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv")]
        )
        if not archivo:
            return

        encabezados = ["Código", "Producto", "Categoría", "Precio", "Stock", "Alerta"]
        filas = [
            [it["codigo"], it["nombre"], it["categoria"], it["precio"], it["stock"], it["alerta"]]
            for it in items
        ]

        try:
            self.service.exportar_a_csv(archivo, encabezados, filas)
            messagebox.showinfo("Exportación Exitosa", f"Archivo generado:\n{archivo}", parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{ex}", parent=self)

    def _exportar_mas_vendidos_csv(self):
        items = self.service.reporte_mas_vendidos(limite=50)
        if not items:
            messagebox.showinfo("Exportar", "No hay ventas registradas aún.", parent=self)
            return

        archivo = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar Reporte de Más Vendidos en CSV",
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv")]
        )
        if not archivo:
            return

        encabezados = ["Ranking", "Código", "Producto", "Categoría", "Piezas Vendidas", "Monto Generado"]
        filas = [
            [f"#{idx}", it["codigo"], it["nombre"], it["categoria_nombre"], it["total_unidades"], f"{it['monto_generado']:.2f}"]
            for idx, it in enumerate(items, start=1)
        ]

        try:
            self.service.exportar_a_csv(archivo, encabezados, filas)
            messagebox.showinfo("Exportación Exitosa", f"Archivo generado:\n{archivo}", parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"No se pudo exportar:\n{ex}", parent=self)
