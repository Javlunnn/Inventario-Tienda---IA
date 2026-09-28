"""Módulo de repositorios de persistencia relacional con SQLite."""
from .usuario_repository import UsuarioRepository
from .categoria_repository import CategoriaRepository
from .producto_repository import ProductoRepository
from .venta_repository import VentaRepository
from .bitacora_repository import BitacoraRepository

__all__ = [
    "UsuarioRepository",
    "CategoriaRepository",
    "ProductoRepository",
    "VentaRepository",
    "BitacoraRepository"
]
