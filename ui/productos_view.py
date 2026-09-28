import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from models.producto import Producto
from models.usuario import Usuario
from services.producto_service import ProductoService
from services.categoria_service import CategoriaService
from ui.theme import ModernTheme


class ProductosView(ttk.Frame):
    """Vista de Catálogo de Productos (Entidad A) con JOIN a categorías, filtros y CRUD."""

    def __init__(self, parent, usuario_actual: Usuario):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.service = ProductoService()
        self.cat_service = CategoriaService()

        self._crear_interfaz()
        self.cargar_datos()

    def _crear_interfaz(self):
        # 1. Barra Superior: Título y Filtros Combinados (RF-6)
        top_frame = ttk.Frame(self, padding=(10, 10, 10, 5))
        top_frame.pack(fill="x")

        lbl_titulo = ttk.Label(top_frame, text="Catálogo de Productos de Almacén", style="Header.TLabel")
        lbl_titulo.pack(side="left")

        # Filtros: Búsqueda de texto y Combo de Categoría
        filter_frame = ttk.Frame(top_frame)
        filter_frame.pack(side="right")

        ttk.Label(filter_frame, text="Categoría:").pack(side="left", padx=(10, 2))
        self.cbo_categoria_filtro = ttk.Combobox(filter_frame, state="readonly", width=22)
        self.cbo_categoria_filtro.pack(side="left", padx=2)
        self.cbo_categoria_filtro.bind("<<ComboboxSelected>>", lambda e: self.filtrar_datos())

        ttk.Label(filter_frame, text="Buscar:").pack(side="left", padx=(10, 2))
        self.txt_buscar = ttk.Entry(filter_frame, width=20)
        self.txt_buscar.pack(side="left", padx=2)
        self.txt_buscar.bind("<KeyRelease>", lambda e: self.filtrar_datos())

        btn_limpiar = ttk.Button(filter_frame, text="✖", width=3, style="Secondary.TButton", command=self._limpiar_filtros)
        btn_limpiar.pack(side="left", padx=2)

        # 2. Barra de Herramientas de Acciones (CRUD)
        toolbar = ttk.Frame(self, padding=(10, 5, 10, 10))
        toolbar.pack(fill="x")

        btn_nuevo = ttk.Button(toolbar, text="➕ Nuevo Producto", style="Primary.TButton", command=self._abrir_formulario_nuevo)
        btn_nuevo.pack(side="left", padx=5)

        btn_editar = ttk.Button(toolbar, text="✏️ Editar", style="Secondary.TButton", command=self._abrir_formulario_editar)
        btn_editar.pack(side="left", padx=5)

        btn_estado = ttk.Button(toolbar, text="🔄 Activar / Desactivar", style="Secondary.TButton", command=self._cambiar_estado)
        btn_estado.pack(side="left", padx=5)

        btn_eliminar = ttk.Button(toolbar, text="🗑️ Eliminar", style="Danger.TButton", command=self._eliminar_producto)
        btn_eliminar.pack(side="left", padx=5)

        # Leyenda de alertas de stock bajo
        lbl_leyenda = ttk.Label(
            toolbar,
            text="⚠️ Rojo: Stock Crítico / Bajo (≤ 5) | Gris: Inactivo",
            font=("Segoe UI", 9, "italic"),
            foreground=ModernTheme.WARNING
        )
        lbl_leyenda.pack(side="right", padx=10)

        # 3. Treeview con JOIN a Categorías (RF-7)
        tree_container = ttk.Frame(self, padding=10)
        tree_container.pack(fill="both", expand=True)

        columnas = ("id", "codigo", "nombre", "categoria", "precio", "stock", "estado")
        self.tree = ttk.Treeview(tree_container, columns=columnas, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("codigo", text="Código")
        self.tree.heading("nombre", text="Nombre del Producto")
        self.tree.heading("categoria", text="Categoría")
        self.tree.heading("precio", text="Precio Unit.")
        self.tree.heading("stock", text="Stock Actual")
        self.tree.heading("estado", text="Estado")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("codigo", width=110, anchor="center")
        self.tree.column("nombre", width=280, anchor="w")
        self.tree.column("categoria", width=180, anchor="w")
        self.tree.column("precio", width=100, anchor="e")
        self.tree.column("stock", width=90, anchor="center")
        self.tree.column("estado", width=100, anchor="center")

        scroll_y = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Configuración de tags para realces visuales
        self.tree.tag_configure("stock_critico", background="#fee2e2", foreground="#991b1b")  # Rojo suave
        self.tree.tag_configure("inactivo", background="#f1f5f9", foreground=ModernTheme.TEXT_MUTED)
        self.tree.tag_configure("normal", background="#ffffff")

        self.tree.bind("<Double-1>", lambda e: self._abrir_formulario_editar())

    def _actualizar_combo_categorias(self):
        cats = self.cat_service.listar_todas(solo_activas=False)
        valores = ["-- Todas las Categorías --"] + [f"{c.id} - {c.nombre}" for c in cats]
        self.cbo_categoria_filtro["values"] = valores
        self.cbo_categoria_filtro.current(0)

    def _limpiar_filtros(self):
        self.txt_buscar.delete(0, tk.END)
        self.cbo_categoria_filtro.current(0)
        self.cargar_datos()

    def cargar_datos(self):
        self._actualizar_combo_categorias()
        self.filtrar_datos()

    def filtrar_datos(self):
        termino = self.txt_buscar.get().strip()

        cat_sel = self.cbo_categoria_filtro.get()
        categoria_id = None
        if cat_sel and not cat_sel.startswith("--"):
            try:
                categoria_id = int(cat_sel.split(" - ")[0])
            except ValueError:
                categoria_id = None

        for item in self.tree.get_children():
            self.tree.delete(item)

        productos = self.service.buscar(termino=termino, categoria_id=categoria_id, solo_activos=False)

        for p in productos:
            if not p.activo:
                tag = "inactivo"
            elif p.es_stock_bajo:
                tag = "stock_critico"
            else:
                tag = "normal"

            self.tree.insert(
                "",
                "end",
                iid=str(p.id),
                values=(
                    p.id,
                    p.codigo,
                    p.nombre,
                    p.categoria_nombre or "N/A",
                    f"${p.precio:.2f}",
                    p.stock,
                    p.estado_texto
                ),
                tags=(tag,)
            )

    def _get_seleccionado_id(self) -> Optional[int]:
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Información", "Por favor seleccione un producto de la tabla.", parent=self)
            return None
        return int(seleccion[0])

    def _abrir_formulario_nuevo(self):
        ProductoDialog(self, titulo="Nuevo Producto", on_save=self.cargar_datos, usuario_actual=self.usuario_actual)

    def _abrir_formulario_editar(self):
        prod_id = self._get_seleccionado_id()
        if prod_id is None:
            return
        prod = self.service.obtener_por_id(prod_id)
        if not prod:
            messagebox.showerror("Error", "No se encontró el producto seleccionado.", parent=self)
            return
        ProductoDialog(
            self,
            titulo="Editar Producto",
            producto=prod,
            on_save=self.cargar_datos,
            usuario_actual=self.usuario_actual
        )

    def _cambiar_estado(self):
        prod_id = self._get_seleccionado_id()
        if prod_id is None:
            return
        prod = self.service.obtener_por_id(prod_id)
        if not prod:
            return

        nuevo_estado = not prod.activo
        accion_texto = "activar" if nuevo_estado else "desactivar"

        if messagebox.askyesno(
            "Confirmación",
            f"¿Está seguro de que desea {accion_texto} el producto '{prod.nombre}'?",
            parent=self
        ):
            try:
                self.service.cambiar_estado(prod_id, nuevo_estado, self.usuario_actual)
                self.cargar_datos()
                messagebox.showinfo("Éxito", f"Producto {accion_texto}do exitosamente.", parent=self)
            except Exception as ex:
                messagebox.showerror("Error", f"No se pudo cambiar el estado:\n{ex}", parent=self)

    def _eliminar_producto(self):
        prod_id = self._get_seleccionado_id()
        if prod_id is None:
            return
        prod = self.service.obtener_por_id(prod_id)
        if not prod:
            return

        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Desea eliminar de forma permanente el producto '{prod.nombre}'?\n\n"
            "Nota: Si el producto ya tiene ventas registradas, la regla de integridad (RF-10) impedirá su borrado físico.",
            parent=self
        ):
            return

        try:
            self.service.eliminar_o_desactivar(prod_id, self.usuario_actual)
            self.cargar_datos()
            messagebox.showinfo("Éxito", "Producto eliminado correctamente.", parent=self)
        except ValueError as val_err:
            # Integridad referencial protegida (RF-10, RNF-4)
            if messagebox.askyesno(
                "Integridad Referencial Protegida",
                f"{val_err}\n\n¿Desea marcar el producto como INACTIVO ahora mismo?",
                parent=self
            ):
                self.service.cambiar_estado(prod_id, False, self.usuario_actual)
                self.cargar_datos()
                messagebox.showinfo("Actualizado", "El producto fue marcado como Inactivo.", parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"Ocurrió un error inesperado al eliminar:\n{ex}", parent=self)


