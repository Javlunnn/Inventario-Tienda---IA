from datetime import datetime
from typing import Dict, List, Optional
from models.usuario import Usuario
from models.venta import DetalleVenta, Venta
from repositories.venta_repository import VentaRepository
from repositories.producto_repository import ProductoRepository
from repositories.bitacora_repository import BitacoraRepository


class VentaService:
    """Reglas de negocio y orquestación del proceso de ventas (RF-5)."""

    def __init__(self):
        self.venta_repo = VentaRepository()
        self.prod_repo = ProductoRepository()
        self.bitacora_repo = BitacoraRepository()

    def procesar_venta(
        self,
        usuario_actual: Usuario,
        items_carrito: List[Dict],
        notas: str = ""
    ) -> Tuple[int, str]:
        """
        Ejecuta el proceso de negocio de la venta:
        - Valida que el carrito tenga al menos 1 producto.
        - Valida stock disponible y estado activo de cada producto.
        - Descuenta stock de manera atómica y registra cabecera y detalles.
        Retorna (venta_id, folio).
        """
        if not items_carrito:
            raise ValueError("El carrito de compras está vacío. Agregue al menos un producto.")

        total_venta = 0.0
        detalles_venta: List[DetalleVenta] = []

        for item in items_carrito:
            prod_id = item["producto_id"]
            cantidad = item["cantidad"]

            if cantidad <= 0:
                raise ValueError("La cantidad de cada producto debe ser mayor a 0.")

            producto = self.prod_repo.obtener_por_id(prod_id)
            if not producto:
                raise ValueError(f"El producto seleccionado (ID: {prod_id}) no existe en catálogo.")

            if not producto.activo:
                raise ValueError(f"El producto '{producto.nombre}' está marcado como INACTIVO y no puede venderse.")

            if producto.stock < cantidad:
                raise ValueError(
                    f"Stock insuficiente para '{producto.nombre}'. "
                    f"Existencia en almacén: {producto.stock}, Solicitado en venta: {cantidad}."
                )

            # precio_unitario se copia al detalle congelando el valor en este momento
            precio_unitario = float(producto.precio)
            subtotal = round(precio_unitario * cantidad, 2)
            total_venta += subtotal

            detalles_venta.append(
                DetalleVenta(
                    id=None,
                    venta_id=None,
                    producto_id=prod_id,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal,
                    producto_codigo=producto.codigo,
                    producto_nombre=producto.nombre
                )
            )

        total_venta = round(total_venta, 2)
        folio = self.venta_repo.generar_siguiente_folio()
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        venta = Venta(
            id=None,
            folio=folio,
            fecha=fecha_actual,
            usuario_id=usuario_actual.id,
            total=total_venta,
            notas=notas.strip(),
            detalles=detalles_venta
        )

        venta_id = self.venta_repo.registrar_venta_transaccional(venta)

        self.bitacora_repo.registrar(
            usuario_actual.id,
            usuario_actual.username,
            "REGISTRO_VENTA",
            f"Venta '{folio}' registrada por ${total_venta:.2f} con {len(detalles_venta)} artículo(s)."
        )

        return venta_id, folio

    def listar_ventas(self, termino: str = "") -> List[Dict]:
        return self.venta_repo.listar_ventas(termino=termino)

    def obtener_venta_completa(self, venta_id: int) -> Optional[Dict]:
        cabecera = self.venta_repo.obtener_venta_por_id(venta_id)
        if not cabecera:
            return None
        detalles = self.venta_repo.obtener_detalles_de_venta(venta_id)
        cabecera["detalles"] = detalles
        return cabecera

    def listar_movimientos_con_join(self, termino: str = "") -> List[Dict]:
        """Consulta con JOIN obligatorio según especificación (RF-7)."""
        return self.venta_repo.listar_todos_los_movimientos_join(termino=termino)
