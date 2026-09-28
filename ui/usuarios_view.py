import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from models.usuario import Usuario
from services.auth_service import AuthService
from repositories.bitacora_repository import BitacoraRepository
from ui.theme import ModernTheme


class UsuariosView(ttk.Frame):
    """Gestión de Cuentas de Personal y Auditoría (Solo Administradores - RF-2)."""

    def __init__(self, parent, usuario_actual: Usuario):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.auth_service = AuthService()
        self.bitacora_repo = BitacoraRepository()

        self._crear_interfaz()
        self.cargar_datos()

    def _crear_interfaz(self):
        # 1. Encabezado
        top = ttk.Frame(self, padding=(10, 10, 10, 5))
        top.pack(fill="x")

        lbl_titulo = ttk.Label(top, text="Administración de Personal y Usuarios del Sistema", style="Header.TLabel")
        lbl_titulo.pack(side="left")

        # Botones de Acción
        toolbar = ttk.Frame(self, padding=(10, 5, 10, 10))
        toolbar.pack(fill="x")

        btn_nuevo = ttk.Button(toolbar, text="➕ Registrar Usuario", style="Primary.TButton", command=self._abrir_modal_nuevo)
        btn_nuevo.pack(side="left", padx=5)

        btn_editar = ttk.Button(toolbar, text="✏️ Modificar Cuenta", style="Secondary.TButton", command=self._abrir_modal_editar)
        btn_editar.pack(side="left", padx=5)

        btn_estado = ttk.Button(toolbar, text="🔄 Alternar Activo / Inactivo", style="Secondary.TButton", command=self._alternar_estado)
        btn_estado.pack(side="left", padx=5)

        # 2. Pestañas: Usuarios del Sistema / Bitácora de Auditoría
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=10, pady=5)

        # Tab 1: Cuentas
        tab_users = ttk.Frame(tabs, padding=5)
        tabs.add(tab_users, text="👥 Cuentas de Personal")

        cols = ("id", "username", "rol", "estado")
        self.tree_users = ttk.Treeview(tab_users, columns=cols, show="headings", selectmode="browse")
        self.tree_users.heading("id", text="ID")
        self.tree_users.heading("username", text="Nombre de Usuario")
        self.tree_users.heading("rol", text="Rol Asignado")
        self.tree_users.heading("estado", text="Estado de Acceso")

        self.tree_users.column("id", width=60, anchor="center")
        self.tree_users.column("username", width=220, anchor="w")
        self.tree_users.column("rol", width=180, anchor="center")
        self.tree_users.column("estado", width=140, anchor="center")

        scroll_u = ttk.Scrollbar(tab_users, orient="vertical", command=self.tree_users.yview)
        self.tree_users.configure(yscrollcommand=scroll_u.set)

        self.tree_users.pack(side="left", fill="both", expand=True)
        scroll_u.pack(side="right", fill="y")

        self.tree_users.tag_configure("inactivo", background="#f1f5f9", foreground=ModernTheme.TEXT_MUTED)

        # Tab 2: Bitácora de Acciones (Extra A.6)
        tab_log = ttk.Frame(tabs, padding=5)
        tabs.add(tab_log, text="📜 Bitácora de Auditoría (Extra A.6)")

        b_cols = ("id", "fecha", "usuario", "accion", "detalles")
        self.tree_log = ttk.Treeview(tab_log, columns=b_cols, show="headings", selectmode="browse")
        self.tree_log.heading("id", text="ID")
        self.tree_log.heading("fecha", text="Fecha / Hora")
        self.tree_log.heading("usuario", text="Operador")
        self.tree_log.heading("accion", text="Acción")
        self.tree_log.heading("detalles", text="Detalles")

        self.tree_log.column("id", width=50, anchor="center")
        self.tree_log.column("fecha", width=150, anchor="center")
        self.tree_log.column("usuario", width=120, anchor="w")
        self.tree_log.column("accion", width=170, anchor="center")
        self.tree_log.column("detalles", width=450, anchor="w")

        scroll_b = ttk.Scrollbar(tab_log, orient="vertical", command=self.tree_log.yview)
        self.tree_log.configure(yscrollcommand=scroll_b.set)

        self.tree_log.pack(side="left", fill="both", expand=True)
        scroll_b.pack(side="right", fill="y")

    def cargar_datos(self):
        # 1. Cargar Usuarios
        for item in self.tree_users.get_children():
            self.tree_users.delete(item)

        try:
            usuarios = self.auth_service.listar_usuarios(self.usuario_actual)
            for u in usuarios:
                tag = "normal" if u.activo else "inactivo"
                self.tree_users.insert(
                    "",
                    "end",
                    iid=str(u.id),
                    values=(u.id, u.username, u.rol.capitalize(), u.estado_texto),
                    tags=(tag,)
                )
        except PermissionError as p_err:
            messagebox.showwarning("Restricción", str(p_err), parent=self)
            return

        # 2. Cargar Bitácora
        for item in self.tree_log.get_children():
            self.tree_log.delete(item)

        logs = self.bitacora_repo.listar_recientes(limite=150)
        for lg in logs:
            self.tree_log.insert(
                "",
                "end",
                iid=str(lg.id),
                values=(lg.id, lg.fecha, lg.usuario_nombre, lg.accion, lg.detalles)
            )

    def _get_seleccionado_id(self) -> Optional[int]:
        sel = self.tree_users.selection()
        if not sel:
            messagebox.showinfo("Atención", "Seleccione un usuario de la lista.", parent=self)
            return None
        return int(sel[0])

    def _abrir_modal_nuevo(self):
        UsuarioDialog(self, "Registrar Nuevo Usuario", self.usuario_actual, on_save=self.cargar_datos)

    def _abrir_modal_editar(self):
        uid = self._get_seleccionado_id()
        if uid is None:
            return
        usuarios = self.auth_service.listar_usuarios(self.usuario_actual)
        u_sel = next((u for u in usuarios if u.id == uid), None)
        if not u_sel:
            return
        UsuarioDialog(self, "Modificar Usuario", self.usuario_actual, on_save=self.cargar_datos, usuario=u_sel)

    def _alternar_estado(self):
        uid = self._get_seleccionado_id()
        if uid is None:
            return

        usuarios = self.auth_service.listar_usuarios(self.usuario_actual)
        u_sel = next((u for u in usuarios if u.id == uid), None)
        if not u_sel:
            return

        nuevo_estado = not u_sel.activo
        accion_str = "activar" if nuevo_estado else "desactivar"

        if not messagebox.askyesno("Confirmar", f"¿Desea {accion_str} la cuenta del usuario '{u_sel.username}'?", parent=self):
            return

        try:
            self.auth_service.cambiar_estado(uid, nuevo_estado, self.usuario_actual)
            self.cargar_datos()
            messagebox.showinfo("Éxito", f"Estado de la cuenta actualizado.", parent=self)
        except ValueError as v_err:
            messagebox.showwarning("Atención", str(v_err), parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"No se pudo alterar el estado:\n{ex}", parent=self)


