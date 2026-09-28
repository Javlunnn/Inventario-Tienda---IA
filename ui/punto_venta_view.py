import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional
from models.usuario import Usuario
from models.producto import Producto
from services.venta_service import VentaService
from services.producto_service import ProductoService
from ui.theme import ModernTheme


class PuntoVentaView(ttk.Frame):
    """
    Vista del Proceso de Negocio: Punto de Venta / Registro de Venta con Carrito (RF-5).
    Descuenta existencias en inventario y relaciona usuario cajero con los productos vendidos.
    """

    def __init__(self, parent, usuario_actual: Usuario, on_venta_realizada=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.on_venta_realizada = on_venta_realizada
        self.venta_service = VentaService()
        self.prod_service = ProductoService()

        # Lista de ítems en carrito: [{'producto_id', 'codigo', 'nombre', 'precio_unitario', 'cantidad', 'subtotal', 'stock_max'}]
        self.carrito: List[Dict] = []
        self.productos_activos: List[Producto] = []
        self.producto_seleccionado: Optional[Producto] = None

        self._crear_interfaz()
        self.recargar_catalogo()

    def _crear_interfaz(self):
        # Layout dividido en 2 columnas: Izquierda (Selección de Producto) y Derecha (Carrito y Cobro)
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # ----------------- PANEL IZQUIERDO: SELECCIÓN DE ARTÍCULOS -----------------
        left_frame = ttk.Frame(paned, padding=10)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Catálogo de Mostrador", style="Header.TLabel").pack(anchor="w", pady=(0, 8))

        # Buscador rápido
        search_box = ttk.Frame(left_frame)
        search_box.pack(fill="x", pady=(0, 10))

        ttk.Label(search_box, text="Buscar:").pack(side="left", padx=(0, 5))
        self.txt_buscar_prod = ttk.Entry(search_box)
        self.txt_buscar_prod.pack(side="left", fill="x", expand=True, padx=5)
        self.txt_buscar_prod.bind("<KeyRelease>", lambda e: self._filtrar_productos_disponibles())

        # Tabla de productos disponibles
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill="both", expand=True)

        cols = ("codigo", "nombre", "categoria", "precio", "stock")
        self.tree_prod = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse", height=10)
        self.tree_prod.heading("codigo", text="Código")
        self.tree_prod.heading("nombre", text="Producto")
        self.tree_prod.heading("categoria", text="Categoría")
        self.tree_prod.heading("precio", text="Precio")
        self.tree_prod.heading("stock", text="Stock")

        self.tree_prod.column("codigo", width=80, anchor="center")
        self.tree_prod.column("nombre", width=180, anchor="w")
        self.tree_prod.column("categoria", width=120, anchor="w")
        self.tree_prod.column("precio", width=70, anchor="e")
        self.tree_prod.column("stock", width=60, anchor="center")

        scroll_prod = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_prod.yview)
        self.tree_prod.configure(yscrollcommand=scroll_prod.set)

        self.tree_prod.pack(side="left", fill="both", expand=True)
        scroll_prod.pack(side="right", fill="y")

        self.tree_prod.bind("<<TreeviewSelect>>", self._on_producto_seleccionado)
        self.tree_prod.bind("<Double-1>", lambda e: self._agregar_al_carrito())

        # Panel de Detalle y Cantidad
        add_frame = ttk.Frame(left_frame, style="Card.TFrame", padding=12)
        add_frame.pack(fill="x", pady=(10, 0))

        self.lbl_prod_info = ttk.Label(
            add_frame,
            text="Seleccione un producto del catálogo para añadirlo al carrito.",
            font=("Segoe UI", 9, "italic"),
            style="Card.TLabel"
        )
        self.lbl_prod_info.pack(anchor="w", pady=(0, 8))

        qty_frame = ttk.Frame(add_frame, style="Card.TFrame")
        qty_frame.pack(fill="x")

        ttk.Label(qty_frame, text="Cantidad a vender:", font=("Segoe UI", 9, "bold"), style="Card.TLabel").pack(side="left", padx=(0, 8))
        self.spin_cantidad = ttk.Spinbox(qty_frame, from_=1, to=999, width=8, font=("Segoe UI", 10))
        self.spin_cantidad.set(1)
        self.spin_cantidad.pack(side="left", padx=5)

        self.btn_agregar = ttk.Button(
            qty_frame,
            text="🛒 Agregar al Carrito",
            style="Primary.TButton",
            command=self._agregar_al_carrito,
            state="disabled"
        )
        self.btn_agregar.pack(side="right", padx=5)

        # ----------------- PANEL DERECHO: TICKET / CARRITO DE VENTA -----------------
        right_frame = ttk.Frame(paned, padding=10)
        paned.add(right_frame, weight=1)

        ttk.Label(right_frame, text="Ticket de Venta Actual", style="Header.TLabel").pack(anchor="w", pady=(0, 8))

        # Tabla del Carrito
        cart_frame = ttk.Frame(right_frame)
        cart_frame.pack(fill="both", expand=True)

        cart_cols = ("codigo", "nombre", "cantidad", "precio", "subtotal")
        self.tree_cart = ttk.Treeview(cart_frame, columns=cart_cols, show="headings", selectmode="browse", height=10)
        self.tree_cart.heading("codigo", text="Código")
        self.tree_cart.heading("nombre", text="Artículo")
        self.tree_cart.heading("cantidad", text="Cant.")
        self.tree_cart.heading("precio", text="P. Unit.")
        self.tree_cart.heading("subtotal", text="Subtotal")

        self.tree_cart.column("codigo", width=80, anchor="center")
        self.tree_cart.column("nombre", width=180, anchor="w")
        self.tree_cart.column("cantidad", width=60, anchor="center")
        self.tree_cart.column("precio", width=80, anchor="e")
        self.tree_cart.column("subtotal", width=90, anchor="e")

        scroll_cart = ttk.Scrollbar(cart_frame, orient="vertical", command=self.tree_cart.yview)
        self.tree_cart.configure(yscrollcommand=scroll_cart.set)

        self.tree_cart.pack(side="left", fill="both", expand=True)
        scroll_cart.pack(side="right", fill="y")

        # Botones de gestión del carrito
        cart_actions = ttk.Frame(right_frame, padding=(0, 5))
        cart_actions.pack(fill="x")

        btn_quitar = ttk.Button(cart_actions, text="❌ Quitar Ítem", style="Secondary.TButton", command=self._quitar_del_carrito)
        btn_quitar.pack(side="left", padx=5)

        btn_vaciar = ttk.Button(cart_actions, text="🗑️ Vaciar Carrito", style="Secondary.TButton", command=self._vaciar_carrito)
        btn_vaciar.pack(side="left", padx=5)

        # Panel de Resumen de Pago y Cobro
        summary_card = ttk.Frame(right_frame, style="Card.TFrame", padding=15)
        summary_card.pack(fill="x", pady=(10, 0))

        # Notas / Observaciones
        ttk.Label(summary_card, text="Notas o Método de Pago:", style="Card.TLabel", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.txt_notas = ttk.Entry(summary_card, font=("Segoe UI", 9))
        self.txt_notas.insert(0, "Pago en mostrador (Efectivo)")
        self.txt_notas.pack(fill="x", pady=(2, 10))

        # Totales
        totales_frame = ttk.Frame(summary_card, style="Card.TFrame")
        totales_frame.pack(fill="x", pady=5)

        ttk.Label(totales_frame, text="Artículos en carrito:", style="Card.TLabel").pack(side="left")
        self.lbl_articulos_count = ttk.Label(totales_frame, text="0 unidades", font=("Segoe UI", 10, "bold"), style="Card.TLabel")
        self.lbl_articulos_count.pack(side="right")

        total_row = ttk.Frame(summary_card, style="Card.TFrame")
        total_row.pack(fill="x", pady=(8, 12))

        ttk.Label(total_row, text="TOTAL A PAGAR:", font=("Segoe UI", 13, "bold"), foreground=ModernTheme.PRIMARY, style="Card.TLabel").pack(side="left")
        self.lbl_total_monto = ttk.Label(total_row, text="$0.00", font=("Segoe UI", 16, "bold"), foreground=ModernTheme.SUCCESS, style="Card.TLabel")
        self.lbl_total_monto.pack(side="right")

        # Botón Cobrar
        self.btn_cobrar = ttk.Button(
            summary_card,
            text="💳 COBRAR Y FINALIZAR VENTA",
            style="Success.TButton",
            command=self._finalizar_venta,
            state="disabled"
        )
        self.btn_cobrar.pack(fill="x", ipady=4)

    def recargar_catalogo(self):
        """Carga solo productos ACTIVOS para evitar ventas de descontinuados (RF-5, A.5)."""
        self.productos_activos = self.prod_service.listar_todos(solo_activos=True)
        self._filtrar_productos_disponibles()

    def _filtrar_productos_disponibles(self):
        termino = self.txt_buscar_prod.get().strip().lower()
        for item in self.tree_prod.get_children():
            self.tree_prod.delete(item)

        for p in self.productos_activos:
            if not termino or (termino in p.codigo.lower() or termino in p.nombre.lower()):
                self.tree_prod.insert(
                    "",
                    "end",
                    iid=str(p.id),
                    values=(p.codigo, p.nombre, p.categoria_nombre or "", f"${p.precio:.2f}", p.stock)
                )

    def _on_producto_seleccionado(self, event):
        sel = self.tree_prod.selection()
        if not sel:
            self.producto_seleccionado = None
            self.btn_agregar.config(state="disabled")
            self.lbl_prod_info.config(text="Seleccione un producto para añadirlo al carrito.")
            return

        prod_id = int(sel[0])
        prod = next((p for p in self.productos_activos if p.id == prod_id), None)
        if prod:
            self.producto_seleccionado = prod
            self.lbl_prod_info.config(
                text=f"Artículo: {prod.nombre} | Precio: ${prod.precio:.2f} | Stock Almacén: {prod.stock} pz."
            )
            if prod.stock <= 0:
                self.btn_agregar.config(state="disabled")
                self.lbl_prod_info.config(text=f"❌ '{prod.nombre}' SIN STOCK DISPONIBLE.", foreground=ModernTheme.DANGER)
            else:
                self.btn_agregar.config(state="normal")
                self.spin_cantidad.config(to=prod.stock)
                self.spin_cantidad.set(1)

    def _agregar_al_carrito(self):
        if not self.producto_seleccionado:
            return

        prod = self.producto_seleccionado
        try:
            cantidad = int(self.spin_cantidad.get())
            if cantidad <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Cantidad Inválida", "Ingrese una cantidad entera positiva.", parent=self)
            return

        # Calcular cantidad ya añadida en carrito
        cant_en_carrito = sum(item["cantidad"] for item in self.carrito if item["producto_id"] == prod.id)
        nueva_cantidad_total = cant_en_carrito + cantidad

        # Validar regla de negocio (RF-5: No vender si cantidad > stock)
        if nueva_cantidad_total > prod.stock:
            messagebox.showwarning(
                "Stock Insuficiente",
                f"No puede agregar {cantidad} unidad(es) más.\n"
                f"Existencia total: {prod.stock} | En carrito: {cant_en_carrito} | Disponible restante: {prod.stock - cant_en_carrito}",
                parent=self
            )
            return

        # Si ya está en el carrito, actualizar cantidad
        item_existente = next((item for item in self.carrito if item["producto_id"] == prod.id), None)
        if item_existente:
            item_existente["cantidad"] = nueva_cantidad_total
            item_existente["subtotal"] = round(item_existente["cantidad"] * item_existente["precio_unitario"], 2)
        else:
            subtotal = round(cantidad * prod.precio, 2)
            self.carrito.append({
                "producto_id": prod.id,
                "codigo": prod.codigo,
                "nombre": prod.nombre,
                "precio_unitario": prod.precio,
                "cantidad": cantidad,
                "subtotal": subtotal,
                "stock_max": prod.stock
            })

        self._actualizar_vista_carrito()

    def _quitar_del_carrito(self):
        sel = self.tree_cart.selection()
        if not sel:
            messagebox.showinfo("Atención", "Seleccione un ítem del carrito para remover.", parent=self)
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.carrito):
            self.carrito.pop(idx)
            self._actualizar_vista_carrito()

    def _vaciar_carrito(self):
        if not self.carrito:
            return
        if messagebox.askyesno("Confirmar", "¿Desea vaciar todos los productos del carrito actual?", parent=self):
            self.carrito.clear()
            self._actualizar_vista_carrito()

    def _actualizar_vista_carrito(self):
        for item in self.tree_cart.get_children():
            self.tree_cart.delete(item)

        total_monto = 0.0
        total_piezas = 0

        for idx, item in enumerate(self.carrito):
            self.tree_cart.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    item["codigo"],
                    item["nombre"],
                    item["cantidad"],
                    f"${item['precio_unitario']:.2f}",
                    f"${item['subtotal']:.2f}"
                )
            )
            total_monto += item["subtotal"]
            total_piezas += item["cantidad"]

        self.lbl_articulos_count.config(text=f"{total_piezas} piezas ({len(self.carrito)} artículos)")
        self.lbl_total_monto.config(text=f"${total_monto:.2f}")

        if self.carrito:
            self.btn_cobrar.config(state="normal")
        else:
            self.btn_cobrar.config(state="disabled")

    def _finalizar_venta(self):
        if not self.carrito:
            return

        total_actual = sum(item["subtotal"] for item in self.carrito)
        notas = self.txt_notas.get().strip()

        # Confirmación de cobro (RF-9)
        msg_confirm = (
            f"¿Desea procesar la venta por un total de ${total_actual:.2f}?\n\n"
            f"Se descontarán las piezas del inventario permanentemente."
        )
        if not messagebox.askyesno("Confirmar Cobro", msg_confirm, parent=self):
            return

        try:
            venta_id, folio = self.venta_service.procesar_venta(
                usuario_actual=self.usuario_actual,
                items_carrito=self.carrito,
                notas=notas
            )

            # Ticket de confirmación
            detalles_str = "\n".join([f"• {it['cantidad']}x {it['nombre']} - ${it['subtotal']:.2f}" for it in self.carrito])
            mensaje_exito = (
                f"✅ ¡VENTA REGISTRADA EXITOSAMENTE!\n\n"
                f"Folio: {folio}\n"
                f"Cajero: {self.usuario_actual.username}\n"
                f"Total Cobrado: ${total_actual:.2f}\n\n"
                f"Artículos:\n{detalles_str}\n\n"
                f"Inventario actualizado correctamente."
            )
            messagebox.showinfo("Venta Finalizada", mensaje_exito, parent=self)

            # Limpiar carrito y recargar catálogo
            self.carrito.clear()
            self._actualizar_vista_carrito()
            self.recargar_catalogo()

            if self.on_venta_realizada:
                self.on_venta_realizada()

        except ValueError as err_val:
            messagebox.showwarning("No se pudo procesar la venta", str(err_val), parent=self)
            self.recargar_catalogo()
        except Exception as ex:
            messagebox.showerror("Error Crítico", f"Error inesperado al registrar venta:\n{ex}", parent=self)
