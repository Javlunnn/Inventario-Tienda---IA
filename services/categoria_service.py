import sqlite3
from typing import List, Optional
from models.categoria import Categoria
from models.usuario import Usuario
from repositories.categoria_repository import CategoriaRepository
from repositories.bitacora_repository import BitacoraRepository


class CategoriaService:
    """Reglas de negocio y operaciones sobre Categorías (Entidad B)."""

    def __init__(self):
        self.repo = CategoriaRepository()
        self.bitacora_repo = BitacoraRepository()

    def listar_todas(self, solo_activas: bool = False) -> List[Categoria]:
        return self.repo.listar_todas(solo_activas=solo_activas)

    def buscar(self, termino: str, solo_activas: bool = False) -> List[Categoria]:
        return self.repo.buscar(termino, solo_activas=solo_activas)

    def obtener_por_id(self, cat_id: int) -> Optional[Categoria]:
        return self.repo.obtener_por_id(cat_id)

    def crear(self, nombre: str, descripcion: str, usuario_actual: Usuario) -> int:
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre de la categoría es obligatorio y no puede estar vacío.")

        existente = self.repo.obtener_por_nombre(nombre)
        if existente:
            raise ValueError(f"Ya existe una categoría con el nombre '{nombre}'.")

        cat = Categoria(id=None, nombre=nombre, descripcion=descripcion.strip(), activo=True)
        try:
            nuevo_id = self.repo.crear(cat)
            self.bitacora_repo.registrar(
                usuario_actual.id,
                usuario_actual.username,
                "CREAR_CATEGORIA",
                f"Categoría '{nombre}' creada con ID {nuevo_id}."
            )
            return nuevo_id
        except sqlite3.IntegrityError:
            raise ValueError(f"Violación de unicidad: la categoría '{nombre}' ya existe.")

    def actualizar(self, cat_id: int, nombre: str, descripcion: str, activo: bool, usuario_actual: Usuario) -> bool:
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre de la categoría es obligatorio.")

        cat_existente = self.repo.obtener_por_id(cat_id)
        if not cat_existente:
            raise ValueError("La categoría a modificar no existe.")

        otra = self.repo.obtener_por_nombre(nombre)
        if otra and otra.id != cat_id:
            raise ValueError(f"El nombre '{nombre}' ya está siendo utilizado por otra categoría.")

        cat = Categoria(id=cat_id, nombre=nombre, descripcion=descripcion.strip(), activo=activo)
        res = self.repo.actualizar(cat)
        self.bitacora_repo.registrar(
            usuario_actual.id,
            usuario_actual.username,
            "ACTUALIZAR_CATEGORIA",
            f"Categoría ID {cat_id} actualizada ({nombre})."
        )
        return res

    def cambiar_estado(self, cat_id: int, activo: bool, usuario_actual: Usuario) -> bool:
        res = self.repo.cambiar_estado(cat_id, activo)
        estado_str = "activada" if activo else "desactivada"
        self.bitacora_repo.registrar(
            usuario_actual.id,
            usuario_actual.username,
            "CAMBIAR_ESTADO_CATEGORIA",
            f"La categoría ID {cat_id} fue {estado_str}."
        )
        return res

    def eliminar_o_desactivar(self, cat_id: int, usuario_actual: Usuario) -> bool:
        """
        Integridad referencial (RF-10):
        Si la categoría tiene productos asociados, no se puede eliminar físicamente;
        se ofrece o aplica desactivarla para mantener la consistencia histórica.
        """
        prods_asociados = self.repo.contar_productos_asociados(cat_id)
        if prods_asociados > 0:
            raise ValueError(
                f"No es posible eliminar la categoría porque tiene {prods_asociados} producto(s) asociado(s). "
                "Para preservar la integridad referencial, desactive la categoría en lugar de eliminarla."
            )

        res = self.repo.eliminar(cat_id)
        self.bitacora_repo.registrar(
            usuario_actual.id,
            usuario_actual.username,
            "ELIMINAR_CATEGORIA",
            f"Se eliminó permanentemente la categoría con ID {cat_id}."
        )
        return res
