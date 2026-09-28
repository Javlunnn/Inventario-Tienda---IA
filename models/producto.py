from dataclasses import dataclass
from typing import Optional


@dataclass
class Producto:
    """Entidad A del dominio: Artículos o productos del inventario."""
    id: Optional[int]
    codigo: str
    nombre: str
    categoria_id: int
    precio: float
    stock: int
    activo: bool = True
    categoria_nombre: Optional[str] = None  # Campo enriquecido para visualización JOIN

    @property
    def es_stock_bajo(self) -> bool:
        return self.stock <= 5

    @property
    def estado_texto(self) -> str:
        return "Activo" if self.activo else "Inactivo"
