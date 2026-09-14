from adaptadores import AdaptadorOpenAI, ProveedorFicticio
from configuracion import Configuracion, ErrorConfiguracion
from dominio import ProveedorChat


def crear_proveedor(configuracion: Configuracion) -> ProveedorChat:
    """Único lugar que decide qué proveedor concreto se usa.

    Quien la llama solo recibe un ProveedorChat y no necesita saber cuál es.
    """
    if configuracion.proveedor_chat == "ficticio":
        return ProveedorFicticio()

    if configuracion.proveedor_chat == "openai":
        return crear_adaptador_openai(configuracion)

    raise ErrorConfiguracion(f"Proveedor desconocido: {configuracion.proveedor_chat}.")


def crear_adaptador_openai(configuracion: Configuracion) -> AdaptadorOpenAI:
    # Se valida aquí y no en Configuracion porque estas variables
    # solo son obligatorias cuando se elige OpenAI.
    if configuracion.clave_openai is None:
        raise ErrorConfiguracion("Falta OPENAI_API_KEY para usar PROVEEDOR_CHAT=openai.")
    if configuracion.modelo_openai is None:
        raise ErrorConfiguracion("Falta OPENAI_MODEL para usar PROVEEDOR_CHAT=openai.")

    return AdaptadorOpenAI(
        clave_api=configuracion.clave_openai,
        modelo=configuracion.modelo_openai,
    )
