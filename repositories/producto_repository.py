import sqlite3
from typing import List, Optional
from db.conexion import DatabaseConexion
from models.producto import Producto


class ProductoRepository:
    """Acceso a datos para productos (Entidad A) con consultas JOIN."""

    @staticmethod
    def _mapear(row) -> Producto:
        return Producto(
            id=row["id"],
            codigo=row["codigo"],
            nombre=row["nombre"],
            categoria_id=row["categoria_id"],
            precio=float(row["precio"]),
            stock=int(row["stock"]),
            activo=bool(row["activo"]),
            categoria_nombre=row["categoria_nombre"] if "categoria_nombre" in row.keys() else None
        )

    def obtener_por_id(self, prod_id: int) -> Optional[Producto]:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT p.*, c.nombre as categoria_nombre
                   FROM productos p
                   JOIN categorias c ON p.categoria_id = c.id
                   WHERE p.id = ?""",
                (prod_id,)
            )
            row = cursor.fetchone()
            return self._mapear(row) if row else None

    def obtener_por_codigo(self, codigo: str) -> Optional[Producto]:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT p.*, c.nombre as categoria_nombre
                   FROM productos p
                   JOIN categorias c ON p.categoria_id = c.id
                   WHERE UPPER(p.codigo) = UPPER(?)""",
                (codigo.strip(),)
            )
            row = cursor.fetchone()
            return self._mapear(row) if row else None

    def listar_todos(self, solo_activos: bool = False) -> List[Producto]:
        """Consulta con JOIN obligatorio (RF-7) entre productos y categorías."""
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT p.*, c.nombre as categoria_nombre
                FROM productos p
                JOIN categorias c ON p.categoria_id = c.id
            """
            if solo_activos:
                sql += " WHERE p.activo = 1"
            sql += " ORDER BY p.nombre ASC"
            cursor.execute(sql)
            return [self._mapear(r) for r in cursor.fetchall()]

    def buscar(self, termino: str = "", categoria_id: Optional[int] = None, solo_activos: bool = False) -> List[Producto]:
        """Búsqueda y filtro con JOIN para el Treeview (RF-6, RF-7)."""
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT p.*, c.nombre as categoria_nombre
                FROM productos p
                JOIN categorias c ON p.categoria_id = c.id
                WHERE 1=1
            """
            params = []
            if termino.strip():
                pattern = f"%{termino.strip()}%"
                sql += " AND (p.codigo LIKE ? OR p.nombre LIKE ?)"
                params.extend([pattern, pattern])

            if categoria_id is not None and categoria_id > 0:
                sql += " AND p.categoria_id = ?"
                params.append(categoria_id)

            if solo_activos:
                sql += " AND p.activo = 1"

            sql += " ORDER BY p.nombre ASC"
            cursor.execute(sql, params)
            return [self._mapear(r) for r in cursor.fetchall()]

    def crear(self, prod: Producto) -> int:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO productos (codigo, nombre, categoria_id, precio, stock, activo)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (prod.codigo.strip(), prod.nombre.strip(), prod.categoria_id, prod.precio, prod.stock, 1 if prod.activo else 0)
            )
            conn.commit()
            return cursor.lastrowid

    def actualizar(self, prod: Producto) -> bool:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE productos
                   SET codigo = ?, nombre = ?, categoria_id = ?, precio = ?, stock = ?, activo = ?
                   WHERE id = ?""",
                (prod.codigo.strip(), prod.nombre.strip(), prod.categoria_id, prod.precio, prod.stock, 1 if prod.activo else 0, prod.id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def cambiar_estado(self, prod_id: int, activo: bool) -> bool:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE productos SET activo = ? WHERE id = ?",
                (1 if activo else 0, prod_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def contar_ventas_asociadas(self, prod_id: int) -> int:
        """Verifica si el producto tiene historial de ventas (RF-10)."""
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM detalle_venta WHERE producto_id = ?", (prod_id,))
            row = cursor.fetchone()
            return row["total"] if row else 0

    def eliminar(self, prod_id: int) -> bool:
        """Elimina físicamente si no tiene ventas registradas (RF-10)."""
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM productos WHERE id = ?", (prod_id,))
            conn.commit()
            return cursor.rowcount > 0

    def obtener_stock_bajo(self, umbral: int = 5) -> List[Producto]:
        """Reporte del caso problemático del dominio: Stock Bajo (RF-8)."""
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT p.*, c.nombre as categoria_nombre
                   FROM productos p
                   JOIN categorias c ON p.categoria_id = c.id
                   WHERE p.stock <= ? AND p.activo = 1
                   ORDER BY p.stock ASC, p.nombre ASC""",
                (umbral,)
            )
            return [self._mapear(r) for r in cursor.fetchall()]