class ProductoDialog(tk.Toplevel):
    """Ventana modal Toplevel para creación y edición de productos (RNF-3)."""

    def __init__(
        self,
        parent,
        titulo: str,
        usuario_actual: Usuario,
        on_save,
        producto: Optional[Producto] = None
    ):
        super().__init__(parent)
        self.title(titulo)
        self.producto = producto
        self.usuario_actual = usuario_actual
        self.on_save = on_save
        self.service = ProductoService()
        self.cat_service = CategoriaService()

        self.geometry("480x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Centrar
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 240
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 210
        self.geometry(f"+{x}+{y}")

        self._crear_formulario()

    def _crear_formulario(self):
        form = ttk.Frame(self, padding=20)
        form.pack(fill="both", expand=True)

        # Código de producto
        ttk.Label(form, text="Código Único (*):", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=4)
        self.txt_codigo = ttk.Entry(form, font=("Segoe UI", 10))
        self.txt_codigo.grid(row=0, column=1, sticky="ew", pady=4)
        self.txt_codigo.focus_set()

        # Nombre de producto
        ttk.Label(form, text="Nombre del Producto (*):", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=4)
        self.txt_nombre = ttk.Entry(form, font=("Segoe UI", 10))
        self.txt_nombre.grid(row=1, column=1, sticky="ew", pady=4)

        # Categoría
        ttk.Label(form, text="Categoría (*):", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=4)
        self.cbo_categoria = ttk.Combobox(form, state="readonly", font=("Segoe UI", 10))
        self.cbo_categoria.grid(row=2, column=1, sticky="ew", pady=4)

        # Cargar categorías activas
        cats = self.cat_service.listar_todas(solo_activas=self.producto is None)
        self.categorias_map = {f"{c.nombre} (ID: {c.id})": c.id for c in cats}
        self.cbo_categoria["values"] = list(self.categorias_map.keys())

        # Precio
        ttk.Label(form, text="Precio Venta ($) (*):", font=("Segoe UI", 9, "bold")).grid(row=3, column=0, sticky="w", pady=4)
        self.txt_precio = ttk.Entry(form, font=("Segoe UI", 10))
        self.txt_precio.grid(row=3, column=1, sticky="ew", pady=4)

        # Stock
        ttk.Label(form, text="Stock Inicial / Existencia (*):", font=("Segoe UI", 9, "bold")).grid(row=4, column=0, sticky="w", pady=4)
        self.txt_stock = ttk.Entry(form, font=("Segoe UI", 10))
        self.txt_stock.grid(row=4, column=1, sticky="ew", pady=4)

        # Activo
        self.var_activo = tk.BooleanVar(value=True)
        if self.producto:
            self.var_activo.set(self.producto.activo)
            chk_activo = ttk.Checkbutton(form, text="Producto Activo en Catálogo", variable=self.var_activo)
            chk_activo.grid(row=5, column=1, sticky="w", pady=10)

        form.grid_columnconfigure(1, weight=1)

        # Cargar datos si es edición
        if self.producto:
            self.txt_codigo.insert(0, self.producto.codigo)
            self.txt_nombre.insert(0, self.producto.nombre)
            self.txt_precio.insert(0, f"{self.producto.precio:.2f}")
            self.txt_stock.insert(0, str(self.producto.stock))

            # Seleccionar categoría
            for nombre_combo, cid in self.categorias_map.items():
                if cid == self.producto.categoria_id:
                    self.cbo_categoria.set(nombre_combo)
                    break
        elif self.categorias_map:
            self.cbo_categoria.current(0)

        # Botones de Acción
        btn_box = ttk.Frame(form)
        btn_box.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(25, 0))

        btn_cancelar = ttk.Button(btn_box, text="Cancelar", style="Secondary.TButton", command=self.destroy)
        btn_cancelar.pack(side="right", padx=5)

        btn_guardar = ttk.Button(btn_box, text="Guardar", style="Primary.TButton", command=self._guardar)
        btn_guardar.pack(side="right", padx=5)

    def _guardar(self):
        codigo = self.txt_codigo.get().strip()
        nombre = self.txt_nombre.get().strip()
        cat_seleccionada = self.cbo_categoria.get()
        precio_str = self.txt_precio.get().strip()
        stock_str = self.txt_stock.get().strip()

        if not cat_seleccionada or cat_seleccionada not in self.categorias_map:
            messagebox.showwarning("Atención", "Debe seleccionar una categoría válida.", parent=self)
            return

        categoria_id = self.categorias_map[cat_seleccionada]

        try:
            if self.producto:
                self.service.actualizar(
                    prod_id=self.producto.id,
                    codigo=codigo,
                    nombre=nombre,
                    categoria_id=categoria_id,
                    precio_str=precio_str,
                    stock_str=stock_str,
                    activo=self.var_activo.get(),
                    usuario_actual=self.usuario_actual
                )
                messagebox.showinfo("Éxito", "Producto actualizado correctamente.", parent=self)
            else:
                self.service.crear(
                    codigo=codigo,
                    nombre=nombre,
                    categoria_id=categoria_id,
                    precio_str=precio_str,
                    stock_str=stock_str,
                    usuario_actual=self.usuario_actual
                )
                messagebox.showinfo("Éxito", "Producto registrado con éxito.", parent=self)

            self.on_save()
            self.destroy()
        except ValueError as val_err:
            messagebox.showwarning("Validación de Datos", str(val_err), parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"No se pudo guardar el producto:\n{ex}", parent=self)
