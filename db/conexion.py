import os
import sqlite3
import sys
from typing import Optional


def get_base_dir() -> str:
    """Retorna el directorio base del proyecto o ejecutable."""
    if getattr(sys, "frozen", False):
        # Ejecutándose como .exe de PyInstaller
        return os.path.dirname(sys.executable)
    # Ejecutándose en modo script
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class DatabaseConexion:
    """
    Administrador central de conexiones SQLite.
    Garantiza PRAGMA foreign_keys = ON y creación idempotente de tablas.
    """
    _db_path: Optional[str] = None

    @classmethod
    def get_db_path(cls) -> str:
        if cls._db_path is None:
            base_dir = get_base_dir()
            cls._db_path = os.path.join(base_dir, "inventario_pos.db")
        return cls._db_path

    @classmethod
    def set_custom_db_path(cls, path: str):
        """Permite asignar una ruta de base de datos específica (útil para tests)."""
        cls._db_path = path

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        """Retorna una nueva conexión con row_factory y claves foráneas habilitadas."""
        db_file = cls.get_db_path()
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        # REQUISITO OBLIGATORIO: Forzar integridad referencial
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @classmethod
    def inicializar_base_datos(cls):
        """Crea el archivo .db y las tablas la primera vez que se ejecuta (RF-1)."""
        db_file = cls.get_db_path()
        es_nueva = not os.path.exists(db_file) or os.path.getsize(db_file) == 0

        with cls.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Tabla de Usuarios del Sistema
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                rol TEXT NOT NULL CHECK(rol IN ('administrador', 'operador')),
                activo INTEGER NOT NULL DEFAULT 1
            );
            """)

            # 2. Entidad B: Categorías
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                descripcion TEXT DEFAULT '',
                activo INTEGER NOT NULL DEFAULT 1
            );
            """)

            # 3. Entidad A: Productos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                categoria_id INTEGER NOT NULL,
                precio REAL NOT NULL CHECK(precio > 0),
                stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                activo INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE RESTRICT
            );
            """)

            # 4. Movimiento: Ventas
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folio TEXT UNIQUE NOT NULL,
                fecha TEXT NOT NULL,
                usuario_id INTEGER NOT NULL,
                total REAL NOT NULL CHECK(total >= 0),
                notas TEXT DEFAULT '',
                FOREIGN KEY (usuario_id) REFERENCES usuarios_sistema(id) ON DELETE RESTRICT
            );
            """)

            # 5. Detalle de Venta
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_venta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL CHECK(cantidad > 0),
                precio_unitario REAL NOT NULL CHECK(precio_unitario > 0),
                subtotal REAL NOT NULL CHECK(subtotal >= 0),
                FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
                FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT
            );
            """)

            # 6. Extra: Bitácora de Auditoría
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bitacora (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                usuario_id INTEGER,
                usuario_nombre TEXT NOT NULL,
                accion TEXT NOT NULL,
                detalles TEXT DEFAULT '',
                FOREIGN KEY (usuario_id) REFERENCES usuarios_sistema(id) ON DELETE SET NULL
            );
            """)

            conn.commit()

        # Si no había usuarios, insertar semillas de prueba (RF-1, A.5)
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM usuarios_sistema")
            row = cursor.fetchone()
            if row and row["total"] == 0:
                from .seed_data import cargar_datos_semilla
                cargar_datos_semilla(conn)
