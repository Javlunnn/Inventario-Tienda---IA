import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional
from models.usuario import Usuario
from services.venta_service import VentaService
from services.reporte_service import ReporteService
from ui.theme import ModernTheme


class VentasHistorialView(ttk.Frame):
    """
    Vista de Historial de Ventas y Movimientos con consulta JOIN obligatoria (RF-7).
    Permite visualizar la cabecera y el desglose de productos vendidos por transacción.
    """

    def __init__(self, parent, usuario_actual: Usuario):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.venta_service = VentaService()
        self.reporte_service = ReporteService()

        self._crear_interfaz()
        self.cargar_datos()

    def _crear_interfaz(self):
        # 1. Barra Superior con Título, Buscador y Botón CSV
        top_bar = ttk.Frame(self, padding=(10, 10, 10, 5))
        top_bar.pack(fill="x")

        lbl_titulo = ttk.Label(top_bar, text="Movimientos de Venta (Consulta Relacional con JOIN)", style="Header.TLabel")
        lbl_titulo.pack(side="left")

        actions_box = ttk.Frame(top_bar)
        actions_box.pack(side="right")

        ttk.Label(actions_box, text="Buscar (Folio/Cajero):").pack(side="left", padx=5)
        self.txt_buscar = ttk.Entry(actions_box, width=22)
        self.txt_buscar.pack(side="left", padx=5)
        self.txt_buscar.bind("<KeyRelease>", lambda e: self.cargar_datos())

        btn_limpiar = ttk.Button(actions_box, text="✖", width=3, style="Secondary.TButton", command=self._limpiar_filtro)
        btn_limpiar.pack(side="left", padx=2)

        btn_exportar = ttk.Button(
            actions_box,
            text="📥 Exportar CSV",
            style="Primary.TButton",
            command=self._exportar_csv_movimientos
        )
        btn_exportar.pack(side="left", padx=(10, 0))

        # 2. Pestañas para ver o la vista Maestro-Detalle o el JOIN Plano
        self.sub_notebook = ttk.Notebook(self)
        self.sub_notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Tab 1: Maestro - Detalle
        tab_maestro = ttk.Frame(self.sub_notebook, padding=5)
        self.sub_notebook.add(tab_maestro, text="🧾 Ventas y Detalle por Transacción")
        self._crear_tab_maestro_detalle(tab_maestro)

        # Tab 2: JOIN Plano Completo
        tab_join = ttk.Frame(self.sub_notebook, padding=5)
        self.sub_notebook.add(tab_join, text="🔗 Vista SQL JOIN (Obligatorio RF-7)")
        self._crear_tab_join_plano(tab_join)

    def _crear_tab_maestro_detalle(self, parent):
        paned = ttk.PanedWindow(parent, orient="vertical")
        paned.pack(fill="both", expand=True)

        # Parte Superior: Listado de Ventas
        ventas_frame = ttk.Frame(paned)
        paned.add(ventas_frame, weight=1)

        ttk.Label(ventas_frame, text="Ventas Realizadas (Seleccione una para ver sus productos):", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))

        v_cols = ("folio", "fecha", "cajero", "piezas", "total", "notas")
        self.tree_ventas = ttk.Treeview(ventas_frame, columns=v_cols, show="headings", selectmode="browse", height=7)
        self.tree_ventas.heading("folio", text="Folio")
        self.tree_ventas.heading("fecha", text="Fecha y Hora")
        self.tree_ventas.heading("cajero", text="Usuario / Cajero")
        self.tree_ventas.heading("piezas", text="Total Piezas")
        self.tree_ventas.heading("total", text="Monto Total")
        self.tree_ventas.heading("notas", text="Notas / Método")

        self.tree_ventas.column("folio", width=150, anchor="center")
        self.tree_ventas.column("fecha", width=160, anchor="center")
        self.tree_ventas.column("cajero", width=120, anchor="w")
        self.tree_ventas.column("piezas", width=90, anchor="center")
        self.tree_ventas.column("total", width=110, anchor="e")
        self.tree_ventas.column("notas", width=250, anchor="w")

        v_scroll = ttk.Scrollbar(ventas_frame, orient="vertical", command=self.tree_ventas.yview)
        self.tree_ventas.configure(yscrollcommand=v_scroll.set)

        self.tree_ventas.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")

        self.tree_ventas.bind("<<TreeviewSelect>>", self._on_venta_seleccionada)

        # Parte Inferior: Desglose de Productos
        detalle_frame = ttk.Frame(paned)
        paned.add(detalle_frame, weight=1)

        self.lbl_detalle_titulo = ttk.Label(detalle_frame, text="Desglose de Artículos de la Venta:", font=("Segoe UI", 10, "bold"))
        self.lbl_detalle_titulo.pack(anchor="w", pady=(8, 4))

        d_cols = ("codigo", "nombre", "categoria", "cantidad", "precio_unit", "subtotal")
        self.tree_detalles = ttk.Treeview(detalle_frame, columns=d_cols, show="headings", selectmode="browse", height=6)
        self.tree_detalles.heading("codigo", text="Código")
        self.tree_detalles.heading("nombre", text="Artículo")
        self.tree_detalles.heading("categoria", text="Categoría")
        self.tree_detalles.heading("cantidad", text="Cantidad")
        self.tree_detalles.heading("precio_unit", text="Precio Unitario (Congelado)")
        self.tree_detalles.heading("subtotal", text="Subtotal")

        self.tree_detalles.column("codigo", width=100, anchor="center")
        self.tree_detalles.column("nombre", width=240, anchor="w")
        self.tree_detalles.column("categoria", width=160, anchor="w")
        self.tree_detalles.column("cantidad", width=80, anchor="center")
        self.tree_detalles.column("precio_unit", width=160, anchor="e")
        self.tree_detalles.column("subtotal", width=110, anchor="e")

        d_scroll = ttk.Scrollbar(detalle_frame, orient="vertical", command=self.tree_detalles.yview)
        self.tree_detalles.configure(yscrollcommand=d_scroll.set)

        self.tree_detalles.pack(side="left", fill="both", expand=True)
        d_scroll.pack(side="right", fill="y")

    def _crear_tab_join_plano(self, parent):
        lbl_info = ttk.Label(
            parent,
            text="Consulta SQL ejecutada: SELECT detalle_venta JOIN ventas JOIN usuarios_sistema JOIN productos JOIN categorias",
            font=("Segoe UI", 9, "italic"),
            foreground=ModernTheme.PRIMARY
        )
        lbl_info.pack(anchor="w", pady=(0, 6))

        frame_join = ttk.Frame(parent)
        frame_join.pack(fill="both", expand=True)

        j_cols = ("folio", "fecha", "cajero", "codigo", "producto", "categoria", "cant", "precio", "subtotal")
        self.tree_join = ttk.Treeview(frame_join, columns=j_cols, show="headings", selectmode="browse")

        self.tree_join.heading("folio", text="Folio")
        self.tree_join.heading("fecha", text="Fecha")
        self.tree_join.heading("cajero", text="Cajero")
        self.tree_join.heading("codigo", text="Cód. Prod.")
        self.tree_join.heading("producto", text="Producto Vendido")
        self.tree_join.heading("categoria", text="Categoría")
        self.tree_join.heading("cant", text="Cant.")
        self.tree_join.heading("precio", text="P. Unit.")
        self.tree_join.heading("subtotal", text="Subtotal")

        self.tree_join.column("folio", width=130, anchor="center")
        self.tree_join.column("fecha", width=140, anchor="center")
        self.tree_join.column("cajero", width=100, anchor="w")
        self.tree_join.column("codigo", width=90, anchor="center")
        self.tree_join.column("producto", width=200, anchor="w")
        self.tree_join.column("categoria", width=140, anchor="w")
        self.tree_join.column("cant", width=60, anchor="center")
        self.tree_join.column("precio", width=80, anchor="e")
        self.tree_join.column("subtotal", width=90, anchor="e")

        j_scroll_y = ttk.Scrollbar(frame_join, orient="vertical", command=self.tree_join.yview)
        j_scroll_x = ttk.Scrollbar(frame_join, orient="horizontal", command=self.tree_join.xview)
        self.tree_join.configure(yscrollcommand=j_scroll_y.set, xscrollcommand=j_scroll_x.set)

        self.tree_join.grid(row=0, column=0, sticky="nsew")
        j_scroll_y.grid(row=0, column=1, sticky="ns")
        j_scroll_x.grid(row=1, column=0, sticky="ew")

        frame_join.grid_rowconfigure(0, weight=1)
        frame_join.grid_columnconfigure(0, weight=1)

    def _limpiar_filtro(self):
        self.txt_buscar.delete(0, tk.END)
        self.cargar_datos()

    def cargar_datos(self):
        termino = self.txt_buscar.get().strip()

        # 1. Cargar Ventas en Tab Maestro
        for item in self.tree_ventas.get_children():
            self.tree_ventas.delete(item)

        ventas = self.venta_service.listar_ventas(termino=termino)
        for v in ventas:
            self.tree_ventas.insert(
                "",
                "end",
                iid=str(v["id"]),
                values=(
                    v["folio"],
                    v["fecha"],
                    v["usuario_nombre"],
                    f"{v['total_piezas'] or 0} pz",
                    f"${v['total']:.2f}",
                    v["notas"]
                )
            )

        # Limpiar detalle
        for item in self.tree_detalles.get_children():
            self.tree_detalles.delete(item)
        self.lbl_detalle_titulo.config(text="Desglose de Artículos de la Venta (Seleccione una arriba):")

        # 2. Cargar Tab JOIN
        for item in self.tree_join.get_children():
            self.tree_join.delete(item)

        movimientos = self.venta_service.listar_movimientos_con_join(termino=termino)
        for m in movimientos:
            self.tree_join.insert(
                "",
                "end",
                iid=str(m["detalle_id"]),
                values=(
                    m["venta_folio"],
                    m["venta_fecha"],
                    m["cajero_nombre"],
                    m["producto_codigo"],
                    m["producto_nombre"],
                    m["categoria_nombre"],
                    m["cantidad"],
                    f"${m['precio_unitario']:.2f}",
                    f"${m['subtotal']:.2f}"
                )
            )

    def _on_venta_seleccionada(self, event):
        sel = self.tree_ventas.selection()
        if not sel:
            return

        venta_id = int(sel[0])
        venta_comp = self.venta_service.obtener_venta_completa(venta_id)
        if not venta_comp:
            return

        self.lbl_detalle_titulo.config(
            text=f"Desglose de Artículos - Folio: {venta_comp['folio']} | Total: ${venta_comp['total']:.2f} | Atendió: {venta_comp['usuario_nombre']}"
        )

        for item in self.tree_detalles.get_children():
            self.tree_detalles.delete(item)

        for d in venta_comp["detalles"]:
            self.tree_detalles.insert(
                "",
                "end",
                values=(
                    d["producto_codigo"],
                    d["producto_nombre"],
                    d["categoria_nombre"],
                    d["cantidad"],
                    f"${d['precio_unitario']:.2f}",
                    f"${d['subtotal']:.2f}"
                )
            )

    def _exportar_csv_movimientos(self):
        movimientos = self.venta_service.listar_movimientos_con_join(termino=self.txt_buscar.get().strip())
        if not movimientos:
            messagebox.showinfo("Exportar", "No hay datos para exportar en este momento.", parent=self)
            return

        archivo = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar Historial de Movimientos en CSV",
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        if not archivo:
            return

        encabezados = ["Folio Venta", "Fecha", "Cajero", "Código Producto", "Producto", "Categoría", "Cantidad", "Precio Unitario", "Subtotal"]
        filas = [
            [
                m["venta_folio"],
                m["venta_fecha"],
                m["cajero_nombre"],
                m["producto_codigo"],
                m["producto_nombre"],
                m["categoria_nombre"],
                m["cantidad"],
                f"{m['precio_unitario']:.2f}",
                f"{m['subtotal']:.2f}"
            ]
            for m in movimientos
        ]

        try:
            self.reporte_service.exportar_a_csv(archivo, encabezados, filas)
            messagebox.showinfo("Exportación Exitosa", f"Los movimientos fueron exportados a:\n{archivo}", parent=self)
        except Exception as ex:
            messagebox.showerror("Error al Exportar", f"No se pudo guardar el archivo:\n{ex}", parent=self)