class UsuarioDialog(tk.Toplevel):
    """Modal para registro y edición de credenciales de usuario."""

    def __init__(self, parent, titulo: str, usuario_actual: Usuario, on_save, usuario: Optional[Usuario] = None):
        super().__init__(parent)
        self.title(titulo)
        self.usuario_actual = usuario_actual
        self.usuario = usuario
        self.on_save = on_save
        self.auth_service = AuthService()

        self.geometry("420x360")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Centrar
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 210
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 180
        self.geometry(f"+{x}+{y}")

        self._crear_formulario()

    def _crear_formulario(self):
        form = ttk.Frame(self, padding=20)
        form.pack(fill="both", expand=True)

        ttk.Label(form, text="Nombre de Usuario (*):", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=6)
        self.txt_user = ttk.Entry(form, font=("Segoe UI", 10))
        self.txt_user.grid(row=0, column=1, sticky="ew", pady=6)
        self.txt_user.focus_set()

        lbl_pass_text = "Nueva Contraseña:" if self.usuario else "Contraseña (*):"
        ttk.Label(form, text=lbl_pass_text, font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        self.txt_pass = ttk.Entry(form, show="•", font=("Segoe UI", 10))
        self.txt_pass.grid(row=1, column=1, sticky="ew", pady=6)

        ttk.Label(form, text="Rol del Sistema (*):", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=6)
        self.cbo_rol = ttk.Combobox(form, values=["operador", "administrador"], state="readonly", font=("Segoe UI", 10))
        self.cbo_rol.grid(row=2, column=1, sticky="ew", pady=6)
        self.cbo_rol.set("operador")

        self.var_activo = tk.BooleanVar(value=True)
        if self.usuario:
            self.var_activo.set(self.usuario.activo)
            chk = ttk.Checkbutton(form, text="Cuenta Habilitada / Activa", variable=self.var_activo)
            chk.grid(row=3, column=1, sticky="w", pady=10)

        form.grid_columnconfigure(1, weight=1)

        if self.usuario:
            self.txt_user.insert(0, self.usuario.username)
            self.cbo_rol.set(self.usuario.rol)

        # Botones
        btn_box = ttk.Frame(form)
        btn_box.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(25, 0))

        btn_cancelar = ttk.Button(btn_box, text="Cancelar", style="Secondary.TButton", command=self.destroy)
        btn_cancelar.pack(side="right", padx=5)

        btn_guardar = ttk.Button(btn_box, text="Guardar", style="Primary.TButton", command=self._guardar)
        btn_guardar.pack(side="right", padx=5)

    def _guardar(self):
        username = self.txt_user.get().strip()
        password = self.txt_pass.get()
        rol = self.cbo_rol.get()

        try:
            if self.usuario:
                self.auth_service.actualizar_usuario(
                    usuario_id=self.usuario.id,
                    username=username,
                    rol=rol,
                    activo=self.var_activo.get(),
                    nueva_password=password,
                    usuario_actual=self.usuario_actual
                )
                messagebox.showinfo("Éxito", "Usuario modificado con éxito.", parent=self)
            else:
                self.auth_service.registrar_usuario(
                    username=username,
                    password=password,
                    rol=rol,
                    usuario_actual=self.usuario_actual
                )
                messagebox.showinfo("Éxito", "Usuario registrado exitosamente.", parent=self)

            self.on_save()
            self.destroy()
        except ValueError as v_err:
            messagebox.showwarning("Atención", str(v_err), parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"No se pudo guardar:\n{ex}", parent=self)
