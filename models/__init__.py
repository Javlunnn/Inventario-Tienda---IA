"""
Módulo de modelos de dominio para el sistema de Inventario y Punto de Venta.
Representan entidades puras de la lógica de negocio sin dependencias de GUI ni SQL.
"""

from .usuario import Usuario
from .categoria import Categoria
from .producto import Producto
from .venta import Venta, DetalleVenta
from .bitacora import Bitacora

__all__ = ["Usuario", "Categoria", "Producto", "Venta", "DetalleVenta", "Bitacora"]
