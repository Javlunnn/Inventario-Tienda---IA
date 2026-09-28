import sqlite3
from typing import List, Optional
from db.conexion import DatabaseConexion
from models.categoria import Categoria


class CategoriaRepository:
    """Acceso a datos para categorías (Entidad B)."""

    @staticmethod
    def _mapear(row) -> Categoria:
        return Categoria(
            id=row["id"],
            nombre=row["nombre"],
            descripcion=row["descripcion"] or "",
            activo=bool(row["activo"])
        )

    def obtener_por_id(self, cat_id: int) -> Optional[Categoria]:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categorias WHERE id = ?", (cat_id,))
            row = cursor.fetchone()
            return self._mapear(row) if row else None

    def obtener_por_nombre(self, nombre: str) -> Optional[Categoria]:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categorias WHERE LOWER(nombre) = LOWER(?)", (nombre.strip(),))
            row = cursor.fetchone()
            return self._mapear(row) if row else None

    def listar_todas(self, solo_activas: bool = False) -> List[Categoria]:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM categorias"
            if solo_activas:
                sql += " WHERE activo = 1"
            sql += " ORDER BY nombre ASC"
            cursor.execute(sql)
            return [self._mapear(r) for r in cursor.fetchall()]

    def buscar(self, termino: str, solo_activas: bool = False) -> List[Categoria]:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            pattern = f"%{termino.strip()}%"
            sql = "SELECT * FROM categorias WHERE (nombre LIKE ? OR descripcion LIKE ?)"
            params = [pattern, pattern]
            if solo_activas:
                sql += " AND activo = 1"
            sql += " ORDER BY nombre ASC"
            cursor.execute(sql, params)
            return [self._mapear(r) for r in cursor.fetchall()]

    def crear(self, categoria: Categoria) -> int:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO categorias (nombre, descripcion, activo) VALUES (?, ?, ?)",
                (categoria.nombre.strip(), categoria.descripcion.strip(), 1 if categoria.activo else 0)
            )
            conn.commit()
            return cursor.lastrowid

    def actualizar(self, categoria: Categoria) -> bool:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE categorias SET nombre = ?, descripcion = ?, activo = ? WHERE id = ?",
                (categoria.nombre.strip(), categoria.descripcion.strip(), 1 if categoria.activo else 0, categoria.id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def cambiar_estado(self, cat_id: int, activo: bool) -> bool:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE categorias SET activo = ? WHERE id = ?",
                (1 if activo else 0, cat_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def contar_productos_asociados(self, cat_id: int) -> int:
        """Verifica productos relacionados para preservar integridad referencial (RF-10)."""
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM productos WHERE categoria_id = ?", (cat_id,))
            row = cursor.fetchone()
            return row["total"] if row else 0

    def eliminar(self, cat_id: int) -> bool:
        """Elimina físicamente solo si no tiene productos dependientes (RF-10)."""
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categorias WHERE id = ?", (cat_id,))
            conn.commit()
            return cursor.rowcount > 0
