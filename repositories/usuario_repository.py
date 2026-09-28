from typing import List, Optional
from db.conexion import DatabaseConexion
from models.usuario import Usuario


class UsuarioRepository:
    """Acceso a datos para usuarios_sistema."""

    @staticmethod
    def _mapear(row) -> Usuario:
        return Usuario(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            rol=row["rol"],
            activo=bool(row["activo"])
        )

    def obtener_por_id(self, usuario_id: int) -> Optional[Usuario]:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios_sistema WHERE id = ?", (usuario_id,))
            row = cursor.fetchone()
            return self._mapear(row) if row else None

    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios_sistema WHERE username = ?", (username,))
            row = cursor.fetchone()
            return self._mapear(row) if row else None

    def listar_todos(self) -> List[Usuario]:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios_sistema ORDER BY id ASC")
            return [self._mapear(r) for r in cursor.fetchall()]

    def crear(self, usuario: Usuario) -> int:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO usuarios_sistema (username, password_hash, rol, activo)
                   VALUES (?, ?, ?, ?)""",
                (usuario.username, usuario.password_hash, usuario.rol, 1 if usuario.activo else 0)
            )
            conn.commit()
            return cursor.lastrowid

    def actualizar(self, usuario: Usuario) -> bool:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            if usuario.password_hash:
                cursor.execute(
                    """UPDATE usuarios_sistema
                       SET username = ?, password_hash = ?, rol = ?, activo = ?
                       WHERE id = ?""",
                    (usuario.username, usuario.password_hash, usuario.rol, 1 if usuario.activo else 0, usuario.id)
                )
            else:
                cursor.execute(
                    """UPDATE usuarios_sistema
                       SET username = ?, rol = ?, activo = ?
                       WHERE id = ?""",
                    (usuario.username, usuario.rol, 1 if usuario.activo else 0, usuario.id)
                )
            conn.commit()
            return cursor.rowcount > 0

    def cambiar_estado(self, usuario_id: int, activo: bool) -> bool:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios_sistema SET activo = ? WHERE id = ?",
                (1 if activo else 0, usuario_id)
            )
            conn.commit()
            return cursor.rowcount > 0
