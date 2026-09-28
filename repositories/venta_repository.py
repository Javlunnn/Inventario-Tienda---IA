from datetime import datetime
import sqlite3
from typing import Dict, List, Optional, Tuple
from db.conexion import DatabaseConexion
from models.venta import DetalleVenta, Venta


class VentaRepository:
    """Acceso a datos y transacciones para el movimiento de ventas y sus detalles."""

    def generar_siguiente_folio(self) -> str:
        """Genera un folio secuencial único con prefijo de fecha (ej. VNT-20260925-0001)."""
        fecha_prefijo = datetime.now().strftime("%Y%m%d")
        patron = f"VNT-{fecha_prefijo}-%"
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT folio FROM ventas WHERE folio LIKE ? ORDER BY id DESC LIMIT 1",
                (patron,)
            )
            row = cursor.fetchone()
            if row:
                ultimo_folio = row["folio"]
                secuencia = int(ultimo_folio.split("-")[-1]) + 1
            else:
                secuencia = 1
            return f"VNT-{fecha_prefijo}-{secuencia:04d}"

    def registrar_venta_transaccional(self, venta: Venta) -> int:
        """
        Ejecuta el proceso atómico de venta (RF-5, Opción 2):
        1. Inserta la cabecera en 'ventas'.
        2. Inserta cada ítem en 'detalle_venta' copiando precio_unitario actual.
        3. Descuenta el stock en 'productos' validando que no quede negativo.
        Si algo falla, realiza rollback automático.
        """
        conn = DatabaseConexion.get_connection()
        try:
            cursor = conn.cursor()
            # 1. Cabecera de venta
            cursor.execute(
                """INSERT INTO ventas (folio, fecha, usuario_id, total, notas)
                   VALUES (?, ?, ?, ?, ?)""",
                (venta.folio, venta.fecha, venta.usuario_id, venta.total, venta.notas or "")
            )
            venta_id = cursor.lastrowid

            # 2. Detalles y descuento de stock
            for item in venta.detalles:
                # Verificar stock disponible actual con bloqueo
                cursor.execute(
                    "SELECT stock, activo, nombre FROM productos WHERE id = ?",
                    (item.producto_id,)
                )
                prod_row = cursor.fetchone()
                if not prod_row:
                    raise ValueError(f"El producto con ID {item.producto_id} no existe.")
                if not prod_row["activo"]:
                    raise ValueError(f"El producto '{prod_row['nombre']}' se encuentra inactivo y no puede venderse.")
                if prod_row["stock"] < item.cantidad:
                    raise ValueError(
                        f"Stock insuficiente para '{prod_row['nombre']}'. Disponible: {prod_row['stock']}, Solicitado: {item.cantidad}."
                    )

                # Descontar stock
                cursor.execute(
                    "UPDATE productos SET stock = stock - ? WHERE id = ?",
                    (item.cantidad, item.producto_id)
                )

                # Insertar detalle copiando precio_unitario
                cursor.execute(
                    """INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                       VALUES (?, ?, ?, ?, ?)""",
                    (venta_id, item.producto_id, item.cantidad, item.precio_unitario, item.subtotal)
                )

            conn.commit()
            return venta_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def listar_ventas(self, termino: str = "") -> List[Dict]:
        """Listado de ventas con JOIN a usuarios_sistema (RF-7)."""
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT v.id, v.folio, v.fecha, v.total, v.notas,
                       u.username as usuario_nombre,
                       (SELECT COUNT(*) FROM detalle_venta d WHERE d.venta_id = v.id) as articulos_distintos,
                       (SELECT SUM(d.cantidad) FROM detalle_venta d WHERE d.venta_id = v.id) as total_piezas
                FROM ventas v
                JOIN usuarios_sistema u ON v.usuario_id = u.id
                WHERE 1=1
            """
            params = []
            if termino.strip():
                patt = f"%{termino.strip()}%"
                sql += " AND (v.folio LIKE ? OR u.username LIKE ? OR v.fecha LIKE ?)"
                params.extend([patt, patt, patt])

            sql += " ORDER BY v.id DESC"
            cursor.execute(sql, params)
            return [dict(r) for r in cursor.fetchall()]

    def obtener_venta_por_id(self, venta_id: int) -> Optional[Dict]:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT v.*, u.username as usuario_nombre
                   FROM ventas v
                   JOIN usuarios_sistema u ON v.usuario_id = u.id
                   WHERE v.id = ?""",
                (venta_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def obtener_detalles_de_venta(self, venta_id: int) -> List[Dict]:
        """Obtiene los detalles de una venta con JOIN a productos y categorías."""
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT d.*, p.codigo as producto_codigo, p.nombre as producto_nombre,
                          c.nombre as categoria_nombre
                   FROM detalle_venta d
                   JOIN productos p ON d.producto_id = p.id
                   JOIN categorias c ON p.categoria_id = c.id
                   WHERE d.venta_id = ?
                   ORDER BY d.id ASC""",
                (venta_id,)
            )
            return [dict(r) for r in cursor.fetchall()]

    def listar_todos_los_movimientos_join(self, termino: str = "") -> List[Dict]:
        """
        JOIN OBLIGATORIO (RF-7, Opción 2):
        detalle_venta + nombre del producto + folio de venta + usuario_nombre + categoría.
        """
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT d.id as detalle_id,
                       v.id as venta_id,
                       v.folio as venta_folio,
                       v.fecha as venta_fecha,
                       u.username as cajero_nombre,
                       p.codigo as producto_codigo,
                       p.nombre as producto_nombre,
                       c.nombre as categoria_nombre,
                       d.cantidad,
                       d.precio_unitario,
                       d.subtotal
                FROM detalle_venta d
                JOIN ventas v ON d.venta_id = v.id
                JOIN usuarios_sistema u ON v.usuario_id = u.id
                JOIN productos p ON d.producto_id = p.id
                JOIN categorias c ON p.categoria_id = c.id
                WHERE 1=1
            """
            params = []
            if termino.strip():
                patt = f"%{termino.strip()}%"
                sql += """ AND (v.folio LIKE ? OR p.codigo LIKE ? OR p.nombre LIKE ?
                                OR u.username LIKE ? OR c.nombre LIKE ?)"""
                params.extend([patt, patt, patt, patt, patt])

            sql += " ORDER BY d.id DESC"
            cursor.execute(sql, params)
            return [dict(r) for r in cursor.fetchall()]

    def obtener_resumen_mas_vendidos(self, limite: int = 10) -> List[Dict]:
        """Reporte analítico de productos con mayor número de unidades vendidas."""
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT p.codigo, p.nombre, c.nombre as categoria_nombre,
                          SUM(d.cantidad) as total_unidades,
                          SUM(d.subtotal) as monto_generado
                   FROM detalle_venta d
                   JOIN productos p ON d.producto_id = p.id
                   JOIN categorias c ON p.categoria_id = c.id
                   GROUP BY p.id, p.codigo, p.nombre, c.nombre
                   ORDER BY total_unidades DESC
                   LIMIT ?""",
                (limite,)
            )
            return [dict(r) for r in cursor.fetchall()]
