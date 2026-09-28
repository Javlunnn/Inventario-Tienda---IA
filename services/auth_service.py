import hashlib
import sqlite3
from typing import List, Optional
from models.usuario import Usuario
from repositories.usuario_repository import UsuarioRepository
from repositories.bitacora_repository import BitacoraRepository


class AuthService:
    """Gestiona autenticación, hash seguro (RF-3) y roles de usuario (RF-2)."""

    def __init__(self):
        self.usuario_repo = UsuarioRepository()
        self.bitacora_repo = BitacoraRepository()

    @staticmethod
    def generar_hash(password: str) -> str:
        """Hash SHA-256 para almacenamiento seguro de credenciales (RF-3)."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def autenticar(self, username: str, password: str) -> Usuario:
        """
        Valida credenciales de acceso.
        Lanza ValueError si el usuario no existe, la clave es incorrecta o está inactivo.
        """
        if not username.strip() or not password:
            raise ValueError("Por favor ingrese su usuario y contraseña.")

        usuario = self.usuario_repo.obtener_por_username(username.strip())
        if not usuario:
            raise ValueError("Usuario o contraseña incorrectos.")

        # Requisito A.4: No entrar si el usuario está inactivo
        if not usuario.activo:
            raise ValueError("La cuenta de este usuario se encuentra inactiva. Contacte al administrador.")

        hash_ingresado = self.generar_hash(password)
        if usuario.password_hash != hash_ingresado:
            raise ValueError("Usuario o contraseña incorrectos.")

        self.bitacora_repo.registrar(
            usuario.id,
            usuario.username,
            "LOGIN",
            f"Inicio de sesión exitoso con rol '{usuario.rol}'."
        )
        return usuario

    def listar_usuarios(self, usuario_actual: Usuario) -> List[Usuario]:
        """Solo administradores pueden consultar el listado de usuarios (RF-2)."""
        if not usuario_actual.es_administrador:
            raise PermissionError("Acceso denegado: El operador no puede gestionar cuentas del personal.")
        return self.usuario_repo.listar_todos()

    def registrar_usuario(self, username: str, password: str, rol: str, usuario_actual: Usuario) -> int:
        """Solo administradores pueden crear usuarios (RF-2)."""
        if not usuario_actual.es_administrador:
            raise PermissionError("Acceso denegado: Solo el administrador puede crear usuarios.")

        username = username.strip()
        if len(username) < 3:
            raise ValueError("El nombre de usuario debe contener al menos 3 caracteres.")
        if len(password) < 4:
            raise ValueError("La contraseña debe tener al menos 4 caracteres.")
        if rol not in ("administrador", "operador"):
            raise ValueError("El rol debe ser 'administrador' u 'operador'.")

        existente = self.usuario_repo.obtener_por_username(username)
        if existente:
            raise ValueError(f"El nombre de usuario '{username}' ya está en uso.")

        nuevo_usuario = Usuario(
            id=None,
            username=username,
            password_hash=self.generar_hash(password),
            rol=rol,
            activo=True
        )

        try:
            nuevo_id = self.usuario_repo.crear(nuevo_usuario)
            self.bitacora_repo.registrar(
                usuario_actual.id,
                usuario_actual.username,
                "CREAR_USUARIO",
                f"Se creó el usuario '{username}' con rol '{rol}'."
            )
            return nuevo_id
        except sqlite3.IntegrityError:
            raise ValueError(f"El usuario '{username}' ya se encuentra registrado.")

    def actualizar_usuario(
        self,
        usuario_id: int,
        username: str,
        rol: str,
        activo: bool,
        nueva_password: Optional[str],
        usuario_actual: Usuario
    ) -> bool:
        """Actualiza datos de un usuario."""
        if not usuario_actual.es_administrador:
            raise PermissionError("Acceso denegado: Solo el administrador puede modificar usuarios.")

        username = username.strip()
        if len(username) < 3:
            raise ValueError("El nombre de usuario debe contener al menos 3 caracteres.")

        usuario = self.usuario_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError("El usuario especificado no existe.")

        # Si se cambia el username, verificar que no colisione con otro
        otro = self.usuario_repo.obtener_por_username(username)
        if otro and otro.id != usuario_id:
            raise ValueError(f"El nombre de usuario '{username}' ya está siendo utilizado por otra cuenta.")

        usuario.username = username
        usuario.rol = rol
        usuario.activo = activo
        if nueva_password and nueva_password.strip():
            if len(nueva_password) < 4:
                raise ValueError("La nueva contraseña debe tener al menos 4 caracteres.")
            usuario.password_hash = self.generar_hash(nueva_password)
        else:
            usuario.password_hash = ""  # Mantener existente

        res = self.usuario_repo.actualizar(usuario)
        self.bitacora_repo.registrar(
            usuario_actual.id,
            usuario_actual.username,
            "ACTUALIZAR_USUARIO",
            f"Se actualizó la información del usuario '{username}'."
        )
        return res

    def cambiar_estado(self, usuario_id: int, activo: bool, usuario_actual: Usuario) -> bool:
        """Activa o desactiva un usuario."""
        if not usuario_actual.es_administrador:
            raise PermissionError("Acceso denegado: Solo el administrador puede alterar estados de usuarios.")

        if usuario_actual.id == usuario_id and not activo:
            raise ValueError("No puede desactivar su propia cuenta de administrador en sesión.")

        res = self.usuario_repo.cambiar_estado(usuario_id, activo)
        estado_str = "activado" if activo else "desactivado"
        self.bitacora_repo.registrar(
            usuario_actual.id,
            usuario_actual.username,
            "CAMBIAR_ESTADO_USUARIO",
            f"El usuario con ID {usuario_id} fue {estado_str}."
        )
        return res
