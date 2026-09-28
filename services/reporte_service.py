import csv
from typing import Dict, List, Optional
from db.conexion import DatabaseConexion
from repositories.producto_repository import ProductoRepository
from repositories.venta_repository import VentaRepository


class ReporteService:
    """Generación de reportes analíticos del dominio y exportación a CSV (RF-8, A.6)."""

    def __init__(self):
        self.prod_repo = ProductoRepository()
        self.venta_repo = VentaRepository()

    def reporte_stock_bajo(self, umbral: int = 5) -> List[Dict]:
        """
        Reporte del caso 'problemático' del dominio (RF-8):
        Productos cuyo stock es menor o igual al umbral especificado.
        """
        prods = self.prod_repo.obtener_stock_bajo(umbral=umbral)
        resultado = []
        for p in prods:
            nivel_alerta = "CRÍTICO (Agotado)" if p.stock == 0 else "BAJO (Reabastecer)"
            resultado.append({
                "id": p.id,
                "codigo": p.codigo,
                "nombre": p.nombre,
                "categoria": p.categoria_nombre or "Sin categoría",
                "precio": f"${p.precio:.2f}",
                "stock": p.stock,
                "alerta": nivel_alerta
            })
        return resultado

    def reporte_mas_vendidos(self, limite: int = 15) -> List[Dict]:
        """Reporte de los productos más vendidos con monto acumulado."""
        return self.venta_repo.obtener_resumen_mas_vendidos(limite=limite)

    def obtener_resumen_kpi(self) -> Dict:
        """Calcula métricas clave del sistema para el panel general."""
        with DatabaseConexion.get_connection() as conn:
            cursor = conn.cursor()

            # Total de productos y valor de inventario
            cursor.execute("""
                SELECT COUNT(*) as total_prods,
                       COALESCE(SUM(stock), 0) as total_unidades,
                       COALESCE(SUM(precio * stock), 0) as valor_almacen
                FROM productos
                WHERE activo = 1
            """)
            prod_row = cursor.fetchone()

            # Productos con stock bajo
            cursor.execute("SELECT COUNT(*) as total_bajos FROM productos WHERE stock <= 5 AND activo = 1")
            bajos_row = cursor.fetchone()

            # Total de ventas y monto recaudado
            cursor.execute("""
                SELECT COUNT(*) as total_ventas,
                       COALESCE(SUM(total), 0) as recaudacion_total
                FROM ventas
            """)
            ventas_row = cursor.fetchone()

            # Total de categorías
            cursor.execute("SELECT COUNT(*) as total_cats FROM categorias WHERE activo = 1")
            cats_row = cursor.fetchone()

            return {
                "total_productos": prod_row["total_prods"] if prod_row else 0,
                "total_unidades": prod_row["total_unidades"] if prod_row else 0,
                "valor_almacen": prod_row["valor_almacen"] if prod_row else 0.0,
                "stock_bajo_count": bajos_row["total_bajos"] if bajos_row else 0,
                "total_ventas": ventas_row["total_ventas"] if ventas_row else 0,
                "recaudacion_total": ventas_row["recaudacion_total"] if ventas_row else 0.0,
                "total_categorias": cats_row["total_cats"] if cats_row else 0
            }

    @staticmethod
    def exportar_a_csv(ruta_archivo: str, encabezados: List[str], filas: List[List]) -> bool:
        """Exporta cualquier conjunto tabular a formato CSV (Extra A.6)."""
        with open(ruta_archivo, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(encabezados)
            writer.writerows(filas)
        return True
