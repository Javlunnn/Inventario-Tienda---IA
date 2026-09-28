import hashlib
import sqlite3
from datetime import datetime, timedelta


def hash_password(password: str) -> str:
    """Genera hash SHA-256 seguro para contraseñas (RF-3)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def cargar_datos_semilla(conn: sqlite3.Connection):
    """
    Inserta datos de prueba obligatorios según A.5 de la especificación:
    - Usuarios admin y operador (cajero)
    - 6 categorías (5 activas, 1 inactiva)
    - 10 productos (8 con stock normal, 1 con stock bajo crítico, 1 inactivo)
    - 3 movimientos de venta (vigente, con múltiples productos, y de prueba histórica)
    """
    cursor = conn.cursor()

    # 1. Usuarios del sistema (RF-2, RF-3, A.5)
    # admin / admin123  y  cajero / cajero123
    usuarios = [
        ("admin", hash_password("admin123"), "administrador", 1),
        ("cajero", hash_password("cajero123"), "operador", 1),
        ("inactivo_demo", hash_password("demo123"), "operador", 0),  # Usuario inactivo de prueba
    ]
    cursor.executemany(
        "INSERT INTO usuarios_sistema (username, password_hash, rol, activo) VALUES (?, ?, ?, ?)",
        usuarios
    )

    # 2. Categorías (Entidad B: al menos 5 registros + 1 inactiva)
    categorias = [
        ("Papelería y Escritura", "Cuadernos, bolígrafos, lápices y hojas", 1),
        ("Bebidas y Refrescos", "Aguas, jugos y gaseosas embotelladas", 1),
        ("Snacks y Botanas", "Galletas, frituras y confitería", 1),
        ("Electrónica y Oficina", "Cables, memorias USB y accesorios", 1),
        ("Servicios de Impresión", "Copias, engargolados y enmicados", 1),
        ("Temporada Pasada", "Categoría descontinuada o inactiva para pruebas de integridad", 0),
    ]
    cursor.executemany(
        "INSERT INTO categorias (nombre, descripcion, activo) VALUES (?, ?, ?)",
        categorias
    )

    # 3. Productos (Entidad A: al menos 8 registros + 1 con stock crítico <= 5 + 1 inactivo)
    productos = [
        ("PROD-001", "Cuaderno Profesional Raya 100h", 1, 35.50, 45, 1),
        ("PROD-002", "Bolígrafo Tinta Negra 0.7mm", 1, 8.00, 120, 1),
        ("PROD-003", "Refresco Cola 600ml", 2, 18.00, 30, 1),
        ("PROD-004", "Agua Natural Purificada 1L", 2, 12.50, 50, 1),
        ("PROD-005", "Papas Fritas Clásicas 45g", 3, 22.00, 25, 1),
        ("PROD-006", "Galletas con Chispas de Chocolate", 3, 16.50, 40, 1),
        ("PROD-007", "Memoria USB Kingston 32GB 3.0", 4, 145.00, 15, 1),
        ("PROD-008", "Paquete Hojas Blancas Carta 500h", 1, 110.00, 18, 1),
        # Caso problemático del dominio: Stock Bajo (umbral <= 5)
        ("PROD-009", "Calculadora Científica 240 Funciones", 4, 210.00, 3, 1),
        # Registro inactivo que no puede usarse en un nuevo movimiento
        ("PROD-010", "Pegamento Líquido Escolar Descontinuado", 1, 15.00, 10, 0),
    ]
    cursor.executemany(
        """INSERT INTO productos (codigo, nombre, categoria_id, precio, stock, activo)
           VALUES (?, ?, ?, ?, ?, ?)""",
        productos
    )

    # 4. Movimientos iniciales (Ventas con detalle: al menos 3 movimientos según A.5)
    # Fecha base hoy y ayer
    ahora = datetime.now()
    ayer = ahora - timedelta(days=1)
    antier = ahora - timedelta(days=2)

    # Venta 1: Venta normal realizada por cajero
    folio_1 = "VNT-20260901-0001"
    fecha_1 = antier.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO ventas (folio, fecha, usuario_id, total, notas) VALUES (?, ?, ?, ?, ?)",
        (folio_1, fecha_1, 2, 59.50, "Venta de mostrador en efectivo")
    )
    v1_id = cursor.lastrowid
    # Detalles Venta 1: 1 Cuaderno (35.50) + 3 Bolígrafos (8.00 c/u = 24.00) = 59.50
    cursor.execute(
        "INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (?, ?, ?, ?, ?)",
        (v1_id, 1, 1, 35.50, 35.50)
    )
    cursor.execute(
        "INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (?, ?, ?, ?, ?)",
        (v1_id, 2, 3, 8.00, 24.00)
    )

    # Venta 2: Venta de refrigerio/botanas por cajero
    folio_2 = "VNT-20260902-0002"
    fecha_2 = ayer.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO ventas (folio, fecha, usuario_id, total, notas) VALUES (?, ?, ?, ?, ?)",
        (folio_2, fecha_2, 2, 56.50, "Cobro con tarjeta")
    )
    v2_id = cursor.lastrowid
    # Detalles Venta 2: 1 Refresco (18.00) + 1 Papas (22.00) + 1 Galletas (16.50) = 56.50
    cursor.execute(
        "INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (?, ?, ?, ?, ?)",
        (v2_id, 3, 1, 18.00, 18.00)
    )
    cursor.execute(
        "INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (?, ?, ?, ?, ?)",
        (v2_id, 5, 1, 22.00, 22.00)
    )
    cursor.execute(
        "INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (?, ?, ?, ?, ?)",
        (v2_id, 6, 1, 16.50, 16.50)
    )

    # Venta 3: Venta de producto de tecnología por admin que redujo la calculadora a stock bajo
    folio_3 = "VNT-20260903-0003"
    fecha_3 = ahora.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO ventas (folio, fecha, usuario_id, total, notas) VALUES (?, ?, ?, ?, ?)",
        (folio_3, fecha_3, 1, 565.00, "Venta escolar mayorista")
    )
    v3_id = cursor.lastrowid
    # Detalles Venta 3: 2 Calculadoras (210.00 c/u = 420.00) + 1 USB (145.00) = 565.00
    cursor.execute(
        "INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (?, ?, ?, ?, ?)",
        (v3_id, 9, 2, 210.00, 420.00)
    )
    cursor.execute(
        "INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (?, ?, ?, ?, ?)",
        (v3_id, 7, 1, 145.00, 145.00)
    )

    # 5. Registro inicial en Bitácora
    cursor.execute(
        """INSERT INTO bitacora (fecha, usuario_id, usuario_nombre, accion, detalles)
           VALUES (?, ?, ?, ?, ?)""",
        (
            ahora.strftime("%Y-%m-%d %H:%M:%S"),
            1,
            "admin",
            "INICIALIZACION",
            "Inicialización de base de datos con catálogo base y configuración inicial."
        )
    )

    conn.commit()
