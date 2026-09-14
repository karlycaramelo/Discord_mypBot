from dominio import ProveedorChat


class ProveedorFicticio(ProveedorChat):
    """Proveedor de prueba: permite ejecutar el bot sin consumir ninguna API."""

    async def responder(self, mensaje: str) -> str:
        return f"Respuesta simulada para: {mensaje}"
