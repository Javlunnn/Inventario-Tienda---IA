from datetime import datetime
from typing import List, Optional
from db.conexion import DatabaseConexion
from models.bitacora import Bitacora


class BitacoraRepository:
    """Acceso a datos para el registro de auditoría / bitácora."""

    def registrar(self, usuario_id: Optional[int], usuario_nombre: str, accion: str, detalles: str = ""):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO bitacora (fecha, usuario_id, usuario_nombre, accion, detalles)
                   VALUES (?, ?, ?, ?, ?)""",
                (fecha, usuario_id, usuario_nombre, accion, detalles)
            )
            conn.commit()

    def listar_recientes(self, limite: int = 150) -> List[Bitacora]:
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM bitacora ORDER BY id DESC LIMIT ?""",
                (limite,)
            )
            rows = cursor.fetchall()
            return [
                Bitacora(
                    id=r["id"],
                    fecha=r["fecha"],
                    usuario_id=r["usuario_id"],
                    usuario_nombre=r["usuario_nombre"],
                    accion=r["accion"],
                    detalles=r["detalles"] or ""
                )
                for r in rows
            ]
