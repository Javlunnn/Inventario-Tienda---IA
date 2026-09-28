"""
Punto de Entrada Principal del Sistema de Inventario y Mini Punto de Venta.
Tópicos Avanzados de Programación - Unidad 1: Proyecto Final.
"""

import os
import sys

# Asegurar que el directorio raíz del proyecto esté en el sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from db.conexion import DatabaseConexion
from models.usuario import Usuario
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


class AplicacionPOS:
    """Controlador del ciclo de vida de la aplicación."""

    def __init__(self):
        # 1. RF-1: Crear base de datos y tablas en la primera ejecución
        DatabaseConexion.inicializar_base_datos()
        self.login_window = None
        self.main_window = None

    def iniciar(self):
        """Inicia el flujo con la ventana de inicio de sesión."""
        self._mostrar_login()

    def _mostrar_login(self):
        self.login_window = LoginWindow(on_login_success=self._on_login_exitoso)
        self.login_window.mainloop()

    def _on_login_exitoso(self, usuario: Usuario):
        """Callback al autenticar credenciales correctamente."""
        self.main_window = MainWindow(usuario_actual=usuario, on_logout=self._on_logout)
        self.main_window.mainloop()

    def _on_logout(self):
        """Callback al cerrar sesión desde la ventana principal."""
        self._mostrar_login()


def main():
    app = AplicacionPOS()
    app.iniciar()


if __name__ == "__main__":
    main()
