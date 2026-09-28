"""
Script de pruebas automatizadas para verificar integridad de modelos, repositorios,
servicios y reglas de negocio del sistema sin abrir la interfaz gráfica.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from db.conexion import DatabaseConexion
from services.auth_service import AuthService
from services.categoria_service import CategoriaService
from services.producto_service import ProductoService
from services.venta_service import VentaService
from services.reporte_service import ReporteService


def ejecutar_pruebas():
    print("==================================================")
    print(" INICIANDO BATERÍA DE PRUEBAS DEL SISTEMA POS")
    print("==================================================")

    # 1. Inicializar BD
    print("\n[1/7] Probando inicialización de BD y tablas (RF-1)...")
    DatabaseConexion.inicializar_base_datos()
    print("  -> Base de datos y tablas inicializadas con éxito.")

    # 2. Probar autenticación
    print("\n[2/7] Probando servicio de autenticación y hash SHA-256 (RF-2, RF-3)...")
    auth_service = AuthService()

    # Login admin
    admin = auth_service.autenticar("admin", "admin123")
    assert admin.es_administrador, "El usuario admin debe tener rol de administrador."
    print(f"  -> Login exitoso: {admin.username} ({admin.rol})")

    # Login cajero
    cajero = auth_service.autenticar("cajero", "cajero123")
    assert not cajero.es_administrador, "El usuario cajero debe tener rol de operador."
    print(f"  -> Login exitoso: {cajero.username} ({cajero.rol})")

    # Clave incorrecta
    try:
        auth_service.autenticar("admin", "clave_falsa")
        assert False, "Debió rechazar clave incorrecta."
    except ValueError:
        print("  -> Rechazo de contraseña incorrecta: OK")

    # Usuario inactivo
    try:
        auth_service.autenticar("inactivo_demo", "demo123")
        assert False, "Debió rechazar usuario inactivo."
    except ValueError as e:
        print(f"  -> Rechazo de usuario inactivo: OK ({e})")

    # Restricción de operador sobre personal (RF-2)
    try:
        auth_service.listar_usuarios(cajero)
        assert False, "El operador no debe tener permiso de listar personal."
    except PermissionError:
        print("  -> Restricción de permisos para operador (RF-2): OK")

    # 3. Probar Categorías (Entidad B)
    print("\n[3/7] Probando CRUD de Categorías (Entidad B, RF-4)...")
    cat_service = CategoriaService()
    cats = cat_service.listar_todas()
    assert len(cats) >= 5, f"Deben existir al menos 5 categorías (A.5). Encontradas: {len(cats)}"
    print(f"  -> Categorías cargadas: {len(cats)}")

    # Crear categoría
    nueva_cat_id = cat_service.crear("Librería Especial", "Libros técnicos y guías", admin)
    assert nueva_cat_id > 0
    print(f"  -> Categoría creada con ID: {nueva_cat_id}")

    # Rechazar duplicado
    try:
        cat_service.crear("Librería Especial", "Intento duplicado", admin)
        assert False, "Debió rechazar nombre duplicado."
    except ValueError:
        print("  -> Prevención de duplicados en categorías: OK")

    # 4. Probar Productos (Entidad A)
    print("\n[4/7] Probando CRUD de Productos (Entidad A, RF-4)...")
    prod_service = ProductoService()
    prods = prod_service.listar_todos()
    assert len(prods) >= 8, f"Deben existir al menos 8 productos (A.5). Encontrados: {len(prods)}"
    print(f"  -> Productos cargados: {len(prods)}")

    # Crear producto
    nuevo_prod_id = prod_service.crear("TEST-999", "Libro de Algoritmos", nueva_cat_id, "450.00", "12", admin)
    assert nuevo_prod_id > 0
    print(f"  -> Producto creado con ID: {nuevo_prod_id}")

    # Rechazar precio negativo
    try:
        prod_service.crear("TEST-NEG", "Producto Malo", nueva_cat_id, "-10.00", "5", admin)
        assert False, "Debió rechazar precio negativo."
    except ValueError:
        print("  -> Rechazo de precio negativo: OK")

    # 5. Probar Movimiento de Ventas (RF-5)
    print("\n[5/7] Probando Proceso de Negocio / Venta Atómica con Descuento de Stock (RF-5)...")
    venta_service = VentaService()

    prod_antes = prod_service.obtener_por_id(nuevo_prod_id)
    stock_inicial = prod_antes.stock

    # Venta de 2 unidades
    carrito = [
        {"producto_id": nuevo_prod_id, "cantidad": 2, "precio_unitario": prod_antes.precio, "subtotal": prod_antes.precio * 2}
    ]
    venta_id, folio = venta_service.procesar_venta(cajero, carrito, notas="Venta de prueba en test")
    print(f"  -> Venta procesada exitosamente. Folio: {folio}, ID: {venta_id}")

    # Verificar descuento de stock
    prod_despues = prod_service.obtener_por_id(nuevo_prod_id)
    assert prod_despues.stock == stock_inicial - 2, f"El stock debió descontarse de {stock_inicial} a {stock_inicial - 2}."
    print(f"  -> Stock descontado correctamente: de {stock_inicial} a {prod_despues.stock} piezas.")

    # Probar rechazo de venta sin stock suficiente
    try:
        carrito_exceso = [
            {"producto_id": nuevo_prod_id, "cantidad": 9999, "precio_unitario": prod_antes.precio, "subtotal": 9999 * prod_antes.precio}
        ]
        venta_service.procesar_venta(cajero, carrito_exceso, notas="Intento de sobreventa")
        assert False, "Debió rechazar la venta por stock insuficiente."
    except ValueError as err_stock:
        print(f"  -> Validación de stock insuficiente: OK ({err_stock})")

    # Probar rechazo de producto inactivo
    # PROD-010 está inactivo según seed_data
    prod_inactivo = prod_service.obtener_por_codigo("PROD-010")
    if prod_inactivo:
        try:
            carrito_inactivo = [
                {"producto_id": prod_inactivo.id, "cantidad": 1, "precio_unitario": 10.0, "subtotal": 10.0}
            ]
            venta_service.procesar_venta(cajero, carrito_inactivo, notas="Vender inactivo")
            assert False, "Debió impedir vender producto inactivo."
        except ValueError as err_inac:
            print(f"  -> Rechazo de venta con producto inactivo (A.5): OK ({err_inac})")

    # 6. Probar Integridad Referencial (RF-10)
    print("\n[6/7] Probando Integridad Referencial (RF-10)...")
    # No eliminar producto con ventas
    try:
        prod_service.eliminar_o_desactivar(nuevo_prod_id, admin)
        assert False, "Debió impedir eliminar producto con historial de ventas."
    except ValueError as err_integ:
        print(f"  -> Protección de producto con ventas activas: OK ({err_integ})")

    # No eliminar categoría con productos
    try:
        cat_service.eliminar_o_desactivar(nueva_cat_id, admin)
        assert False, "Debió impedir eliminar categoría con productos asociados."
    except ValueError as err_cat:
        print(f"  -> Protección de categoría con productos asociados: OK ({err_cat})")

    # 7. Probar Reportes y Consultas con JOIN (RF-7, RF-8, A.6)
    print("\n[7/7] Probando Consultas JOIN y Reporte de Stock Bajo (RF-7, RF-8)...")
    reporte_service = ReporteService()

    # Consulta JOIN de movimientos
    movs_join = venta_service.listar_movimientos_con_join()
    assert len(movs_join) > 0, "La consulta JOIN debe retornar registros."
    print(f"  -> Consulta JOIN ejecutada con éxito. Filas retornadas: {len(movs_join)}")
    primer_join = movs_join[0]
    print(f"     Muestra JOIN: Folio: {primer_join['venta_folio']} | Producto: {primer_join['producto_nombre']} | Cajero: {primer_join['cajero_nombre']}")

    # Reporte de Stock Bajo (Caso Problemático RF-8)
    bajos = reporte_service.reporte_stock_bajo(umbral=5)
    assert len(bajos) > 0, "Debe existir al menos un producto con stock crítico (A.5)."
    print(f"  -> Reporte de Stock Bajo (RF-8): Encontrados {len(bajos)} artículo(s) con stock <= 5:")
    for b in bajos:
        print(f"     * {b['codigo']} - {b['nombre']}: Stock={b['stock']} ({b['alerta']})")

    # Exportación a CSV (Extra A.6)
    csv_path = os.path.join(BASE_DIR, "test_reporte_stock_bajo.csv")
    encabezados = ["Código", "Producto", "Categoría", "Precio", "Stock", "Alerta"]
    filas = [[b["codigo"], b["nombre"], b["categoria"], b["precio"], b["stock"], b["alerta"]] for b in bajos]
    reporte_service.exportar_a_csv(csv_path, encabezados, filas)
    assert os.path.exists(csv_path), "El archivo CSV debió crearse."
    print(f"  -> Exportación a CSV (Extra A.6): OK ({csv_path})")

    print("\n==================================================")
    print(" ¡TODAS LAS PRUEBAS (RF-1 a RF-10) PASARON CON ÉXITO! ")
    print("==================================================")


if __name__ == "__main__":
    ejecutar_pruebas()
