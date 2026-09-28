from dataclasses import dataclass
from typing import Optional


@dataclass
class Bitacora:
    """Registro de auditoría de acciones en el sistema (extra opcional)."""
    id: Optional[int]
    fecha: str
    usuario_id: Optional[int]
    usuario_nombre: str
    accion: str
    detalles: str
