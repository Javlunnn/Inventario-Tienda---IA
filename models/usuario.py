from dataclasses import dataclass
from typing import Optional


@dataclass
class Usuario:
    """Representa a un usuario del sistema (administrador u operador)."""
    id: Optional[int]
    username: str
    password_hash: str
    rol: str  # 'administrador' | 'operador'
    activo: bool = True

    @property
    def es_administrador(self) -> bool:
        return self.rol.lower() == "administrador"

    @property
    def estado_texto(self) -> str:
        return "Activo" if self.activo else "Inactivo"
