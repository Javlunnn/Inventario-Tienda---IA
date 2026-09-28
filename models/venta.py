from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DetalleVenta:
    """Ítem individual dentro de una venta."""
    id: Optional[int]
    venta_id: Optional[int]
    producto_id: int
    cantidad: int
    precio_unitario: float
    subtotal: float
    producto_codigo: Optional[str] = None
    producto_nombre: Optional[str] = None


@dataclass
class Venta:
    """Movimiento principal de negocio que relaciona usuarios y productos."""
    id: Optional[int]
    folio: str
    fecha: str
    usuario_id: int
    total: float
    notas: str = ""
    detalles: List[DetalleVenta] = field(default_factory=list)
    usuario_nombre: Optional[str] = None
