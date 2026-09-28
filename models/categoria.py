from dataclasses import dataclass
from typing import Optional


@dataclass
class Categoria:
    """Entidad B del dominio: Categorías del catálogo de inventario."""
    id: Optional[int]
    nombre: str
    descripcion: str = ""
    activo: bool = True

    @property
    def estado_texto(self) -> str:
        return "Activa" if self.activo else "Inactiva"
