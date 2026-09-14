from abc import ABC, abstractmethod


class ErrorProveedorNoDisponible(Exception):
    """El proveedor no puede atender solicitudes (configuración o credenciales)."""


class ErrorTemporalProveedor(Exception):
    """Falla pasajera del proveedor; intentar más tarde podría funcionar."""


class ProveedorChat(ABC):
    """Contrato que nuestra aplicación espera de cualquier proveedor de respuestas.

    No depende de Discord ni de OpenAI: es la "forma" que definimos nosotros
    y a la que cada adaptador debe ajustarse.
    """

    @abstractmethod
    async def responder(self, mensaje: str) -> str:
        """Recibe una pregunta y regresa el texto de la respuesta."""
