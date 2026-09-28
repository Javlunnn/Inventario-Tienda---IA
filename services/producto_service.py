import sqlite3
from typing import List, Optional
from models.producto import Producto
from models.usuario import Usuario
from repositories.producto_repository import ProductoRepository
from repositories.categoria_repository import CategoriaRepository
from repositories.bitacora_repository import BitacoraRepository


class ProductoService:
    """Reglas de negocio y operaciones para Productos (Entidad A)."""

    def __init__(self):
        self.repo = ProductoRepository()
        self.cat_repo = CategoriaRepository()
        self.bitacora_repo = BitacoraRepository()

    def listar_todos(self, solo_activos: bool = False) -> List[Producto]:
        return self.repo.listar_todos(solo_activos=solo_activos)

    def buscar(self, termino: str = "", categoria_id: Optional[int] = None, solo_activos: bool = False) -> List[Producto]:
        return self.repo.buscar(termino=termino, categoria_id=categoria_id, solo_activos=solo_activos)

    def obtener_por_id(self, prod_id: int) -> Optional[Producto]:
        return self.repo.obtener_por_id(prod_id)

    def obtener_por_codigo(self, codigo: str) -> Optional[Producto]:
        return self.repo.obtener_por_codigo(codigo)

    def crear(
        self,
        codigo: str,
        nombre: str,
        categoria_id: int,
        precio_str: str,
        stock_str: str,
        usuario_actual: Usuario
    ) -> int:
        codigo = codigo.strip().upper()
        nombre = nombre.strip()

        if not codigo:
            raise ValueError("El código del producto es obligatorio.")
        if not nombre:
            raise ValueError("El nombre del producto es obligatorio.")

        # Validaciones numéricas (RNF-4)
        try:
            precio = float(precio_str)
            if precio <= 0:
                raise ValueError()
        except ValueError:
            raise ValueError("El precio debe ser un número decimal estrictamente mayor a 0 (ej. 25.50).")

        try:
            stock = int(stock_str)
            if stock < 0:
                raise ValueError()
        except ValueError:
            raise ValueError("El stock debe ser un número entero mayor o igual a 0.")

        # Validar existencia de categoría
        cat = self.cat_repo.obtener_por_id(categoria_id)
        if not cat:
            raise ValueError("La categoría seleccionada no existe.")
        if not cat.activo:
            raise ValueError(f"La categoría '{cat.nombre}' está inactiva. No se pueden registrar productos en categorías inactivas.")

        # Validar unicidad de código
        existente = self.repo.obtener_por_codigo(codigo)
        if existente:
            raise ValueError(f"Ya existe un producto registrado con el código '{codigo}'.")

        prod = Producto(
            id=None,
            codigo=codigo,
            nombre=nombre,
            categoria_id=categoria_id,
            precio=precio,
            stock=stock,
            activo=True
        )

        try:
            nuevo_id = self.repo.crear(prod)
            self.bitacora_repo.registrar(
                usuario_actual.id,
                usuario_actual.username,
                "CREAR_PRODUCTO",
                f"Producto '{nombre}' ({codigo}) creado con stock {stock} y precio ${precio:.2f}."
            )
            return nuevo_id
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Error de integridad en base de datos: {e}")

    def actualizar(
        self,
        prod_id: int,
        codigo: str,
        nombre: str,
        categoria_id: int,
        precio_str: str,
        stock_str: str,
        activo: bool,
        usuario_actual: Usuario
    ) -> bool:
        codigo = codigo.strip().upper()
        nombre = nombre.strip()

        if not codigo:
            raise ValueError("El código del producto es obligatorio.")
        if not nombre:
            raise ValueError("El nombre del producto es obligatorio.")

        try:
            precio = float(precio_str)
            if precio <= 0:
                raise ValueError()
        except ValueError:
            raise ValueError("El precio debe ser un número decimal mayor a 0.")

        try:
            stock = int(stock_str)
            if stock < 0:
                raise ValueError()
        except ValueError:
            raise ValueError("El stock debe ser un número entero mayor o igual a 0.")

        existente = self.repo.obtener_por_id(prod_id)
        if not existente:
            raise ValueError("El producto a modificar no existe.")

        otro = self.repo.obtener_por_codigo(codigo)
        if otro and otro.id != prod_id:
            raise ValueError(f"El código '{codigo}' ya está asignado a otro producto.")

        cat = self.cat_repo.obtener_por_id(categoria_id)
        if not cat:
            raise ValueError("La categoría seleccionada no existe.")

        prod = Producto(
            id=prod_id,
            codigo=codigo,
            nombre=nombre,
            categoria_id=categoria_id,
            precio=precio,
            stock=stock,
            activo=activo
        )

        res = self.repo.actualizar(prod)
        self.bitacora_repo.registrar(
            usuario_actual.id,
            usuario_actual.username,
            "ACTUALIZAR_PRODUCTO",
            f"Producto ID {prod_id} ({codigo} - {nombre}) actualizado."
        )
        return res

    def cambiar_estado(self, prod_id: int, activo: bool, usuario_actual: Usuario) -> bool:
        res = self.repo.cambiar_estado(prod_id, activo)
        estado_str = "activado" if activo else "desactivado"
        self.bitacora_repo.registrar(
            usuario_actual.id,
            usuario_actual.username,
            "CAMBIAR_ESTADO_PRODUCTO",
            f"El producto ID {prod_id} fue {estado_str}."
        )
        return res

    def eliminar_o_desactivar(self, prod_id: int, usuario_actual: Usuario) -> bool:
        """
        Regla de integridad (RF-10, Opción 2):
        'No eliminar un producto con ventas; desactivar.'
        """
        ventas_asoc = self.repo.contar_ventas_asociadas(prod_id)
        if ventas_asoc > 0:
            raise ValueError(
                f"No es posible eliminar físicamente el producto porque tiene {ventas_asoc} registro(s) de venta asociados.\n"
                "Para mantener la trazabilidad contable e integridad referencial, el sistema lo desactivará."
            )

        res = self.repo.eliminar(prod_id)
        self.bitacora_repo.registrar(
            usuario_actual.id,
            usuario_actual.username,
            "ELIMINAR_PRODUCTO",
            f"Producto ID {prod_id} eliminado de forma permanente."
        )
        return res

    def obtener_stock_bajo(self, umbral: int = 5) -> List[Producto]:
        """Reporte del caso problemático: Artículos con inventario en riesgo (RF-8)."""
        return self.repo.obtener_stock_bajo(umbral=umbral)
