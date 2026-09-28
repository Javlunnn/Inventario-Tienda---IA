import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from models.categoria import Categoria
from models.usuario import Usuario
from services.categoria_service import CategoriaService
from ui.theme import ModernTheme


class CategoriasView(ttk.Frame):
    """Vista de Catálogo de Categorías (Entidad B) con CRUD completo y Treeview."""

    def __init__(self, parent, usuario_actual: Usuario):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.service = CategoriaService()

        self._crear_interfaz()
        self.cargar_datos()

    def _crear_interfaz(self):
        # 1. Barra Superior con Título y Buscador (RF-6)
        top_frame = ttk.Frame(self, padding=(10, 10, 10, 5))
        top_frame.pack(fill="x")

        lbl_titulo = ttk.Label(top_frame, text="Catálogo de Categorías", style="Header.TLabel")
        lbl_titulo.pack(side="left")

        # Buscador en Treeview
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side="right")

        ttk.Label(search_frame, text="Buscar:").pack(side="left", padx=5)
        self.txt_buscar = ttk.Entry(search_frame, width=25)
        self.txt_buscar.pack(side="left", padx=5)
        self.txt_buscar.bind("<KeyRelease>", lambda e: self.filtrar_datos())

        btn_limpiar = ttk.Button(search_frame, text="✖", width=3, style="Secondary.TButton", command=self._limpiar_filtro)
        btn_limpiar.pack(side="left")

        # 2. Barra de Herramientas de Acciones (CRUD)
        toolbar = ttk.Frame(self, padding=(10, 5, 10, 10))
        toolbar.pack(fill="x")

        btn_nuevo = ttk.Button(toolbar, text="➕ Nueva Categoría", style="Primary.TButton", command=self._abrir_formulario_nuevo)
        btn_nuevo.pack(side="left", padx=5)

        btn_editar = ttk.Button(toolbar, text="✏️ Editar", style="Secondary.TButton", command=self._abrir_formulario_editar)
        btn_editar.pack(side="left", padx=5)

        btn_estado = ttk.Button(toolbar, text="🔄 Activar / Desactivar", style="Secondary.TButton", command=self._cambiar_estado)
        btn_estado.pack(side="left", padx=5)

        btn_eliminar = ttk.Button(toolbar, text="🗑️ Eliminar", style="Danger.TButton", command=self._eliminar_categoria)
        btn_eliminar.pack(side="left", padx=5)

        # 3. Contenedor de la Tabla Treeview con Scrollbar
        tree_container = ttk.Frame(self, padding=10)
        tree_container.pack(fill="both", expand=True)

        columnas = ("id", "nombre", "descripcion", "estado")
        self.tree = ttk.Treeview(tree_container, columns=columnas, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre de Categoría")
        self.tree.heading("descripcion", text="Descripción")
        self.tree.heading("estado", text="Estado")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("nombre", width=220, anchor="w")
        self.tree.column("descripcion", width=420, anchor="w")
        self.tree.column("estado", width=120, anchor="center")

        scroll_y = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Tags para estilos de fila
        self.tree.tag_configure("inactivo", foreground=ModernTheme.TEXT_MUTED, background="#f1f5f9")
        self.tree.tag_configure("activo", background="#ffffff")

        self.tree.bind("<Double-1>", lambda e: self._abrir_formulario_editar())

    def _limpiar_filtro(self):
        self.txt_buscar.delete(0, tk.END)
        self.cargar_datos()

    def cargar_datos(self):
        """Carga todas las categorías en el Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        categorias = self.service.listar_todas(solo_activas=False)
        for cat in categorias:
            tag = "activo" if cat.activo else "inactivo"
            self.tree.insert(
                "",
                "end",
                iid=str(cat.id),
                values=(cat.id, cat.nombre, cat.descripcion, cat.estado_texto),
                tags=(tag,)
            )

    def filtrar_datos(self):
        termino = self.txt_buscar.get().strip()
        for item in self.tree.get_children():
            self.tree.delete(item)

        categorias = self.service.buscar(termino, solo_activas=False)
        for cat in categorias:
            tag = "activo" if cat.activo else "inactivo"
            self.tree.insert(
                "",
                "end",
                iid=str(cat.id),
                values=(cat.id, cat.nombre, cat.descripcion, cat.estado_texto),
                tags=(tag,)
            )

    def _get_seleccionado_id(self) -> Optional[int]:
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Información", "Por favor seleccione una categoría de la lista.", parent=self)
            return None
        return int(seleccion[0])

    def _abrir_formulario_nuevo(self):
        CategoriaDialog(self, titulo="Nueva Categoría", on_save=self.cargar_datos, usuario_actual=self.usuario_actual)

    def _abrir_formulario_editar(self):
        cat_id = self._get_seleccionado_id()
        if cat_id is None:
            return
        cat = self.service.obtener_por_id(cat_id)
        if not cat:
            messagebox.showerror("Error", "No se encontró la categoría seleccionada.", parent=self)
            return
        CategoriaDialog(
            self,
            titulo="Editar Categoría",
            categoria=cat,
            on_save=self.cargar_datos,
            usuario_actual=self.usuario_actual
        )

    def _cambiar_estado(self):
        cat_id = self._get_seleccionado_id()
        if cat_id is None:
            return
        cat = self.service.obtener_por_id(cat_id)
        if not cat:
            return

        nuevo_estado = not cat.activo
        accion_texto = "activar" if nuevo_estado else "desactivar"

        # Confirmación con messagebox (RF-9)
        if messagebox.askyesno(
            "Confirmación",
            f"¿Está seguro de que desea {accion_texto} la categoría '{cat.nombre}'?",
            parent=self
        ):
            try:
                self.service.cambiar_estado(cat_id, nuevo_estado, self.usuario_actual)
                self.cargar_datos()
                messagebox.showinfo("Éxito", f"Categoría {accion_texto}da correctamente.", parent=self)
            except Exception as ex:
                messagebox.showerror("Error", f"No se pudo cambiar el estado:\n{ex}", parent=self)

    def _eliminar_categoria(self):
        cat_id = self._get_seleccionado_id()
        if cat_id is None:
            return
        cat = self.service.obtener_por_id(cat_id)
        if not cat:
            return

        # Confirmación previa (RF-9)
        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Desea eliminar la categoría '{cat.nombre}'?\n\n"
            "Nota: Si la categoría tiene productos registrados, el sistema impedirá su eliminación para proteger los datos.",
            parent=self
        ):
            return

        try:
            self.service.eliminar_o_desactivar(cat_id, self.usuario_actual)
            self.cargar_datos()
            messagebox.showinfo("Éxito", "Categoría eliminada con éxito.", parent=self)
        except ValueError as val_err:
            # Integridad referencial protegida (RF-10, RNF-4)
            messagebox.showwarning("Integridad Protegida", str(val_err), parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"Error al intentar eliminar:\n{ex}", parent=self)


class CategoriaDialog(tk.Toplevel):
    """Formulario modal para alta y edición de categorías (RNF-3)."""

    def __init__(
        self,
        parent,
        titulo: str,
        usuario_actual: Usuario,
        on_save,
        categoria: Optional[Categoria] = None
    ):
        super().__init__(parent)
        self.title(titulo)
        self.categoria = categoria
        self.usuario_actual = usuario_actual
        self.on_save = on_save
        self.service = CategoriaService()

        self.geometry("450x320")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Centrar relativo al padre
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 225
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 160
        self.geometry(f"+{x}+{y}")

        self._crear_formulario()

    def _crear_formulario(self):
        form = ttk.Frame(self, padding=20)
        form.pack(fill="both", expand=True)

        # Nombre
        ttk.Label(form, text="Nombre de la Categoría (*):", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        self.txt_nombre = ttk.Entry(form, font=("Segoe UI", 10))
        self.txt_nombre.pack(fill="x", pady=(0, 15))
        self.txt_nombre.focus_set()

        # Descripción
        ttk.Label(form, text="Descripción:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        self.txt_desc = ttk.Entry(form, font=("Segoe UI", 10))
        self.txt_desc.pack(fill="x", pady=(0, 15))

        # Checkbox Activo (solo si edita)
        self.var_activo = tk.BooleanVar(value=True)
        if self.categoria:
            self.var_activo.set(self.categoria.activo)
            chk_activo = ttk.Checkbutton(form, text="Categoría Activa", variable=self.var_activo)
            chk_activo.pack(anchor="w", pady=(0, 15))

        # Cargar valores si es edición
        if self.categoria:
            self.txt_nombre.insert(0, self.categoria.nombre)
            self.txt_desc.insert(0, self.categoria.descripcion)

        # Botones de Acción
        btn_box = ttk.Frame(form)
        btn_box.pack(fill="x", side="bottom")

        btn_cancelar = ttk.Button(btn_box, text="Cancelar", style="Secondary.TButton", command=self.destroy)
        btn_cancelar.pack(side="right", padx=5)

        btn_guardar = ttk.Button(btn_box, text="Guardar", style="Primary.TButton", command=self._guardar)
        btn_guardar.pack(side="right", padx=5)

    def _guardar(self):
        nombre = self.txt_nombre.get().strip()
        descripcion = self.txt_desc.get().strip()

        try:
            if self.categoria:
                self.service.actualizar(
                    cat_id=self.categoria.id,
                    nombre=nombre,
                    descripcion=descripcion,
                    activo=self.var_activo.get(),
                    usuario_actual=self.usuario_actual
                )
                messagebox.showinfo("Éxito", "Categoría actualizada correctamente.", parent=self)
            else:
                self.service.crear(
                    nombre=nombre,
                    descripcion=descripcion,
                    usuario_actual=self.usuario_actual
                )
                messagebox.showinfo("Éxito", "Categoría creada con éxito.", parent=self)

            self.on_save()
            self.destroy()
        except ValueError as val_err:
            messagebox.showwarning("Validación", str(val_err), parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"No se pudo guardar la categoría:\n{ex}", parent=self)
